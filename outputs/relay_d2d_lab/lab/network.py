"""UDP data plane and ordered, idempotent run controls for PC/Android/ESP32."""
import asyncio
import json
import socket
import time
from .packet import Packet, DATA, ACK, HELLO, payload_for
from .records import Run, RESULTS
from .devices import register, endpoint, control_update


class SourceProtocol(asyncio.DatagramProtocol):
    def __init__(self, engine): self.e = engine
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, raw, addr):
        try:
            p = Packet.decode(raw)
            if p.kind == HELLO:
                register(self.e.devices, json.loads(p.payload.decode()), addr)
                return
            run = self.e.current
            if p.kind != ACK or not run or p.run != run.id or p.seq not in run.sent:
                return
            if run.config.get('source_id', 'laptop') != 'laptop': return
            if self.e.expected_ack and addr != self.e.expected_ack: return
            if p.sent_ns != run.sent[p.seq] or p.seq in run.acked: return
            run.acked.add(p.seq)
            rtt = (time.perf_counter_ns() - p.sent_ns) / 1e6
            run.rtts.append(rtt)
            run.event({'type': 'ack', 'node': 'S', 'seq': p.seq, 'sent_ns': p.sent_ns, 'hops': p.hops, 'rtt_ms': rtt})
        except (ValueError, KeyError, TypeError, UnicodeError):
            pass


class SinkProtocol(asyncio.DatagramProtocol):
    def __init__(self, engine): self.e = engine
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, raw, addr):
        try:
            p = Packet.decode(raw)
            if p.kind != DATA: return
            if p.payload != payload_for(p.run, p.seq, len(p.payload)):
                raise ValueError('Unexpected payload')
            if self.e.current and self.e.current.id == p.run:
                self.e.current.event({'type': 'receive', 'node': 'D', 'seq': p.seq,
                                      'bytes': len(p.payload), 'sent_ns': p.sent_ns, 'hops': p.hops})
            self.transport.sendto(p.ack().encode(), addr)
        except ValueError:
            if self.e.current: self.e.current.event({'type': 'invalid', 'node': 'D'})


class LocalRelay(asyncio.DatagramProtocol):
    def __init__(self, engine): self.e = engine; self.sources = {}
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, raw, addr):
        try:
            p = Packet.decode(raw)
            run = self.e.current
            if not run or p.run != run.id: return
            if p.kind == DATA:
                if p.hops >= 1 or p.payload != payload_for(p.run, p.seq, len(p.payload)):
                    raise ValueError('Invalid relay payload/hops')
                run.event({'type': 'relay_receive', 'node': 'R', 'seq': p.seq, 'bytes': len(p.payload)})
                if self.e.paused:
                    run.event({'type': 'drop_paused', 'node': 'R', 'seq': p.seq}); return
                if self.e.drop_every and (p.seq + 1) % self.e.drop_every == 0:
                    run.event({'type': 'drop_injected', 'node': 'R', 'seq': p.seq}); return
                self.sources[(p.run, p.seq)] = (addr, p.sent_ns)
                if len(self.sources) > 24000: self.sources.clear()
                p.hops += 1
                self.transport.sendto(p.encode(), self.e.local_sink)
                run.event({'type': 'forward', 'node': 'R', 'seq': p.seq, 'processing_ms': 0.0})
            elif p.kind == ACK and addr == self.e.local_sink:
                origin = self.sources.get((p.run, p.seq))
                if origin and origin[1] == p.sent_ns:
                    self.sources.pop((p.run, p.seq))
                    self.transport.sendto(raw, origin[0])
        except ValueError:
            if self.e.current: self.e.current.event({'type': 'invalid', 'node': 'R'})


class Engine:
    def __init__(self):
        self.current = None
        self.devices, self.controls, self.runs = {}, {}, {}
        self.transports = []
        self.task = None
        self.paused = False
        self.drop_every = 0
        self.expected_ack = None
        self.local_sink = ('127.0.0.1', 39002)

    async def open(self, practice=False):
        loop = asyncio.get_running_loop()
        for port, factory in [(39001, lambda: SourceProtocol(self)), (39002, lambda: SinkProtocol(self)),
                              (39010, lambda: LocalRelay(self))]:
            addr = ('127.0.0.1', 0) if practice else ('0.0.0.0', port)
            transport, protocol = await loop.create_datagram_endpoint(factory, local_addr=addr)
            if port == 39002: self.local_sink = ('127.0.0.1', transport.get_extra_info('sockname')[1])
            if port == 39010: self.local_relay = ('127.0.0.1', transport.get_extra_info('sockname')[1])
            self.transports.append(transport)
            if port == 39001: self.source = protocol

    def close(self):
        if self.task: self.task.cancel()
        for transport in self.transports: transport.close()
        for run in self.runs.values(): run.close(); run.log.close()

    def endpoint(self, key): return endpoint(self.devices, key)

    async def configure(self, key, **changes):
        version = control_update(self, key, **changes)
        deadline = time.monotonic() + 8
        while self.devices.get(key, {}).get('control_version') != version:
            if time.monotonic() > deadline: raise ValueError('Thiết bị chưa xác nhận cấu hình: ' + key)
            await asyncio.sleep(.08)

    async def start(self, config):
        if self.task and not self.task.done(): raise ValueError('Run already active')
        config = dict(config)
        source_id = config.setdefault('source_id', 'laptop')
        route, relay_id, dest_id = config['route'], config['relay_id'], config['destination_id']
        local = config['environment'] == 'local'
        if not local:
            if source_id == dest_id == 'laptop' and route == 'direct':
                raise ValueError('Laptop tự gửi cho laptop là LOOPBACK; chọn môi trường LOOPBACK hoặc một đích Android')
            active = [source_id, dest_id] + ([relay_id] if route == 'relay' else [])
            actual = [x for x in active if x != 'laptop']
            if len(actual) != len(set(actual)): raise ValueError('Nguồn, relay và đích phải là các thiết bị khác nhau')
            for key, role in [(source_id, 'source'), (dest_id, 'sink')] + ([(relay_id, 'relay')] if route == 'relay' else []):
                if key != 'laptop':
                    self.endpoint(key)
                    if self.devices[key].get('role') != role: raise ValueError('Vai trò thiết bị không đúng: ' + role)
            dd = self.devices.get(dest_id, {})
            relay = self.devices.get(relay_id, {}) if route == 'relay' else {}
            if route == 'relay' and (relay.get('platform') != 'esp32' or config.get('relay_kind') not in (None, '', 'esp32')):
                raise ValueError('Trạm chuyển tiếp phải là ESP32.')
            source_bridge = self.devices.get(source_id, {}).get('bridge_id')
            if source_bridge and (relay_id != source_bridge or relay.get('platform') != 'esp32'):
                raise ValueError('Nguồn đang nối RelayBox. Chọn ESP32 đang phát mạng này.')
            if source_bridge and dd.get('bridge_id'):
                raise ValueError('Đặt một đầu ở Wi-Fi router và đầu kia ở RelayBox.')
            if route == 'relay' and self.devices.get(relay_id, {}).get('platform') == 'esp32' and config['rate'] > 50:
                raise ValueError('RelayBox bản 2 giới hạn thí nghiệm ở 50 gói/giây để bảo toàn telemetry')
            if dd.get('bridge_id') and (route != 'relay' or relay_id != dd['bridge_id']):
                raise ValueError('Đích ở SoftAP ESP32: chọn đúng ESP32 relay; muốn Direct hãy chuyển đích sang Wi-Fi router')
            dest = self.endpoint(dest_id) if dest_id != 'laptop' else (config['laptop_ip'], self.local_sink[1])
            target = self.endpoint(relay_id) if route == 'relay' else dest
            if route == 'relay':
                peer = (dd.get('local_ip', dest[0]), dd.get('listen_port', dest[1])) if dest_id != 'laptop' else dest
                await self.configure(relay_id, target_ip=peer[0], target_port=peer[1], paused=False,
                                     drop_every=config.get('drop_every', 0), action='idle')
            if source_id != 'laptop':
                td = self.devices.get(relay_id if route == 'relay' else dest_id, {})
                if td and not td.get('bridge_id'):
                    target = (td.get('local_ip', target[0]), td.get('listen_port', target[1]))
            if source_bridge:
                target = (relay['ap_ip'], relay['listen_port'])
            topology = 'LAN UDP via esp32 packet relay' if route == 'relay' else 'LAN UDP application-direct'
            if dd.get('bridge_id'): topology += '; sink on ESP32 SoftAP, control HTTP proxied'
            if source_bridge: topology += '; source on ESP32 SoftAP, control HTTP proxied'
            if source_id == dest_id == 'laptop': topology += '; laptop holds S and D (pilot)'
        else:
            config.update(source_id='laptop', destination_id='laptop', relay_id='local')
            target = self.local_relay if route == 'relay' else self.local_sink
            topology = 'LOOPBACK software nodes; not physical device evidence'
        if self.current: self.current.save()
        if len(self.runs) >= 20:
            self.runs.pop(next(iter(self.runs))).log.close()
        run_id = int(time.time() * 1000) % 0x7fffffff
        while run_id in self.runs or (RESULTS / f'run_{run_id}').exists(): run_id += 1
        run = Run(run_id, config, topology)
        self.current = run; self.runs[run_id] = run
        self.paused = False; self.drop_every = config.get('drop_every', 0)
        self.expected_ack = target
        if config['source_id'] == 'laptop':
            self.task = asyncio.create_task(self.send_loop(target, run))
        else:
            try:
                await self.configure(source_id, action='start', run_id=run_id, target_ip=target[0], target_port=target[1],
                                     duration=config['duration'], rate=config['rate'], payload=config['payload'],
                                     corrupt_every=config.get('corrupt_every', 0))
            except Exception:
                control_update(self, source_id, action='stop', run_id=run_id)
                run.stop_reason = 'source_control_timeout'; run.close()
                raise
            self.task = asyncio.create_task(self.monitor_external(run))
        return run.snapshot()

    async def monitor_external(self, run):
        deadline = time.monotonic() + run.config['duration'] + 12
        try:
            while time.monotonic() < deadline:
                if run.source_done and time.monotonic() - run.source_finished_at > 2: break
                await asyncio.sleep(.15)
            if not run.source_done: run.stop_reason = 'source_telemetry_timeout'
        except asyncio.CancelledError:
            run.stop_reason = 'operator_stop'
        finally:
            control_update(self, run.config['source_id'], action='stop', run_id=run.id)
            run.close()

    async def send_loop(self, target, run):
        count = round(run.config['duration'] * run.config['rate'])
        start = time.perf_counter(); interval = 1 / run.config['rate']
        try:
            for seq in range(count):
                await asyncio.sleep(max(0, start + seq * interval - time.perf_counter()))
                stamp = time.perf_counter_ns()
                packet = Packet(DATA, run.id, seq, stamp, payload_for(run.id, seq, run.config['payload']))
                raw = packet.encode()
                corrupt = run.config.get('corrupt_every', 0)
                if corrupt and (seq + 1) % corrupt == 0:
                    raw = raw[:-1] + bytes([raw[-1] ^ 1])
                self.source.transport.sendto(raw, target)
                run.sent[seq] = stamp
                run.event({'type': 'send', 'node': 'S', 'seq': seq, 'bytes': len(packet.payload),
                           'sent_ns': stamp, 'hops': packet.hops,
                           'corrupted_deliberately': bool(corrupt and (seq + 1) % corrupt == 0)})
            run.source_done = True
            run.source_elapsed = time.perf_counter() - start
            await asyncio.sleep(max(0, start + run.config['duration'] - time.perf_counter()) + 2)
        except asyncio.CancelledError:
            run.stop_reason = 'operator_stop'
            run.event({'type': 'stopped', 'node': 'S'})
        finally:
            run.close()


def lan_ip():
    from .settings import selected_address
    return selected_address()[0]
