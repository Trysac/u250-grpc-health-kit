"""
The gRPC health checking protocol for Python without protoc or protobuf: a status registry, Check
and Watch semantics, a hand-written wire codec and a grpcio handler adapter
"""

from __future__ import annotations

__all__ = ["__version__", "normalize"]

__version__ = "0.1.0"


def normalize(value: str) -> str:
    """Return ``value`` trimmed and lower-cased.

    Placeholder API created by the template: replace it with the utility's real behavior.

    Raises:
        ValueError: if ``value`` is empty or only whitespace.
    """
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("value must not be empty")
    return cleaned.lower()
