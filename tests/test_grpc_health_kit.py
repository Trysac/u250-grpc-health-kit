"""Behavior tests for the public API of grpc_health_kit."""

from __future__ import annotations

import pytest

import grpc_health_kit


def test_normalize_trims_and_lowercases() -> None:
    assert grpc_health_kit.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        grpc_health_kit.normalize(value)


def test_version_is_semver() -> None:
    parts = grpc_health_kit.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
