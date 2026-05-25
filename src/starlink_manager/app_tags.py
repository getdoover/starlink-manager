from pydoover.tags import AnyChange, Delta, Tag, Tags


class StarlinkManagerTags(Tags):
    # ---- top-level state -------------------------------------------
    is_responding = Tag("boolean", default=False, live=True)
    has_internet = Tag("boolean", default=False, live=True)
    state = Tag("string", default=None, log_on=AnyChange())

    # ---- device identity (rarely changes; AnyChange catches firmware
    # updates and hardware swaps) -----------------------------------
    device_id = Tag("string", default=None, log_on=AnyChange())
    hardware_version = Tag("string", default=None, log_on=AnyChange())
    software_version = Tag("string", default=None, log_on=AnyChange())
    # ms-since-epoch of the dish's last boot — derived in the app from
    # ``status.uptime``. Delta=2s tolerates measurement jitter while
    # still logging a row when the dish actually reboots (uptime
    # resets, so started_at jumps by however long the dish was down).
    started_at_ms = Tag("integer", default=None, log_on=Delta(amount=2000))
    seconds_to_first_nonempty_slot = Tag("number", default=None)

    # ---- live link quality -----------------------------------------
    downlink_mbps = Tag("number", default=None, live=True)
    uplink_mbps = Tag("number", default=None, live=True)
    latency_ms = Tag("number", default=None, live=True)
    ping_drop_rate = Tag("number", default=None, live=True, log_on=Delta(amount=1.0))
    snr_above_noise_floor = Tag("boolean", default=False)

    # ---- obstruction -----------------------------------------------
    fraction_obstructed = Tag("number", default=None, log_on=Delta(amount=0.5))
    currently_obstructed = Tag("boolean", default=False)
    # Positive-logic mirror for WarningIndicator(hidden=...) — see prosense.
    obstruction_ok = Tag("boolean", default=True)
    obstruction_duration_s = Tag("number", default=None)
    obstruction_interval_s = Tag("number", default=None)
    direction_azimuth_deg = Tag("number", default=None, log_on=Delta(amount=1.0))
    direction_elevation_deg = Tag("number", default=None, log_on=Delta(amount=1.0))

    # ---- GPS status (lat/long/alt are published to the `location`
    # channel, not surfaced as tags) ---------------------------------
    gps_enabled = Tag("boolean", default=False)
    gps_ready = Tag("boolean", default=False)
    gps_sats = Tag("integer", default=0)

    # ---- alerts (boolean per condition; the few that drive a
    # WarningIndicator have a paired *_ok positive-logic tag) -------
    thermal_ok = Tag("boolean", default=True)
    alert_thermal_throttle = Tag("boolean", default=False)
    alert_thermal_shutdown = Tag("boolean", default=False)
    alert_power_supply_thermal_throttle = Tag("boolean", default=False)

    water_ok = Tag("boolean", default=True)
    alert_dish_water_detected = Tag("boolean", default=False)
    alert_router_water_detected = Tag("boolean", default=False)

    hardware_ok = Tag("boolean", default=True)
    alert_motors_stuck = Tag("boolean", default=False)
    alert_mast_not_near_vertical = Tag("boolean", default=False)

    alert_unexpected_location = Tag("boolean", default=False)
    alert_install_pending = Tag("boolean", default=False)
    alert_roaming = Tag("boolean", default=False)
    alert_is_heating = Tag("boolean", default=False)
    alert_slow_ethernet_speeds = Tag("boolean", default=False)
    alert_lower_signal_than_predicted = Tag("boolean", default=False)
