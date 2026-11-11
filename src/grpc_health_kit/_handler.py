from collections.abc import Iterator
from types import ModuleType
from typing import Any

from ._codec import Codec
from ._errors import HealthError
from ._registry import HealthRegistry
from ._serving_status import ServingStatus


def generic_handler(registry: HealthRegistry, grpc: ModuleType) -> object:
    """Create a grpc generic handler for the standard health service."""

    def check(request: str, context: Any) -> ServingStatus:
        try:
            return registry.check(request)
        except HealthError as e:
            if e.code == "not_found":
                context.abort(grpc.StatusCode.NOT_FOUND, "unknown service")
                raise
            raise

    def watch(request: str, context: Any) -> Iterator[ServingStatus]:
        watcher = registry.watch(request)
        try:
            while context.is_active():
                status = watcher.wait(0.5)
                if status is not None:
                    yield status
        finally:
            watcher.close()

    return grpc.method_handlers_generic_handler(
        "grpc.health.v1.Health",
        {
            "Check": grpc.unary_unary_rpc_method_handler(
                check,
                request_deserializer=Codec.decode_request,
                response_serializer=Codec.encode_response,
            ),
            "Watch": grpc.unary_stream_rpc_method_handler(
                watch,
                request_deserializer=Codec.decode_request,
                response_serializer=Codec.encode_response,
            ),
        },
    )
