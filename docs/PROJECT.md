# Project record

## Objective

Implement the gRPC health checking protocol for Python without protoc or protobuf: a status registry, Check and Watch semantics, a hand-written wire codec and a grpcio handler adapter.

## Scope

- In scope: the public API documented in [README.md](../README.md): `ServingStatus`, `HealthError`, `Codec`, `HealthRegistry`, `Watcher` and `generic_handler`, with typed and tested behaviour.
- In scope: a standard-library-only package; the caller passes the imported `grpc` module to `generic_handler`.
- Out of scope: server reflection. It needs descriptor pools and the protobuf runtime, which `grpcio-reflection` already provides, so this package stays protobuf-free.
- Out of scope: a client probe CLI.
- Out of scope: asyncio servers; an aio adapter is documented as future work.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays pending measurement.

| Metric | Value |
|---|---|
| Tokens (input / output) | 991534 / 59361 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0945 |

## Factory run u250 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1931 | 20744 | 0 | 3328 | 0.0424 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 24413 | 9966 | 0 | 247168 | 0.0104 |
| 2026-11-10 | audit | deepseek-flash | no | 32433 | 13400 | 0 | 401408 | 0.0141 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 13655 | 4060 | 0 | 161152 | 0.0050 |
| 2026-11-10 | docs | deepseek-flash | no | 105790 | 11191 | 0 | 256 | 0.0226 |

Total: $0.0945. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
