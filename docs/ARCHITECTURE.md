# Architecture

## Overview

`grpc_health_kit` implements the gRPC health checking protocol defined in `grpc/health/v1/health.proto` without relying on protobuf or grpcio. It is composed of independent components:

- `ServingStatus`: enum mirroring the proto enum.
- `Codec`: encodes/decodes `HealthCheckRequest` and `HealthCheckResponse` following the protobuf wire format.
- `HealthRegistry`: thread-safe store of service statuses, supporting `set`, `check`, `watch`, `services`, and `enter_graceful_shutdown`.
- `Watcher`: exposes `poll` and `wait` for status updates, coalescing multiple updates into a single pending status.
- `generic_handler`: adapts the registry to grpcio's generic handler interface, enabling integration without a servicer.

## Wire Format

The two messages are simple:

- `HealthCheckRequest { string service = 1; }`
- `HealthCheckResponse { ServingStatus status = 1; }`

Encoding follows protobuf: field 1 string uses tag `0x0a`; field 1 enum uses tag `0x08`. Empty strings and the `UNKNOWN` status are omitted (proto3 default values). Decoding skips unknown fields of wire types 0, 1, 2, and 5, and rejects groups (types 3, 4), field number 0, malformed varints (more than 10 bytes), truncated data, and invalid UTF-8. Input is limited to 4096 bytes to prevent abuse. The service string is limited to 1024 UTF-8 bytes.

## Registry Semantics

The overall server status is keyed by the empty service name `""`. Initially `SERVING`. `check` for an unregistered service raises `HealthError('not_found')`. `watch` always succeeds for any service; if unregistered, the watcher's initial status is `SERVICE_UNKNOWN`. Status changes are broadcast to watchers for that service only; each watcher stores only the latest undelivered status, ensuring constant memory per watcher. `enter_graceful_shutdown` sets all services to `NOT_SERVING` and marks the registry terminal: subsequent `set` calls are ignored and emit an `ignored_after_shutdown` event.

## Handler Adapter

`generic_handler(registry, grpc)` registers `grpc.health.v1.Health` with a `Check` unary-unary method and a `Watch` unary-stream method. Both handlers return or yield `ServingStatus` enum values; the `response_serializer=Codec.encode_response` registered on each method encodes them exactly once, so a handler result must never be pre-encoded. `Check` maps an unknown service to `StatusCode.NOT_FOUND` via `context.abort`; `Watch` yields statuses from `watcher.wait(0.5)` while `context.is_active()` and closes the watcher in a `finally` block.

## Thread Safety

A single re-entrant lock guards the registry's internal state. Each `Watcher` has its own `threading.Condition` to manage waiting threads. `close()` is idempotent and wakes any waiting threads.

## Error Handling

All errors raised by the library are instances of `HealthError` with a stable machine-readable `code`. Codes: `malformed_message`, `service_too_long`, `not_found`, `too_many_watchers`, `too_many_services`, `invalid_status`. Messages do not contain sensitive data.

## Logging

The library uses `logging.getLogger(__name__)` and attaches a `NullHandler` to avoid interfering with application logging configuration.
