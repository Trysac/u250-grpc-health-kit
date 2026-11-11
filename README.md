# trysac-grpc-health-kit

`grpc_health_kit` implements the gRPC Health Checking Protocol (`grpc.health.v1.Health`) in Python without a protobuf runtime or generated stubs. It provides a hand-written codec for the two protocol messages, a thread-safe status registry with Check and Watch semantics, and an adapter for grpcio's generic handler API. Services use it to answer Kubernetes probes, load balancers and service meshes and to flip to NOT_SERVING during shutdown.

## Features

- `ServingStatus` enum with UNKNOWN, SERVING, NOT_SERVING and SERVICE_UNKNOWN values from `grpc/health/v1/health.proto`.
- Hand-written protobuf codec for `HealthCheckRequest` and `HealthCheckResponse`; no protoc, no generated code.
- Thread-safe `HealthRegistry`; the empty service name is initialised to SERVING.
- Coalescing `Watcher` that stores only the latest undelivered status.
- `enter_graceful_shutdown()` sets every registered service to NOT_SERVING and makes later `set` calls ignored.
- `generic_handler()` registers `Check` as unary-unary and `Watch` as unary-stream on a grpcio server; the grpc module is passed by the caller.
- Optional `on_event` callback for status changes and shutdown events.
- Uses only the Python standard library; grpcio is not a runtime dependency.

## Installation

```bash
pip install trysac-grpc-health-kit
```

Import name is `grpc_health_kit`. Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from grpc_health_kit import Codec, HealthRegistry, ServingStatus

registry = HealthRegistry()
registry.set("orders", ServingStatus.SERVING)
assert registry.check("orders") is ServingStatus.SERVING
assert Codec.decode_request(Codec.encode_request("orders")) == "orders"
watcher = registry.watch("orders")
assert watcher.poll() is ServingStatus.SERVING
watcher.close()
```

## Public API

- `ServingStatus(IntEnum)`: `UNKNOWN = 0`, `SERVING = 1`, `NOT_SERVING = 2`, `SERVICE_UNKNOWN = 3`.
- `HealthError(code)`: exception with `code` in `malformed_message`, `service_too_long`, `not_found`, `too_many_watchers`, `too_many_services`, `invalid_status`.
- `Codec.encode_request(service: str) -> bytes`: empty service returns `b''`; service longer than 1024 UTF-8 bytes raises `HealthError('service_too_long')`.
- `Codec.decode_request(data: bytes) -> str`: input over 4096 bytes or malformed wire data raises `HealthError('malformed_message')`; a decoded service over 1024 UTF-8 bytes raises `service_too_long`; a repeated field 1 keeps the last value.
- `Codec.encode_response(status: ServingStatus) -> bytes`: `UNKNOWN` returns `b''`.
- `Codec.decode_response(data: bytes) -> ServingStatus`: input over 4096 bytes raises `malformed_message`; unknown status numbers decode as `UNKNOWN`.
- `HealthRegistry(*, max_services: int = 1000, max_watchers: int = 1000, on_event: Callable[[dict[str, object]], None] | None = None)`.
- `HealthRegistry.set(service, status)`: rejects a non-`ServingStatus` value or `SERVICE_UNKNOWN` with `invalid_status`; raises `too_many_services` when registering beyond the limit; after graceful shutdown it ignores the call and emits `ignored_after_shutdown` if `on_event` is set.
- `HealthRegistry.check(service)`: raises `not_found` for an unregistered service.
- `HealthRegistry.watch(service)`: raises `too_many_watchers` at the limit; the watcher starts with the current status, or `SERVICE_UNKNOWN` for an unregistered service.
- `HealthRegistry.services()`: returns a sorted list of registered service names, including the empty name.
- `HealthRegistry.enter_graceful_shutdown()`: sets all registered services to `NOT_SERVING` and makes the registry terminal.
- `Watcher.poll()`: returns the latest pending status or `None`.
- `Watcher.wait(timeout: float)`: returns the latest pending status, or `None` on timeout or after `close()`.
- `Watcher.close()`: idempotent; unregisters the watcher and wakes waiting threads.
- `generic_handler(registry, grpc)`: returns a handler for `grpc.health.v1.Health` with `Check` and `Watch`; `Check` of an unknown service calls `context.abort(grpc.StatusCode.NOT_FOUND, 'unknown service')`; `Watch` yields `watcher.wait(0.5)` while `context.is_active()` and closes the watcher in `finally`.

## Why not grpcio-health-checking

`grpcio-health-checking` requires the protobuf runtime and generated code. This package encodes the two health messages directly, keeps one pending status per watcher rather than an unbounded queue, exposes a registry that can be tested without a gRPC server, and provides an explicit terminal shutdown transition.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and limits.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Project](docs/PROJECT.md)
- [Security](docs/SECURITY.md)
- [Testing](docs/TESTING.md)

## License

MIT
