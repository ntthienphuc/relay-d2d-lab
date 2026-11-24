import asyncio
import time
import pytest
from lab.packet import Packet, DATA, payload_for
from lab.network import Engine


def test_binary_roundtrip_corruption_and_hops():
    p=Packet(DATA,123,7,123456789,payload_for(123,7,128),hops=1)
    raw=p.encode();q=Packet.decode(raw);assert p==q and len(raw)==160
    broken=bytearray(raw);broken[-1]^=1
    with pytest.raises(ValueError):Packet.decode(broken)
    with pytest.raises(ValueError):Packet.decode(raw[:31])
    p.hops=3
    with pytest.raises(ValueError):p.encode()


def test_real_loopback_udp_loss_and_ack():
    async def run():
        # Test uses its own ephemeral UDP endpoints, avoiding running lab server.
        from lab.network import SourceProtocol, SinkProtocol, LocalRelay
        from lab.records import Run
        loop=asyncio.get_running_loop();e=Engine()
        source_t,source=await loop.create_datagram_endpoint(lambda:SourceProtocol(e),local_addr=('127.0.0.1',0))
        sink_t,sink=await loop.create_datagram_endpoint(lambda:SinkProtocol(e),local_addr=('127.0.0.1',0))
        c={'duration':1,'rate':20,'payload':128,'environment':'test','route':'direct'}
        e.current=Run(int(time.time()*1000)%0x7fffffff,c,'PYTEST localhost UDP')
        try:
            for seq in range(20):
                stamp=time.perf_counter_ns();e.current.sent[seq]=stamp
                p=Packet(DATA,e.current.id,seq,stamp,payload_for(e.current.id,seq,128))
                raw=p.encode()
                # Every fifth DATA is corrupted. Sink must reject; no ACK.
                if seq%5==0:raw=raw[:-1]+bytes([raw[-1]^1])
                source_t.sendto(raw,sink_t.get_extra_info('sockname'))
                await asyncio.sleep(.002)
            await asyncio.sleep(.2)
            assert len(e.current.received)==16
            assert len(e.current.acked)==16
            assert e.current.invalid==4
            assert all(x>=0 for x in e.current.rtts)
        finally:
            source_t.close();sink_t.close();e.current.close();e.current.log.close()
    asyncio.run(run())
