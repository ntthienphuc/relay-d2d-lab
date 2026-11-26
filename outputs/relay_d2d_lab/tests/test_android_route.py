import asyncio
import time

import pytest

from lab import records
from lab.network import Engine
from lab.packet import ACK, DATA, Packet


class PhoneRelay(asyncio.DatagramProtocol):
    """UDP peer fixture for the Android single-hop route."""
    def __init__(self):
        self.target = None
        self.origins = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, raw, address):
        packet = Packet.decode(raw)
        key = packet.run, packet.seq, packet.sent_ns
        if packet.kind == DATA and packet.hops == 0:
            self.origins[key] = address
            packet.hops = 1
            self.transport.sendto(packet.encode(), self.target)
        elif packet.kind == ACK and address == self.target and key in self.origins:
            self.transport.sendto(raw, self.origins.pop(key))


def test_android_relay_laptop_endpoints_and_kind_guard(tmp_path, monkeypatch):
    monkeypatch.setattr(records, 'RESULTS', tmp_path)

    async def exercise():
        engine = Engine()
        await engine.open(practice=True)
        loop = asyncio.get_running_loop()
        transport, phone = await loop.create_datagram_endpoint(PhoneRelay, local_addr=('127.0.0.1', 0))
        ip, port = transport.get_extra_info('sockname')
        engine.devices['phone'] = {
            'role': 'relay', 'platform': 'android', 'running': True,
            'last_seen': time.time(), 'local_ip': ip, 'listen_port': port, 'endpoint': [ip,port],
        }

        async def configure(key, **settings):
            assert key == 'phone'
            phone.target = settings['target_ip'], settings['target_port']

        monkeypatch.setattr(engine, 'configure', configure)
        config = dict(environment='live', route='relay', relay_kind='esp32', relay_id='phone',
                      source_id='laptop', destination_id='laptop', laptop_ip='127.0.0.1',
                      rate=3, duration=1, payload=128)
        try:
            with pytest.raises(ValueError, match='Android hoặc ESP32'):
                await engine.start(config)
            assert engine.current is None
            config['relay_kind'] = 'android'
            await engine.start(config)
            await engine.task
            snapshot = engine.current.snapshot()
            assert snapshot['sent'] == snapshot['received_observed'] == snapshot['acked'] == 3
            assert engine.current.config['relay_kind'] == 'android'
            for trace in engine.current.traces.values():
                events = {event['type']: event for event in trace['events']}
                assert events['send']['sent_ns'] == events['receive']['sent_ns'] == events['ack']['sent_ns']
                assert events['receive']['hops'] == events['ack']['hops'] == 1
        finally:
            transport.close()
            engine.close()

    asyncio.run(exercise())

