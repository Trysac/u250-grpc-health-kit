import threading
import time

import pytest

from grpc_health_kit import HealthError, HealthRegistry, ServingStatus


def test_initial_overall_status():
    registry = HealthRegistry()
    assert registry.check("") == ServingStatus.SERVING


def test_set_and_check():
    registry = HealthRegistry()
    registry.set("orders", ServingStatus.NOT_SERVING)
    assert registry.check("orders") == ServingStatus.NOT_SERVING
    with pytest.raises(HealthError) as exc_info:
        registry.check("billing")
    assert exc_info.value.code == "not_found"


def test_services_sorted_includes_empty():
    registry = HealthRegistry()
    registry.set("z", ServingStatus.SERVING)
    registry.set("a", ServingStatus.SERVING)
    assert registry.services() == ["", "a", "z"]


def test_set_invalid_status():
    registry = HealthRegistry()
    with pytest.raises(HealthError) as exc_info:
        registry.set("svc", 1)  # type: ignore
    assert exc_info.value.code == "invalid_status"
    with pytest.raises(HealthError) as exc_info:
        registry.set("svc", ServingStatus.SERVICE_UNKNOWN)
    assert exc_info.value.code == "invalid_status"


def test_watch_unregistered_initial_service_unknown():
    registry = HealthRegistry()
    watcher = registry.watch("billing")
    assert watcher.poll() == ServingStatus.SERVICE_UNKNOWN
    assert watcher.poll() is None
    watcher.close()


def test_watch_coalescing():
    registry = HealthRegistry()
    registry.set("billing", ServingStatus.SERVING)
    watcher = registry.watch("billing")
    # consume initial SERVING
    assert watcher.poll() == ServingStatus.SERVING
    # set NOT_SERVING then SERVING quickly
    registry.set("billing", ServingStatus.NOT_SERVING)
    registry.set("billing", ServingStatus.SERVING)
    # should only get latest
    assert watcher.poll() == ServingStatus.SERVING
    assert watcher.poll() is None
    watcher.close()


def test_set_same_status_no_notify():
    events: list[dict[str, object]] = []
    registry = HealthRegistry(on_event=events.append)
    registry.set("svc", ServingStatus.SERVING)
    events.clear()
    registry.set("svc", ServingStatus.SERVING)
    assert events == []


def test_enter_graceful_shutdown():
    events: list[dict[str, object]] = []
    registry = HealthRegistry(on_event=events.append)
    registry.set("orders", ServingStatus.SERVING)
    registry.set("billing", ServingStatus.SERVING)
    watcher = registry.watch("orders")
    watcher.poll()  # consume initial
    registry.enter_graceful_shutdown()
    # check statuses
    assert registry.check("") == ServingStatus.NOT_SERVING
    assert registry.check("orders") == ServingStatus.NOT_SERVING
    assert registry.check("billing") == ServingStatus.NOT_SERVING
    # watcher receives NOT_SERVING
    assert watcher.poll() == ServingStatus.NOT_SERVING
    # later set ignored
    events.clear()
    registry.set("orders", ServingStatus.SERVING)
    assert len(events) == 1
    assert events[0]["event"] == "ignored_after_shutdown"
    assert events[0]["service"] == "orders"
    # status unchanged
    assert registry.check("orders") == ServingStatus.NOT_SERVING
    watcher.close()


def test_max_watchers():
    registry = HealthRegistry(max_watchers=1)
    watcher1 = registry.watch("svc")
    with pytest.raises(HealthError) as exc_info:
        registry.watch("svc2")
    assert exc_info.value.code == "too_many_watchers"
    watcher1.close()
    watcher2 = registry.watch("svc")  # should succeed
    watcher2.close()


def test_max_services():
    registry = HealthRegistry(max_services=2)
    registry.set("a", ServingStatus.SERVING)
    with pytest.raises(HealthError) as exc_info:
        registry.set("b", ServingStatus.SERVING)
    assert exc_info.value.code == "too_many_services"


def test_watcher_close_unregisters():
    registry = HealthRegistry()
    watcher = registry.watch("svc")
    assert registry._total_watchers == 1
    # an unregistered service starts with the initial SERVICE_UNKNOWN pending
    assert watcher.poll() == ServingStatus.SERVICE_UNKNOWN
    watcher.close()
    assert registry._total_watchers == 0
    # ensure watcher no longer receives notifications
    registry.set("svc", ServingStatus.NOT_SERVING)
    assert watcher.poll() is None


def test_watcher_wait_timeout():
    registry = HealthRegistry()
    watcher = registry.watch("svc")
    watcher.poll()  # consume initial
    start = time.monotonic()
    result = watcher.wait(0.1)
    elapsed = time.monotonic() - start
    assert result is None
    assert elapsed >= 0.1 and elapsed < 0.5
    watcher.close()


def test_watcher_closed_while_waiting():
    registry = HealthRegistry()
    watcher = registry.watch("svc")
    watcher.poll()  # consume initial
    result_holder = []

    def wait_thread():
        result_holder.append(watcher.wait(5.0))

    t = threading.Thread(target=wait_thread)
    t.start()
    time.sleep(0.1)
    watcher.close()
    t.join()
    assert result_holder[0] is None


def test_thread_safety():
    registry = HealthRegistry()
    service = "svc"
    watcher = registry.watch(service)
    watcher.poll()  # consume initial

    def setter():
        for i in range(100):
            status = ServingStatus.SERVING if i % 2 == 0 else ServingStatus.NOT_SERVING
            registry.set(service, status)

    threads = [threading.Thread(target=setter) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # final status should be one of the set values
    final_status = registry.check(service)
    assert final_status in (ServingStatus.SERVING, ServingStatus.NOT_SERVING)
    # watcher should have received at least one update
    assert watcher.poll() is not None
    watcher.close()


def test_on_event_status_change():
    events: list[dict[str, object]] = []
    registry = HealthRegistry(on_event=events.append)
    registry.set("svc", ServingStatus.NOT_SERVING)
    assert events == [{"event": "status_changed", "service": "svc", "status": "NOT_SERVING"}]
