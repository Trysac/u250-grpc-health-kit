from typing import Literal


class HealthError(Exception):
    """Base error for grpc_health_kit."""

    def __init__(
        self,
        code: Literal[
            "malformed_message",
            "service_too_long",
            "not_found",
            "too_many_watchers",
            "too_many_services",
            "invalid_status",
        ],
    ):
        super().__init__(code)
        self.code = code
