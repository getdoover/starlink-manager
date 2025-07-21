import logging
import asyncio
import time
from datetime import datetime, timedelta

from pydoover.docker import Application
from pydoover import ui

from .app_config import StarlinkManagerConfig
from .app_ui import StarlinkManagerUI
from .app_state import StarlinkManagerState

from .starlink import Starlink

log = logging.getLogger()

class StarlinkManagerApplication(Application):
    config: StarlinkManagerConfig  # not necessary, but helps your IDE provide autocomplete!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.loop_target_period = 2 ## seconds

        self.started: float = time.time()
        # self.ui: StarlinkManagerUI = None
        self.state: StarlinkManagerState = None

        self._shutdown_at: datetime = None
        self._shutdown_task: asyncio.Task = None

    async def setup(self):
        self.starlink = Starlink("192.168.1.1")
        self.state = StarlinkManagerState(self)

        # self.ui = StarlinkManagerUI()
        # self.ui_manager.add_children(*self.ui.fetch())

    async def main_loop(self):
        log.info(f"Starlink State : {self.state.state}")
        self.starlink.update()
        await self.state.spin_state()
        
        if self.state.state == "off":
            await self.set_power_off()
        else:
            await self.set_power_on()

    async def on_shutdown_at(self, shutdown_at: datetime):
        if self._shutdown_task is not None:
            self._shutdown_task.cancel()
        self._shutdown_at = shutdown_at
        self._shutdown_task = asyncio.create_task(self.shutdown_task())

    async def shutdown_task(self):
        tolerance = 10 ## Trigger shutdown if we're within 10 seconds of the shutdown time
        while datetime.now() < self._shutdown_at - timedelta(seconds=tolerance):
            await asyncio.sleep(1)
        await self.state.trigger_shutdown()

    def is_connected(self):
        return self.starlink.is_connected()

    def has_internet(self):
        return self.starlink.has_internet()

    async def set_power_off(self):
        if self.config.power_pin.value is not None:
            await self.platform_iface.set_do_async(self.config.power_pin.value, 0)

    async def set_power_on(self):
        if self.config.power_pin.value is not None:
            await self.platform_iface.set_do_as(self.config.power_pin.value, 1)