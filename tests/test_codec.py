import pytest

from grpc_health_kit import Codec, HealthError, ServingStatus


def test_encode_request_simple():
    assert Codec.encode_request("svc") == b"\x0a\x03svc"
    assert Codec.encode_request("") == b""


def test_encode_request_service_too_long():
    long_service = "a" * 1025
    with pytest.raises(HealthError) as exc_info:
        Codec.encode_request(long_service)
    assert exc_info.value.code == "service_too_long"


def test_encode_request_1024_ok():
    service_1024 = "a" * 1024
    encoded = Codec.encode_request(service_1024)
    assert len(encoded) == 1027  # tag (1 byte) + length varint (2 bytes) + data


def test_encode_response():
    assert Codec.encode_response(ServingStatus.SERVING) == b"\x08\x01"
    assert Codec.encode_response(ServingStatus.NOT_SERVING) == b"\x08\x02"
    assert Codec.encode_response(ServingStatus.UNKNOWN) == b""


def test_request_non_ascii_roundtrip():
    service = "café-日本"
    encoded = service.encode("utf-8")
    data = Codec.encode_request(service)
    assert data == b"\x0a" + _varint(len(encoded)) + encoded
    assert Codec.decode_request(data) == service


def test_decode_empty_request():
    # proto3 omits the default empty service name
    assert Codec.decode_request(b"") == ""


def test_decode_empty_response():
    # proto3 omits the default UNKNOWN status
    assert Codec.decode_response(b"") is ServingStatus.UNKNOWN


def test_request_1024_byte_limit_is_utf8_bytes():
    # 512 two-byte characters == 1024 UTF-8 bytes: accepted
    accepted = "é" * 512
    assert len(accepted.encode("utf-8")) == 1024
    data = Codec.encode_request(accepted)
    assert Codec.decode_request(data) == accepted
    # 513 two-byte characters == 1026 UTF-8 bytes: rejected on encode and decode
    rejected = "é" * 513
    with pytest.raises(HealthError) as exc_info:
        Codec.encode_request(rejected)
    assert exc_info.value.code == "service_too_long"
    rejected_wire = b"\x0a" + _varint(len(rejected.encode("utf-8"))) + rejected.encode("utf-8")
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(rejected_wire)
    assert exc_info.value.code == "service_too_long"


def test_decode_request_unknown_field_skipped():
    # field 2 (varint) with value 1, then field 1 (string) 'a'
    data = b"\x10\x01\x0a\x01a"
    assert Codec.decode_request(data) == "a"


def test_decode_request_last_wins():
    data = b"\x0a\x01a\x0a\x01b"
    assert Codec.decode_request(data) == "b"


def test_decode_response_not_serving():
    assert Codec.decode_response(b"\x08\x02") is ServingStatus.NOT_SERVING


def test_decode_response_unknown_status_becomes_unknown():
    assert Codec.decode_response(b"\x08\x7f") is ServingStatus.UNKNOWN


def test_decode_request_malformed_truncated_tag():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(b"\x0a")
    assert exc_info.value.code == "malformed_message"


def test_decode_request_malformed_truncated_length():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(b"\x0a\x05ab")
    assert exc_info.value.code == "malformed_message"


def test_decode_request_malformed_invalid_utf8():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(b"\x0a\x01\xff")
    assert exc_info.value.code == "malformed_message"


def test_decode_request_malformed_field_number_zero():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(b"\x00")
    assert exc_info.value.code == "malformed_message"


def test_decode_request_malformed_wire_type_group():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(b"\x0b")  # tag: field 1, wire type 3
    assert exc_info.value.code == "malformed_message"


def test_decode_request_malformed_input_too_large():
    data = b"\x00" * 4097
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(data)
    assert exc_info.value.code == "malformed_message"


def test_decode_request_service_too_long_after_decode():
    # encode a valid protobuf with a 1025-byte service
    long_service = "a" * 1025
    data = b"\x0a" + _varint(len(long_service.encode())) + long_service.encode()
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_request(data)
    assert exc_info.value.code == "service_too_long"


def test_decode_response_malformed_truncated_value():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_response(b"\x08")
    assert exc_info.value.code == "malformed_message"


def test_decode_response_malformed_field_number_zero():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_response(b"\x00")
    assert exc_info.value.code == "malformed_message"


def test_decode_response_malformed_wire_type_group():
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_response(b"\x0b")
    assert exc_info.value.code == "malformed_message"


def test_decode_response_malformed_input_too_large():
    data = b"\x00" * 4097
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_response(data)
    assert exc_info.value.code == "malformed_message"


def test_decode_response_varint_10_bytes_ok():
    # 10-byte varint for field 1 (status)
    value = 2**64 - 1
    varint = _varint(value)
    assert len(varint) == 10
    data = b"\x08" + varint
    # should parse and become UNKNOWN (since value is too large for enum)
    assert Codec.decode_response(data) is ServingStatus.UNKNOWN


def test_decode_response_varint_11_bytes_malformed():
    # construct a varint that continues beyond 10 bytes
    varint = b"\x80" * 10 + b"\x01"
    data = b"\x08" + varint
    with pytest.raises(HealthError) as exc_info:
        Codec.decode_response(data)
    assert exc_info.value.code == "malformed_message"


# Helper to encode varint in tests (duplicate of private function for independence)
def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            break
    return bytes(out)
