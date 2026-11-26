import time
import pytest
from lab.packet import Packet,DATA,ACK,payload_for
from lab.records import Run
from lab.devices import register,endpoint

def test_header_reserved_flags_and_ack_body_rejected():
    raw=Packet(DATA,1,2,3,payload_for(1,2,16)).encode()
    for offset in (7,26):
        damaged=bytearray(raw);damaged[offset]=1
        with pytest.raises(ValueError): Packet.decode(damaged)
    with pytest.raises(ValueError):Packet(ACK,1,2,3,b'x').encode()

def test_remote_source_out_of_order_receipts_and_duplicate_ack(tmp_path,monkeypatch):
    import lab.records
    monkeypatch.setattr(lab.records,'RESULTS',tmp_path)
    r=Run(123,{'duration':1,'rate':2,'payload':128,'source_id':'phone','environment':'test'},'unit')
    try:
        r.event({'type':'receive','node':'D','seq':0,'bytes':128})
        ack={'type':'ack','node':'S','seq':0,'sent_ns':999,'rtt_ms':12.5,'event_id':'ack0'}
        r.source_event(ack)
        assert r.snapshot()['delivery_confirmed']==0
        r.source_event({'type':'send','node':'S','seq':0,'sent_ns':999,'bytes':128,'event_id':'send0'})
        r.source_event(ack)
        assert r.snapshot()['delivery_confirmed']==1 and r.snapshot()['acked']==1
        assert r.rtts==[12.5]
        r.source_event({'type':'send','node':'S','seq':1,'sent_ns':1000,'event_id':'send1'})
        r.source_event({'type':'ack','node':'S','seq':1,'sent_ns':1001,'rtt_ms':1})
        assert r.snapshot()['acked']==1 and r.snapshot()['pdr_confirmed']==.5
        assert r.snapshot()['pdr_ci95_iid'][0]<.5<r.snapshot()['pdr_ci95_iid'][1]
        r.source_event({'type':'source_done','seq':-1,'source_elapsed_s':1})
        assert -1 not in r.traces and r.source_done
    finally:r.close();r.log.close()

def test_device_requires_udp_heartbeat_and_clears_old_session_endpoint():
    nodes={};d={'id':'esp','role':'relay','listen_port':39010,'local_ip':'192.168.1.5','running':True,'session':'a'}
    register(nodes,d)
    with pytest.raises(ValueError):endpoint(nodes,'esp')
    register(nodes,d,('192.168.1.5',39010));assert endpoint(nodes,'esp')==('192.168.1.5',39010)
    register(nodes,{**d,'session':'b'})
    with pytest.raises(ValueError):endpoint(nodes,'esp')

def test_reject_invalid_identity():
    for data in ({},{'id':'x','role':'not-node'},{'id':'x','role':'sink','listen_port':70000}):
        with pytest.raises(ValueError):register({},data)


def test_esp_softap_routes_to_private_sink_and_rejects_invalid_topologies(tmp_path,monkeypatch):
    """Control-plane contract only; this does not emulate ESP32 Wi-Fi."""
    import asyncio
    import lab.records
    from lab.network import Engine
    monkeypatch.setattr(lab.records,'RESULTS',tmp_path)
    async def scenario():
        e=Engine();commands=[]
        for key,role,ip,port,bridge in [('a','source','192.168.1.10',39020,''),
                                     ('esp','relay','192.168.1.20',39010,''),
                                     ('b','sink','192.168.50.2',39021,'esp')]:
            register(e.devices,dict(id=key,role=role,local_ip=ip,listen_port=port,
                bridge_id=bridge,platform='esp32' if key=='esp' else 'android',
                running=True,session='test'),('192.168.1.20',39001) if bridge else (ip,port))
        async def configure(key,**changes):commands.append((key,changes))
        e.configure=configure
        cfg=dict(environment='live',route='relay',source_id='a',relay_id='esp',
                 destination_id='b',laptop_ip='192.168.1.2',duration=1,rate=20,payload=128)
        with pytest.raises(ValueError,match='SoftAP'):
            await e.start({**cfg,'route':'direct'})
        with pytest.raises(ValueError,match='50'):
            await e.start({**cfg,'rate':51})
        with pytest.raises(ValueError,match='LOOPBACK'):
            await e.start({**cfg,'route':'direct','source_id':'laptop','destination_id':'laptop'})
        await e.start(cfg)
        assert commands[0][0]=='esp'
        assert (commands[0][1]['target_ip'],commands[0][1]['target_port'])==('192.168.50.2',39021)
        assert commands[1][0]=='a'
        assert (commands[1][1]['target_ip'],commands[1][1]['target_port'])==('192.168.1.20',39010)
        await asyncio.sleep(0)
        e.task.cancel();await e.task;e.close()
    asyncio.run(scenario())
