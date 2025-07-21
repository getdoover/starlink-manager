import logging

from pydoover.state import StateMachine

log = logging.getLogger(__name__)

class StarlinkManagerState:
    state: str

    states = [
        {"name": "off", "timeout": 120, "on_timeout": "turn_on"}, ## For the moment, only allowed to stay off for a short period
        {"name": "initialising", "timeout": 120, "on_timeout": "no_connection"},
        {"name": "not_connected", "timeout": 120, "on_timeout": "power_off"}, ## If not connected after a while, power off, which will start a loop of powering on/off till it works
        {"name": "offline"},
        {"name": "online"},
    ]

    transitions = [
        {"trigger": "turn_on", "source": "off", "dest": "initialising"},
        {"trigger": "set_connected", "source": "initialising", "dest": "offline"},
        {"trigger": "disconnected", "source": ["offline", "online", "initialising"], "dest": "not_connected"},
        {"trigger": "set_online", "source": "offline", "dest": "online"},
        {"trigger": "set_offline", "source": "online", "dest": "offline"},
        {"trigger": "power_off", "source": "*", "dest": "off"},
    ]

    def __init__(self, app):
        self.app = app
        self.state_machine = StateMachine(
            states=self.states,
            transitions=self.transitions,
            model=self,
            initial="initialising",
            queued=True,
        )

    async def spin_state(self):
        last_state = None
        ## keep spinning until state has stabilised
        count = 0
        while last_state != self.state:
            count += 1
            if count > 15:
                break
            last_state = self.state
            await self.evaluate_state()
            # log.info(f"State : {self.state}")

    async def evaluate_state(self):
        if self.state == "off":
            pass ## Do nothing

        elif self.state in ["initialising", "not_connected"]:
            if self.app.is_connected():
                await self.set_connected()

        elif self.state == "offline":
            if self.app.has_internet():
                await self.set_online()

        elif self.state == "online":
            if not self.app.has_internet():
                await self.set_offline()

    async def trigger_shutdown(self):
        if self.state != "off":
            await self.power_off()