import logging
import starlink_grpc

logging.basicConfig(level=logging.INFO)

class Starlink:

    def __init__(self, ip_address: str):
        self.ip_address = ip_address
        self._status = None
        self._context = starlink_grpc.ChannelContext(self.uri)

    @property
    def uri(self):
        return f"{self.ip_address}:9000"

    def update(self):
        logging.debug(f"Updating starlink status from {self.uri}")
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
    

def main():
    starlink = Starlink("192.168.1.1")
    starlink.update()
    print(starlink._status)
    print(f"Connected: {starlink.is_connected()}")
    print(f"Has internet: {starlink.has_internet()}")
    if starlink.is_connected():
        print(f"Software version: {starlink.software_version}")

if __name__ == "__main__":
    main()