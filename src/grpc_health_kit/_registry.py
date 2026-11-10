import threading
from collections.abc import Callable

from ._errors import HealthError
from ._serving_status import ServingStatus
from ._watcher import Watcher


class HealthRegistry:
    """Thread-safe registry of service health statuses."""

    def __init__(
        self,
        *,
        max_services: int = 1000,
        max_watchers: int = 1000,
        on_event: Callable[[dict[str, object]], None] | None = None,
    ):
        self._lock = threading.RLock()
        self._services: dict[str, ServingStatus] = {"": ServingStatus.SERVING}
        self._after_shutdown = False
        self._max_services = max_services
        self._max_watchers = max_watchers
        self._on_event = on_event
        self._watchers: dict[str, set[Watcher]] = {}
        self._total_watchers = 0

    def set(self, service: str, status: ServingStatus) -> None:
        """Set the status for a service. Raises on invalid status or if limits exceeded."""
        if not isinstance(status, ServingStatus) or status == ServingStatus.SERVICE_UNKNOWN:
            raise HealthError("invalid_status")
        with self._lock:
            if self._after_shutdown:
                if self._on_event:
                    self._on_event({"event": "ignored_after_shutdown", "service": service})
                return
            current = self._services.get(service)
            if status == current:
                return
            if service not in self._services and len(self._services) >= self._max_services:
                raise HealthError("too_many_services")
            self._services[service] = status
            if self._on_event:
                self._on_event(
                    {"event": "status_changed", "service": service, "status": status.name}
                )
            watchers = self._watchers.get(service)
            if watchers:
                for w in list(watchers):
                    w._notify(status)

    def check(self, service: str) -> ServingStatus:
        """Return the current status for a service. Raises not_found if absent."""
        with self._lock:
            status = self._services.get(service)
            if status is None:
                raise HealthError("not_found")
            return status

    def watch(self, service: str) -> Watcher:
        """Create a watcher for a service. Initial status is current or SERVICE_UNKNOWN."""
        with self._lock:
            if self._total_watchers >= self._max_watchers:
                raise HealthError("too_many_watchers")
            status = self._services.get(service, ServingStatus.SERVICE_UNKNOWN)
            watcher = Watcher(service, status, self)
            self._watchers.setdefault(service, set()).add(watcher)
            self._total_watchers += 1
            return watcher

    def services(self) -> list[str]:
        """Return sorted list of registered services (including empty)."""
        with self._lock:
            return sorted(self._services.keys())

    def enter_graceful_shutdown(self) -> None:
        """Set all services to NOT_SERVING and ignore further sets."""
        with self._lock:
            if self._after_shutdown:
                return
            self._after_shutdown = True
            for service in list(self._services.keys()):
                self._set_unlocked(service, ServingStatus.NOT_SERVING)
            if self._on_event:
                self._on_event({"event": "graceful_shutdown"})

    def _set_unlocked(self, service: str, status: ServingStatus) -> None:
        """Internal set assuming lock is held. Notifies watchers."""
        current = self._services.get(service)
        if status == current:
            return
        self._services[service] = status
        watchers = self._watchers.get(service)
        if watchers:
            for w in list(watchers):
                w._notify(status)
        if self._on_event:
            self._on_event({"event": "status_changed", "service": service, "status": status.name})

    def _remove_watcher(self, watcher: Watcher) -> None:
        """Called by Watcher.close() to unregister."""
        with self._lock:
            service = watcher._service
            watchers = self._watchers.get(service)
            if watchers:
                watchers.discard(watcher)
                if not watchers:
                    del self._watchers[service]
            self._total_watchers -= 1
