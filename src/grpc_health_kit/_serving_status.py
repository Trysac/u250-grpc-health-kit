from enum import IntEnum


class ServingStatus(IntEnum):
    """Serving status per grpc.health.v1.HealthCheckResponse."""

    UNKNOWN = 0
    SERVING = 1
    NOT_SERVING = 2
    SERVICE_UNKNOWN = 3
