import logging
import starlink_grpc

log = logging.getLogger(__name__)


class Starlink:
    def __init__(self, ip_address: str):
        self.ip_address = ip_address
        self._status = None
        self._context = starlink_grpc.ChannelContext(self.uri)

    @property
    def uri(self):
        return f"{self.ip_address}:9000"

    def update(self):
        log.debug(f"Updating starlink status from {self.uri}")
        try:
            self._status, grpc_status, alerts = starlink_grpc.status_data(self._context)
        except Exception as e:
            logging.error(f"Error updating starlink status: {e}")
            self._status = None

    def __getattr__(self, name: str):
        if name in self._status:
            return self._status[name]
        else:
            raise AttributeError(f"Attribute {name} not found")

    def is_connected(self) -> bool:
        return not self._status is None

    def has_internet(self) -> bool:
        if not self.is_connected():
            return False
        return self._status["state"] == "CONNECTED"
