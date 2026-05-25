from pathlib import Path

from pydoover import config
from pydoover.config import ApplicationPosition


class StarlinkManagerConfig(config.Schema):
    starlink_ip_address = config.String(
        "Starlink IP Address",
        description="The IP address of the Starlink dish's gRPC API (default 192.168.100.1).",
        default="192.168.100.1",
    )
    power_pin = config.Integer(
        "Power Pin",
        description="The digital output pin that controls the power to the Starlink",
        default=None,
    )
    position = ApplicationPosition(default=110)  # low but not as low as power management


def export():
    StarlinkManagerConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "starlink_manager"
    )
