"""Wire format shared with Android Packet.java. All integers network order."""
import struct
import zlib
from dataclasses import dataclass

HEADER = struct.Struct('!4sBBBBIIQHHI')
DATA, ACK, HELLO = 1, 2, 3
MAX_PAYLOAD = 1024


@dataclass
class Packet:
    kind: int
    run: int
    seq: int
    sent_ns: int
    payload: bytes = b''
    hops: int = 0
    flags: int = 0

    def encode(self):
        if len(self.payload) > MAX_PAYLOAD or self.hops > 2:
            raise ValueError('Packet exceeds experiment limits')
        return HEADER.pack(b'RLY1', 1, self.kind, self.hops, self.flags,
                           self.run, self.seq, self.sent_ns, len(self.payload), 0,
                           zlib.crc32(self.payload)) + self.payload

    @classmethod
    def decode(cls, raw):
        if len(raw) < HEADER.size:
            raise ValueError('Truncated header')
        magic, version, kind, hops, flags, run, seq, stamp, size, _, crc = HEADER.unpack_from(raw)
        payload = raw[HEADER.size:]
        if magic != b'RLY1' or version != 1 or kind not in (DATA, ACK, HELLO):
            raise ValueError('Unknown protocol')
        if size != len(payload) or size > MAX_PAYLOAD or hops > 2:
            raise ValueError('Length or hop limit')
        if zlib.crc32(payload) != crc:
            raise ValueError('CRC32 mismatch')
        return cls(kind, run, seq, stamp, payload, hops, flags)

    def ack(self):
        return Packet(ACK, self.run, self.seq, self.sent_ns, hops=self.hops)


def payload_for(run, seq, size):
    """Known byte pattern: deterministic and identical in Java/Python."""
    return bytes((run + seq * 31 + i * 17) & 255 for i in range(size))
