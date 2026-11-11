# Implement gRPC health checking without protobuf

Status: accepted (generated, pending human review)

## Context

Kubernetes probes and other tools require gRPC services to implement health checks. Existing libraries often require protobuf runtimes and generated code, adding complexity. This utility provides a lightweight, dependency-free implementation using hand-written wire format codec and a generic handler for grpcio integration.

## Decision

Implement the gRPC Health Checking Protocol directly in Python using a custom codec for the two small messages, a thread-safe registry with coalescing watchers, and a generic handler adapter. No external dependencies; grpcio is passed as a parameter to the generic handler to avoid a hard dependency.

## Consequences

The library is small, easy to audit, and has no transitive dependencies. It requires careful maintenance of the wire encoding/decoding and protocol semantics. grpcio integration is optional and must be provided by the user at server setup time. Future extensions may require manual updates to the codec.
