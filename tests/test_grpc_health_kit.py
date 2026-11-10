"""Smoke tests for the public API of grpc_health_kit."""

from __future__ import annotations

import grpc_health_kit


def test_public_api_exports() -> None:
    assert grpc_health_kit.__all__ == [
        "Codec",
        "HealthError",
        "HealthRegistry",
        "ServingStatus",
        "Watcher",
        "generic_handler",
    ]


def test_version_is_semver() -> None:
    parts = grpc_health_kit.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_serving_status_values() -> None:
    assert grpc_health_kit.ServingStatus.UNKNOWN == 0
    assert grpc_health_kit.ServingStatus.SERVING == 1
    assert grpc_health_kit.ServingStatus.NOT_SERVING == 2
    assert grpc_health_kit.ServingStatus.SERVICE_UNKNOWN == 3


def test_health_error_carries_code() -> None:
    error = grpc_health_kit.HealthError("not_found")
    assert error.code == "not_found"
    assert str(error) == "not_found"
