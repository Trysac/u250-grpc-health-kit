# Security

## Threat Model

Defended:

- Untrusted serialized messages passed to `Codec.decode_request` and `Codec.decode_response`: input size is capped at 4096 bytes before parsing; varints are limited to 10 bytes and shifts below 64; field number 0 is rejected; groups (wire types 3 and 4) are rejected; truncated fixed32, fixed64 and length-delimited fields are rejected; invalid UTF-8 in the service field raises `malformed_message`; a service name over 1024 UTF-8 bytes raises `service_too_long`.
- Unbounded registry growth: `HealthRegistry` accepts `max_services` and `max_watchers` (default 1000 each) and raises `too_many_services` or `too_many_watchers` at the limits. `set` rejects non-`ServingStatus` values and `SERVICE_UNKNOWN` with `invalid_status`. A watcher stores only the latest undelivered status.
- Accidental state changes after shutdown: `enter_graceful_shutdown()` sets all registered services to `NOT_SERVING` and makes later `set` calls ignored.

Not defended:

- Transport security, authentication and authorization: grpcio and the application own TLS, call credentials and access control. This package only implements the health messages, registry and handler adapter.
- Code running in the same process: registry methods and `on_event` callbacks are called directly with no sandbox.
- Resource exhaustion beyond the configured limits: a caller can open watchers up to `max_watchers` and register services up to `max_services`; parsing CPU time is bounded only by the 4096-byte input cap.
- No metrics, tracing or log-based detection is built in.

## Input Validation

- `Codec.decode_request` and `Codec.decode_response` reject input over 4096 bytes with `HealthError('malformed_message')` before parsing.
- Varints are limited to 10 bytes; overlong or truncated varints raise `malformed_message`.
- Field number 0 is rejected; groups (wire types 3 and 4) are rejected.
- Wire types 1 and 5 skip their fixed-width payload after checking the buffer length; wire type 2 checks the declared length against the remaining buffer.
- Invalid UTF-8 in field 1 of `HealthCheckRequest` raises `malformed_message`.
- `Codec.encode_request` and `Codec.decode_request` enforce a 1024 UTF-8 byte service name limit, raising `service_too_long`.
- An unknown status number in `HealthCheckResponse` decodes as `ServingStatus.UNKNOWN`.

## Resource Limits

- Default `max_services` and `max_watchers` are 1000 each.
- `HealthRegistry.set` raises `too_many_services` only when a new service would exceed `max_services`.
- `HealthRegistry.watch` raises `too_many_watchers` when the total number of live watchers would exceed `max_watchers`; `Watcher.close()` decrements the count.
- Each `Watcher` holds only the latest pending status.
- The registry uses one `threading.RLock`; each watcher uses a `threading.Condition`.

## Exceptions

All library errors are `HealthError` instances with a stable `code`: `malformed_message`, `service_too_long`, `not_found`, `too_many_watchers`, `too_many_services` or `invalid_status`. Error messages are the code string and contain no request data.

## Logging

The package creates `logging.getLogger(__name__)` and attaches a `logging.NullHandler`. The library does not emit log records by itself; `on_event` payloads contain event names, service names and status names supplied by the caller's registry operations.
