"""Walk through the real demo packet parser without transmitting network data."""
from packet_codec import Packet, DATA, payload_for


def relay_step(raw):
    packet = Packet.decode(raw)  # header length/version/hop + payload CRC32
    if packet.kind != DATA or packet.hops >= 1:
        raise ValueError('Only first-hop DATA may be relayed')
    if packet.payload != payload_for(packet.run, packet.seq, len(packet.payload)):
        raise ValueError('Unexpected test payload')
    packet.hops += 1
    return packet.encode()


if __name__ == '__main__':
    source = Packet(DATA, 7, 12, 123456789, payload_for(7, 12, 128))
    wire = source.encode()
    dest = Packet.decode(relay_step(wire))
    assert dest.payload == source.payload and dest.hops == 1
    corrupted = bytearray(wire); corrupted[-1] ^= 1
    try:
        relay_step(bytes(corrupted))
    except ValueError as exc:
        print('PASS: bad payload rejected:', exc)
    else:
        raise AssertionError('CRC corruption should have been rejected')
    print('PASS: 32-byte header + 128-byte payload; sequence preserved; hop incremented')
