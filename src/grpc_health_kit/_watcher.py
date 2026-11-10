from threading import Condition
from typing import TYPE_CHECKING

from ._serving_status import ServingStatus

if TYPE_CHECKING:
    from ._registry import HealthRegistry


class Watcher:
    """Watch a service and receive status updates (coalesced)."""

    def __init__(
        self,
        service: str,
        initial_status: ServingStatus,
        registry: "HealthRegistry",
    ):
        self._service = service
        self._registry = registry
        self._cond = Condition()
        self._pending: ServingStatus | None = initial_status
        self._has_pending = True
        self._closed = False

    def poll(self) -> ServingStatus | None:
        """Return the latest pending status, or None if none."""
        with self._cond:
            if self._has_pending:
                status = self._pending
                self._pending = None
                self._has_pending = False
                return status
            return None

    def wait(self, timeout: float) -> ServingStatus | None:
        """Wait up to timeout seconds for a status; returns None on timeout or close."""
        with self._cond:
            if self._closed:
                return None
            if not self._has_pending:
                self._cond.wait(timeout)
            if self._closed:
                return None
            if self._has_pending:
                return self.poll()
            return None

    def close(self) -> None:
        """Close the watcher and unregister from the registry."""
        with self._cond:
            if self._closed:
                return
            self._closed = True
            self._cond.notify_all()
        self._registry._remove_watcher(self)

    def _notify(self, status: ServingStatus) -> None:
        """Called by registry when status changes."""
        with self._cond:
            if self._closed:
                return
            self._pending = status
            self._has_pending = True
            self._cond.notify_all()
