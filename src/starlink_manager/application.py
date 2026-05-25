import asyncio
import logging
import time
from datetime import datetime, timedelta

from pydoover.docker import Application

from .app_config import StarlinkManagerConfig
from .app_state import StarlinkManagerState
from .app_tags import StarlinkManagerTags
from .app_ui import StarlinkManagerUI
from .starlink import Starlink

log = logging.getLogger()


def _mbps(bps):
    return None if bps is None else round(bps / 1_000_000, 2)


def _pct(fraction):
    return None if fraction is None else round(fraction * 100, 2)


class StarlinkManagerApplication(Application):
    config: StarlinkManagerConfig
    tags: StarlinkManagerTags

    config_cls = StarlinkManagerConfig
    tags_cls = StarlinkManagerTags
    ui_cls = StarlinkManagerUI

    async def setup(self):
        self.starlink = Starlink(self.config.starlink_ip_address.value or "192.168.100.1")
        self.state = StarlinkManagerState(self)

        self.loop_target_period = 2  # seconds

        self._shutdown_at: datetime | None = None
        self._shutdown_task: asyncio.Task | None = None

        self._last_published_location: dict | None = None

    async def main_loop(self):
        log.info("Starlink State : %s", self.state.state)

        await self.starlink.fetch_status()
        await self._publish_status()

        # Location rarely changes on a fixed install; throttle to
        # Starlink.location_period_s (5 min by default).
        if self.starlink.is_responding and self.starlink.location_due:
            await self.starlink.fetch_location()
            await self._publish_location_channel()

        await self.state.spin_state()

        if self.state.state == "off":
            await self.set_power_off()
        else:
            await self.set_power_on()

    # -----------------------------------------------------------------
    # Tag publishing
    # -----------------------------------------------------------------

    async def _publish_status(self) -> None:
        snap = self.starlink.snapshot
        await self.tags.is_responding.set(self.starlink.is_responding)
        await self.tags.has_internet.set(self.starlink.has_internet)

        if snap.status is None:
            # Dish unreachable — leave the rest of the tags at their
            # last value rather than zeroing them, so the UI shows
            # "stale" readings instead of misleading clean ones.
            return

        s = snap.status
        await self.tags.state.set(s.get("state"))
        await self.tags.device_id.set(s.get("id"))
        await self.tags.hardware_version.set(s.get("hardware_version"))
        await self.tags.software_version.set(s.get("software_version"))
        uptime = s.get("uptime")
        if uptime is not None:
            # Convert "seconds since boot" into ms-since-epoch so the UI
            # can render it as a wall-clock timestamp.
            await self.tags.started_at_ms.set(int((time.time() - uptime) * 1000))
        await self.tags.seconds_to_first_nonempty_slot.set(
            s.get("seconds_to_first_nonempty_slot")
        )

        await self.tags.downlink_mbps.set(_mbps(s.get("downlink_throughput_bps")))
        await self.tags.uplink_mbps.set(_mbps(s.get("uplink_throughput_bps")))
        await self.tags.latency_ms.set(s.get("pop_ping_latency_ms"))
        await self.tags.ping_drop_rate.set(_pct(s.get("pop_ping_drop_rate")))
        await self.tags.snr_above_noise_floor.set(
            bool(s.get("is_snr_above_noise_floor"))
        )

        await self.tags.gps_enabled.set(bool(s.get("gps_enabled")))
        await self.tags.gps_ready.set(bool(s.get("gps_ready")))
        sats = s.get("gps_sats")
        await self.tags.gps_sats.set(int(sats) if sats is not None else 0)

        # All obstruction & direction values live in the StatusDict, not
        # the ObstructionDict (which only carries the now-obsolete
        # per-wedge arrays).
        currently_obstructed = bool(s.get("currently_obstructed"))
        await self.tags.fraction_obstructed.set(_pct(s.get("fraction_obstructed")))
        await self.tags.currently_obstructed.set(currently_obstructed)
        await self.tags.obstruction_ok.set(not currently_obstructed)
        await self.tags.obstruction_duration_s.set(s.get("obstruction_duration"))
        await self.tags.obstruction_interval_s.set(s.get("obstruction_interval"))
        await self.tags.direction_azimuth_deg.set(s.get("direction_azimuth"))
        await self.tags.direction_elevation_deg.set(s.get("direction_elevation"))

        await self._publish_alerts(snap.alerts or {})

    async def _publish_alerts(self, alerts: dict) -> None:
        # Per-condition booleans. Read with .get(default=False) so a
        # firmware that drops an alert key doesn't flap our tag.
        def a(key: str) -> bool:
            return bool(alerts.get(key, False))

        thermal = a("thermal_throttle") or a("thermal_shutdown") or a(
            "power_supply_thermal_throttle"
        )
        water = a("dish_water_detected") or a("router_water_detected")
        hardware = a("motors_stuck") or a("mast_not_near_vertical")

        await self.tags.thermal_ok.set(not thermal)
        await self.tags.water_ok.set(not water)
        await self.tags.hardware_ok.set(not hardware)

        await self.tags.alert_thermal_throttle.set(a("thermal_throttle"))
        await self.tags.alert_thermal_shutdown.set(a("thermal_shutdown"))
        await self.tags.alert_power_supply_thermal_throttle.set(
            a("power_supply_thermal_throttle")
        )
        await self.tags.alert_dish_water_detected.set(a("dish_water_detected"))
        await self.tags.alert_router_water_detected.set(a("router_water_detected"))
        await self.tags.alert_motors_stuck.set(a("motors_stuck"))
        await self.tags.alert_mast_not_near_vertical.set(a("mast_not_near_vertical"))
        await self.tags.alert_unexpected_location.set(a("unexpected_location"))
        await self.tags.alert_install_pending.set(a("install_pending"))
        await self.tags.alert_roaming.set(a("roaming"))
        await self.tags.alert_is_heating.set(a("is_heating"))
        await self.tags.alert_slow_ethernet_speeds.set(a("slow_ethernet_speeds"))
        await self.tags.alert_lower_signal_than_predicted.set(
            a("lower_signal_than_predicted")
        )

    async def _publish_location_channel(self) -> None:
        """Push GPS fix to the shared ``location`` channel.

        Format mirrors what ``location-manager`` publishes so downstream
        consumers (maps, geofence apps) treat both sources identically.
        We dedup on lat/long to avoid spamming the channel from a
        stationary install.
        """
        loc = self.starlink.snapshot.location or {}
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if lat is None or lon is None:
            return

        # Omit ``accuracy`` rather than send None — location-manager's
        # publish path compares it against a numeric threshold, which
        # would raise on None. Its read path tolerates absence.
        payload = {
            "lat": lat,
            "long": lon,
            "alt": loc.get("altitude"),
        }
        if self._last_published_location == payload:
            return

        try:
            await self.publish_to_channel("location", payload)
        except Exception:
            log.exception("Failed to publish location to channel")
            return
        self._last_published_location = payload

    async def on_shutdown_at(self, shutdown_at: datetime):
        if self._shutdown_task is not None:
            self._shutdown_task.cancel()
        self._shutdown_at = shutdown_at
        self._shutdown_task = asyncio.create_task(self.shutdown_task())

    async def shutdown_task(self):
        tolerance = 10  # trigger shutdown when within 10s of the target
        while datetime.now() < self._shutdown_at - timedelta(seconds=tolerance):
            await asyncio.sleep(1)
        await self.state.trigger_shutdown()

    def is_connected(self):
        return self.starlink.is_responding

    def has_internet(self):
        return self.starlink.has_internet

    async def set_power_off(self):
        if self.config.power_pin.value is not None:
            await self.platform_iface.set_do(self.config.power_pin.value, 0)

    async def set_power_on(self):
        if self.config.power_pin.value is not None:
            await self.platform_iface.set_do(self.config.power_pin.value, 1)
