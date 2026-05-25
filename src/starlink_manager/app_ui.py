from pathlib import Path

from pydoover import ui

from .app_tags import StarlinkManagerTags as T


class StarlinkManagerUI(ui.UI):
    # ---- at-a-glance, always visible -------------------------------
    has_internet = ui.BooleanVariable(
        "Internet",
        value=T.has_internet,
        position=1,
    )
    state = ui.TextVariable(
        "Dish State",
        value=T.state,
        position=2,
    )
    downlink = ui.NumericVariable(
        "Download",
        value=T.downlink_mbps,
        units="Mbps",
        precision=1,
        form=ui.Widget.radial,
        ranges=[
            ui.Range("Slow", 0, 25, ui.Colour.yellow),
            ui.Range("OK", 25, 100, ui.Colour.blue),
            ui.Range("Fast", 100, 500, ui.Colour.green),
        ],
        position=3,
    )
    uplink = ui.NumericVariable(
        "Upload",
        value=T.uplink_mbps,
        units="Mbps",
        precision=1,
        position=4,
    )
    latency = ui.NumericVariable(
        "Latency",
        value=T.latency_ms,
        units="ms",
        precision=0,
        ranges=[
            ui.Range("Good", 0, 60, ui.Colour.green),
            ui.Range("High", 60, 150, ui.Colour.yellow),
            ui.Range("Bad", 150, 1000, ui.Colour.red),
        ],
        position=5,
    )
    ping_drop = ui.NumericVariable(
        "Packet Loss",
        value=T.ping_drop_rate,
        units="%",
        precision=1,
        position=6,
    )

    # ---- warnings — bind to *positive* state tag, hide when ok ----
    obstructed_warning = ui.WarningIndicator(
        "Dish Obstructed",
        hidden=T.obstruction_ok,
        position=20,
    )
    thermal_warning = ui.WarningIndicator(
        "Thermal Throttling",
        hidden=T.thermal_ok,
        position=21,
    )
    water_warning = ui.WarningIndicator(
        "Water Detected",
        hidden=T.water_ok,
        position=22,
    )
    hardware_warning = ui.WarningIndicator(
        "Hardware Fault",
        hidden=T.hardware_ok,
        position=23,
    )

    # ---- collapsible detail sections --------------------------------
    obstruction = ui.Submodule(
        "Obstruction",
        children=[
            ui.NumericVariable(
                "Obstructed Fraction",
                value=T.fraction_obstructed,
                units="%",
                precision=2,
            ),
            ui.BooleanVariable(
                "Currently Obstructed",
                value=T.currently_obstructed,
            ),
            ui.NumericVariable(
                "Mean Obstruction Duration",
                value=T.obstruction_duration_s,
                units="s",
                precision=1,
            ),
            ui.NumericVariable(
                "Mean Obstruction Interval",
                value=T.obstruction_interval_s,
                units="s",
                precision=0,
            ),
            ui.NumericVariable(
                "Azimuth",
                value=T.direction_azimuth_deg,
                units="deg",
                precision=1,
            ),
            ui.NumericVariable(
                "Elevation",
                value=T.direction_elevation_deg,
                units="deg",
                precision=1,
            ),
        ],
        is_collapsed=True,
        position=40,
    )

    device = ui.Submodule(
        "Device",
        children=[
            ui.TextVariable("Serial", value=T.device_id),
            ui.TextVariable("Hardware", value=T.hardware_version),
            ui.TextVariable("Software", value=T.software_version),
            ui.Timestamp("Started", value=T.started_at_ms),
            ui.BooleanVariable("SNR Above Noise Floor", value=T.snr_above_noise_floor),
        ],
        is_collapsed=True,
        position=42,
    )

    # ---- history chart ---------------------------------------------
    history = ui.Multiplot(
        "Throughput & Latency",
        name="history",
        series=[
            ui.Series(
                "Download",
                value=T.downlink_mbps,
                units="Mbps",
                colour=ui.Colour.blue,
                active=True,
            ),
            ui.Series(
                "Upload",
                value=T.uplink_mbps,
                units="Mbps",
                colour=ui.Colour.green,
                active=True,
            ),
            ui.Series(
                "Latency",
                value=T.latency_ms,
                units="ms",
                colour=ui.Colour.yellow,
                shared_axis=False,
                active=True,
            ),
        ],
        position=50,
    )


def export():
    StarlinkManagerUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "starlink_manager"
    )
