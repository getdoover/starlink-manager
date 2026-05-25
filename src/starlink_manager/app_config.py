from pathlib import Path

from pydoover import config


class StarlinkManagerConfig(config.Schema):
    starlink_ip_address = config.String(
        "Starlink IP Address",
        description="The IP address of the starlink dish",
        default="192.168.1.1",
    )
    power_pin = config.Integer(
        "Power Pin",
        description="The digital output pin that controls the power to the Starlink",
        default=None,
    )


def export():
    StarlinkManagerConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "starlink_manager"
    )
