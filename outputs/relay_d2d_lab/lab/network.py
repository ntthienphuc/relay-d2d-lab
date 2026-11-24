import asyncio
import json
import socket
import time
from .packet import Packet, DATA, ACK, HELLO, payload_for
from .records import Run


class SourceProtocol(asyncio.DatagramProtocol):
    def __init__(self, engine): self.e = engine
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, raw, addr):
        try:
            p = Packet.decode(raw)
            if p.kind == HELLO:
                item = json.loads(p.payload.decode())
                device = self.e.devices.setdefault(item['id'],{})
                device.update(item, endpoint=list(addr), last_seen=time.time())
                return
            run = self.e.current
            if p.kind != ACK or not run or p.run != run.id or p.seq not in run.sent:
                return
            if p.sent_ns != run.sent[p.seq] or p.seq in run.acked:
                return
            run.acked.add(p.seq)
            rtt = (time.perf_counter_ns()-p.sent_ns)/1e6
            run.rtts.append(rtt)
            run.event({'type':'ack','node':'S','seq':p.seq,'hops':p.hops,'rtt_ms':rtt})
        except (ValueError,KeyError,UnicodeError,json.JSONDecodeError):
            pass


class SinkProtocol(asyncio.DatagramProtocol):
    def __init__(self, engine): self.e = engine
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, raw, addr):
        try:
            p = Packet.decode(raw)
            if p.kind != DATA: return
            if p.payload != payload_for(p.run,p.seq,len(p.payload)):
                raise ValueError('Unexpected payload')
            if self.e.current and self.e.current.id == p.run:
                self.e.current.event({'type':'receive','node':'D','seq':p.seq,'bytes':len(p.payload),'hops':p.hops})
            self.transport.sendto(p.ack().encode(),addr)
        except ValueError:
            if self.e.current: self.e.current.event({'type':'invalid','node':'D'})


class LocalRelay(asyncio.DatagramProtocol):
    def __init__(self, engine): self.e = engine; self.sources = {}
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, raw, addr):
        try:
            p = Packet.decode(raw)
            if p.kind == DATA:
                self.sources[(p.run,p.seq)] = addr
                if len(self.sources)>30000: self.sources.clear()
                if self.e.paused: return
                run = self.e.current
                if not run or run.id != p.run: return
                run.event({'type':'relay_receive','node':'R','seq':p.seq,'bytes':len(p.payload)})
                if self.e.drop_every and (p.seq+1)%self.e.drop_every==0:
                    run.event({'type':'drop_injected','node':'R','seq':p.seq}); return
                p.hops += 1
                self.transport.sendto(p.encode(),('127.0.0.1',39002))
                run.event({'type':'forward','node':'R','seq':p.seq,'processing_ms':0.0})
            elif p.kind == ACK and (p.run,p.seq) in self.sources:
                self.transport.sendto(raw,self.sources.pop((p.run,p.seq)))
        except ValueError: pass


class Engine:
    def __init__(self):
        self.current = None
        self.devices = {}
        self.controls = {}
        self.transports = []
        self.task = None
        self.paused = False
        self.drop_every = 0
        self.runs = {}

    async def open(self):
        loop = asyncio.get_running_loop()
        for port, factory in [(39001,lambda:SourceProtocol(self)),(39002,lambda:SinkProtocol(self)),
                              (39010,lambda:LocalRelay(self))]:
            t,p = await loop.create_datagram_endpoint(factory,local_addr=('0.0.0.0',port))
            self.transports.append(t)
            if port==39001: self.source=p

    def close(self):
        if self.task: self.task.cancel()
        for t in self.transports: t.close()
        for run in self.runs.values():
            run.close()
            run.log.close()

    def endpoint(self, device_id):
        d = self.devices.get(device_id)
        if not d or time.time()-d.get('last_seen',0)>8 or 'endpoint' not in d:
            raise ValueError('Device offline or UDP HELLO not received')
        return tuple(d['endpoint'])

    async def start(self, config):
        if self.task and not self.task.done(): raise ValueError('Run already active')
        route, relay_id, dest_id = config['route'], config['relay_id'], config['destination_id']
        local = config['environment']=='local'
        if not local:
            if relay_id == dest_id and dest_id!='laptop': raise ValueError('Relay and destination must differ')
            if dest_id!='laptop' and self.devices.get(dest_id,{}).get('role')!='sink':
                raise ValueError('Destination must be a sink node')
            if route=='relay' and self.devices.get(relay_id,{}).get('role')!='relay':
                raise ValueError('Selected device is not a relay')
            dest = self.endpoint(dest_id) if dest_id!='laptop' else (config['laptop_ip'],39002)
            target = self.endpoint(relay_id) if route=='relay' else dest
            if route=='relay':
                # Device-to-device on same WLAN: use sink's local address/listen port.
                dd = self.devices.get(dest_id,{})
                peer = (dd.get('local_ip',dest[0]),dd.get('listen_port',dest[1])) if dest_id!='laptop' else dest
                old = self.controls.get(relay_id,{})
                self.controls[relay_id] = {'version':old.get('version',0)+1,'target_ip':peer[0],
                    'target_port':peer[1],'paused':False}
                version = self.controls[relay_id]['version']
                deadline = time.monotonic()+6
                while self.devices[relay_id].get('control_version') != version:
                    if time.monotonic()>deadline: raise ValueError('Relay did not acknowledge target configuration')
                    await asyncio.sleep(.1)
            topology = 'LAN UDP via physical Android relay' if route=='relay' else 'LAN UDP application-direct'
            if dest_id=='laptop': topology += '; laptop holds S and D (two-device pilot)'
        else:
            target = ('127.0.0.1',39010 if route=='relay' else 39002)
            topology = 'LOOPBACK software nodes; not physical device evidence'
        if self.current:
            self.current.save()
        if len(self.runs)>=20:
            oldest = next(iter(self.runs))
            self.runs.pop(oldest).log.close()
        run_id = int(time.time()*1000)%0x7fffffff
        self.current = Run(run_id,config,topology)
        self.runs[run_id] = self.current
        self.paused=False; self.drop_every=config.get('drop_every',0) if local else 0
        self.task = asyncio.create_task(self.send_loop(target))
        return self.current.snapshot()

    async def send_loop(self,target):
        run = self.current
        count = round(run.config['duration']*run.config['rate'])
        interval = 1/run.config['rate']
        start = time.perf_counter()
        try:
            for seq in range(count):
                await asyncio.sleep(max(0,start+seq*interval-time.perf_counter()))
                stamp = time.perf_counter_ns()
                packet = Packet(DATA,run.id,seq,stamp,payload_for(run.id,seq,run.config['payload']))
                run.sent[seq] = stamp
                self.source.transport.sendto(packet.encode(),target)
                run.event({'type':'send','node':'S','seq':seq,'bytes':len(packet.payload)})
            await asyncio.sleep(max(0,start+run.config['duration']-time.perf_counter())+2)
        except asyncio.CancelledError:
            run.event({'type':'stopped','node':'S'})
        finally:
            run.close()


def lan_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.2.1',80)); return s.getsockname()[0]
    finally: s.close()

