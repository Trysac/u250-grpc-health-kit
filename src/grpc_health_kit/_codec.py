from ._errors import HealthError
from ._serving_status import ServingStatus


def _encode_varint(value: int) -> bytes:
    """Encode an unsigned integer as a protobuf varint."""
    if value < 0:
        raise ValueError("varint cannot be negative")
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


def _decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Decode a varint starting at pos, enforcing the 10-byte limit.

    Returns (value, new_pos). Raises HealthError('malformed_message') on invalid input.
    """
    result = 0
    shift = 0
    start = pos
    while True:
        if pos >= len(data):
            raise HealthError("malformed_message")
        byte = data[pos]
        pos += 1
        if pos - start > 10:
            raise HealthError("malformed_message")
        if shift >= 64:
            raise HealthError("malformed_message")
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
        if shift > 63:
            raise HealthError("malformed_message")
    return result, pos


class Codec:
    """Hand-written protobuf codec for HealthCheckRequest/Response."""

    @staticmethod
    def encode_request(service: str) -> bytes:
        """Encode a HealthCheckRequest. Empty service encodes to b'' (default)."""
        encoded = service.encode("utf-8")
        if len(encoded) > 1024:
            raise HealthError("service_too_long")
        if not encoded:
            return b""
        return b"\x0a" + _encode_varint(len(encoded)) + encoded

    @staticmethod
    def decode_request(data: bytes) -> str:
        """Decode a HealthCheckRequest. Returns the service string."""
        if len(data) > 4096:
            raise HealthError("malformed_message")
        service = ""
        pos = 0
        while pos < len(data):
            tag, pos = _decode_varint(data, pos)
            field_number = tag >> 3
            wire_type = tag & 0x7
            if field_number == 0:
                raise HealthError("malformed_message")
            if wire_type == 0:
                _, pos = _decode_varint(data, pos)
            elif wire_type == 1:
                if pos + 8 > len(data):
                    raise HealthError("malformed_message")
                pos += 8
            elif wire_type == 2:
                length, pos = _decode_varint(data, pos)
                if pos + length > len(data):
                    raise HealthError("malformed_message")
                if field_number == 1:
                    try:
                        service = data[pos : pos + length].decode("utf-8")
                    except UnicodeDecodeError:
                        raise HealthError("malformed_message") from None
                pos += length
            elif wire_type == 5:
                if pos + 4 > len(data):
                    raise HealthError("malformed_message")
                pos += 4
            elif wire_type in (3, 4):
                raise HealthError("malformed_message")
            else:
                raise HealthError("malformed_message")
        if len(service.encode("utf-8")) > 1024:
            raise HealthError("service_too_long")
        return service

    @staticmethod
    def encode_response(status: ServingStatus) -> bytes:
        """Encode a HealthCheckResponse. UNKNOWN encodes to b'' (default)."""
        if status == ServingStatus.UNKNOWN:
            return b""
        return b"\x08" + _encode_varint(status.value)

    @staticmethod
    def decode_response(data: bytes) -> ServingStatus:
        """Decode a HealthCheckResponse. Unknown status numbers become UNKNOWN."""
        if len(data) > 4096:
            raise HealthError("malformed_message")
        status_value = 0
        pos = 0
        while pos < len(data):
            tag, pos = _decode_varint(data, pos)
            field_number = tag >> 3
            wire_type = tag & 0x7
            if field_number == 0:
                raise HealthError("malformed_message")
            if wire_type == 0:
                value, pos = _decode_varint(data, pos)
                if field_number == 1:
                    status_value = value
            elif wire_type == 1:
                if pos + 8 > len(data):
                    raise HealthError("malformed_message")
                pos += 8
            elif wire_type == 2:
                length, pos = _decode_varint(data, pos)
                if pos + length > len(data):
                    raise HealthError("malformed_message")
                pos += length
            elif wire_type == 5:
                if pos + 4 > len(data):
                    raise HealthError("malformed_message")
                pos += 4
            elif wire_type in (3, 4):
                raise HealthError("malformed_message")
            else:
                raise HealthError("malformed_message")
        try:
            return ServingStatus(status_value)
        except ValueError:
            return ServingStatus.UNKNOWN
