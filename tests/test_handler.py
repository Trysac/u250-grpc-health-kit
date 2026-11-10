from types import SimpleNamespace

import pytest

from grpc_health_kit import Codec, HealthRegistry, ServingStatus, generic_handler


class FakeGrpc:
    StatusCode = SimpleNamespace(NOT_FOUND=5)

    @staticmethod
    def method_handlers_generic_handler(service_name, handlers):
        return SimpleNamespace(service_name=service_name, handlers=handlers)

    @staticmethod
    def unary_unary_rpc_method_handler(func, request_deserializer, response_serializer):
        return SimpleNamespace(
            function=func,
            request_deserializer=request_deserializer,
            response_serializer=response_serializer,
        )

    @staticmethod
    def unary_stream_rpc_method_handler(func, request_deserializer, response_serializer):
        return SimpleNamespace(
            function=func,
            request_deserializer=request_deserializer,
            response_serializer=response_serializer,
        )


def test_generic_handler_creation():
    registry = HealthRegistry()
    handler = generic_handler(registry, FakeGrpc)
    assert handler.service_name == "grpc.health.v1.Health"
    assert set(handler.handlers.keys()) == {"Check", "Watch"}
    check_handler = handler.handlers["Check"]
    watch_handler = handler.handlers["Watch"]
    assert check_handler.request_deserializer == Codec.decode_request
    assert check_handler.response_serializer == Codec.encode_response
    assert watch_handler.request_deserializer == Codec.decode_request
    assert watch_handler.response_serializer == Codec.encode_response


def test_check_handler_known_service():
    registry = HealthRegistry()
    registry.set("svc", ServingStatus.NOT_SERVING)
    handler = generic_handler(registry, FakeGrpc).handlers["Check"]
    context = SimpleNamespace()
    # request will be deserialized to string "svc"
    result = handler.function("svc", context)
    # the handler returns the enum; grpcio serialises it exactly once
    assert result is ServingStatus.NOT_SERVING
    assert handler.response_serializer(result) == Codec.encode_response(ServingStatus.NOT_SERVING)
    assert handler.response_serializer(result) == b"\x08\x02"


def test_check_handler_unknown_service_aborts():
    registry = HealthRegistry()
    handler = generic_handler(registry, FakeGrpc).handlers["Check"]
    context = SimpleNamespace(abort_called=False)

    def abort(code, message):
        context.abort_called = True
        assert code == FakeGrpc.StatusCode.NOT_FOUND
        assert message == "unknown service"
        raise RuntimeError("aborted")

    context.abort = abort
    with pytest.raises(RuntimeError, match="aborted"):
        handler.function("unknown", context)
    assert context.abort_called


def test_watch_handler_yields_and_closes():
    registry = HealthRegistry()
    registry.set("svc", ServingStatus.SERVING)
    handler = generic_handler(registry, FakeGrpc).handlers["Watch"]
    context = SimpleNamespace(is_active_count=3)

    def is_active():
        context.is_active_count -= 1
        return context.is_active_count >= 0

    context.is_active = is_active
    # The watcher is internal to the generator; after it exhausts we only need to check
    # that the registry's total_watchers is 0.
    gen = handler.function("svc", context)
    results = list(gen)
    # The first yield should be initial status
    assert len(results) == 1
    assert results[0] is ServingStatus.SERVING
    assert handler.response_serializer(results[0]) == b"\x08\x01"
    # After generator completes, watcher should be closed.
    assert registry._total_watchers == 0
