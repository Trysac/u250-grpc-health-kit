"""grpc_health_kit: gRPC health checking protocol without protobuf."""

import logging

from ._codec import Codec
from ._errors import HealthError
from ._handler import generic_handler
from ._registry import HealthRegistry
from ._serving_status import ServingStatus
from ._watcher import Watcher

__all__ = [
    "Codec",
    "HealthError",
    "HealthRegistry",
    "ServingStatus",
    "Watcher",
    "generic_handler",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
