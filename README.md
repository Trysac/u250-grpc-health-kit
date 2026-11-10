# grpc-health-kit

[![PyPI version](https://img.shields.io/pypi/v/trysac-grpc-health-kit)](https://pypi.org/project/trysac-grpc-health-kit/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-grpc-health-kit)](LICENSE)
[![CI](https://github.com/Trysac/u250-grpc-health-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u250-grpc-health-kit/actions/workflows/ci.yml)

The gRPC health checking protocol for Python without protoc or protobuf: a status registry, Check and Watch semantics, a hand-written wire codec and a grpcio handler adapter

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-grpc-health-kit
# or
uv add trysac-grpc-health-kit
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import grpc_health_kit

# normalize() trims surrounding whitespace and lower-cases the text.
print(grpc_health_kit.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    grpc_health_kit.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
