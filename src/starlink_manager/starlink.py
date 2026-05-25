import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import grpc
import starlink_grpc

log = logging.getLogger(__name__)


@dataclass
class StarlinkSnapshot:
    """Most-recent values pulled from the dish.

    Status + obstruction + alerts come from one gRPC call per loop;
    location comes from a separate call on a much slower cadence. Any
    field is ``None`` until its first successful fetch.
    """

    status: dict[str, Any] | None = None
    obstruction: dict[str, Any] | None = None
    alerts: dict[str, Any] | None = None
    location: dict[str, Any] | None = None

    last_status_at: float = 0.0
    last_location_at: float = 0.0

    consecutive_status_failures: int = field(default=0)


class Starlink:
    """Async wrapper around the (sync) starlink_grpc client.

    The library is blocking; we run each call in the default thread pool
    so a slow dish (or one whose TCP connection just dropped) doesn't
    stall the application's main loop.
    """

    def __init__(self, ip_address: str, location_period_s: float = 300.0):
        self.ip_address = ip_address
        self.location_period_s = location_period_s
        self._context = starlink_grpc.ChannelContext(self.uri)
        self.snapshot = StarlinkSnapshot()

    @property
    def uri(self) -> str:
        return f"{self.ip_address}:9200"

    async def close(self) -> None:
        await asyncio.to_thread(self._context.close)

    # ---- fetches ----------------------------------------------------

    async def fetch_status(self) -> bool:
        """Pull status + obstruction + alert dicts. Cheap; call every loop."""
        try:
            status, obstruction, alerts = await asyncio.to_thread(
                starlink_grpc.status_data, self._context
            )
        except (grpc.RpcError, starlink_grpc.GrpcError) as e:
            self.snapshot.consecutive_status_failures += 1
            log.warning(
                "Starlink status fetch failed (streak=%d, target=%s): %s",
                self.snapshot.consecutive_status_failures, self.uri, e,
            )
            self.snapshot.status = None
            self.snapshot.obstruction = None
            self.snapshot.alerts = None
            return False

        self.snapshot.consecutive_status_failures = 0
        self.snapshot.status = status
        self.snapshot.obstruction = obstruction
        self.snapshot.alerts = alerts
        self.snapshot.last_status_at = time.time()
        return True

    async def fetch_location(self) -> bool:
        try:
            location = await asyncio.to_thread(
                starlink_grpc.location_data, self._context
            )
        except (grpc.RpcError, starlink_grpc.GrpcError) as e:
            log.debug("Starlink location fetch failed: %s", e)
            self.snapshot.location = None
            return False
        self.snapshot.location = location
        self.snapshot.last_location_at = time.time()
        return True

    # ---- convenience accessors --------------------------------------

    @property
    def is_responding(self) -> bool:
        return self.snapshot.status is not None

    @property
    def has_internet(self) -> bool:
        return self.is_responding and self.snapshot.status.get("state") == "CONNECTED"

    @property
    def location_due(self) -> bool:
        return (time.time() - self.snapshot.last_location_at) >= self.location_period_s
