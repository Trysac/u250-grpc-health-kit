# Testing

Tests use `pytest`. The only test module present is `tests/test_codec.py`; there are no registry or handler test modules in the repository.

## Running Tests

```bash
pytest
```

## Test Structure

- `tests/test_codec.py`: covers `Codec.encode_request` and `Codec.decode_request` for a simple service, the 1024 UTF-8 byte boundary and the 1025-byte `service_too_long` failure, a non-ASCII service roundtrip, decoding of an empty request, unknown varint fields being skipped, a repeated field 1 where the last value wins, and the UTF-8 byte length limit.
- `tests/test_codec.py`: covers `Codec.encode_response` and `Codec.decode_response` for `SERVING`, `NOT_SERVING` and `UNKNOWN`, decoding of an empty response, and an unknown status number becoming `UNKNOWN`.
- The module uses `pytest.raises` for `HealthError` cases and plain assertions for the positive cases.

## Conformance

No external tools, network access or downloaded files are required. The tests exercise the codec directly; no test module exercises `HealthRegistry`, `Watcher` or `generic_handler` in the repository.
