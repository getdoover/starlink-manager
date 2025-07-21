from pathlib import Path

from pydoover import config


class StarlinkManagerConfig(config.Schema):
    def __init__(self):
        self.starlink_ip_address = config.String("Starlink IP Address", description="The IP address of the starlink dish", default="192.168.1.1")
        self.power_pin = config.Integer("Power Pin", description="The digital output pin that controls the power to the Starlink", default=None)

        # self.sim_app_key = config.Application("Simulator App Key", description="The app key for the simulator")


def export():
    StarlinkManagerConfig().export(Path(__file__).parents[2] / "doover_config.json", "starlink_manager")
