import json
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
RESULTS.mkdir(exist_ok=True)


class Run:
    def __init__(self, run_id, config, topology):
        self.id, self.config, self.topology = run_id, config, topology
        self.started_wall = time.time()
        self.started = time.monotonic()
        self.finished = False
        self.sent = {}
        self.received, self.acked = set(), set()
        self.rtts, self.relay_delays = [], []
        self.duplicates = 0
        self.invalid = 0
        self.bytes_received = 0
        self.events = []
        self.traces = {}
        self.dropped = set()
        self.observed_events = set()
        self.folder = RESULTS / f'run_{run_id}'
        self.folder.mkdir(exist_ok=True)
        self.log = (self.folder/'events.jsonl').open('a',encoding='utf-8')
        (self.folder/'config.json').write_text(json.dumps({'id':run_id,'topology':topology,
            'started_wall': self.started_wall, **config},indent=2),encoding='utf-8')

    def event(self, item):
        event_id = item.get('event_id')
        if event_id and event_id in self.observed_events:
            return
        if event_id:
            self.observed_events.add(event_id)
        item = dict(item, server_time=time.time(), run=self.id)
        self.events.append(item)
        self.events = self.events[-400:]
        self.log.write(json.dumps(item,ensure_ascii=False)+'\n')
        self.log.flush()
        seq = item.get('seq')
        if isinstance(seq,int):
            trace=self.traces.setdefault(seq,{'seq':seq,'bytes':0,'events':[]})
            trace['events'].append(item)
            trace['events']=trace['events'][-12:]
            trace[item['type']]=True
            if item.get('bytes',0):trace['bytes']=item['bytes']
            if 'rtt_ms' in item:trace['rtt_ms']=item['rtt_ms']
            if 'processing_ms' in item:trace['processing_ms']=item['processing_ms']
            if item['type'].startswith('drop'):self.dropped.add(seq)
        if item.get('type') == 'receive' and item.get('node') == 'D':
            if seq in self.received:
                self.duplicates += 1
            else:
                self.received.add(seq)
                self.bytes_received += item.get('bytes',0)
        if item.get('type') == 'forward' and 'processing_ms' in item:
            self.relay_delays.append(item['processing_ms'])
        if item.get('type') == 'invalid':
            self.invalid += 1

    def snapshot(self):
        sent = len(self.sent)
        elapsed = min(time.monotonic()-self.started, self.config['duration'])
        confirmed = self.received | self.acked
        return {'id': self.id, 'config': self.config, 'topology': self.topology,
            'finished': self.finished, 'elapsed': round(elapsed,2), 'sent': sent,
            'received_observed': len(self.received), 'delivery_confirmed': len(confirmed),
            'acked': len(self.acked), 'pdr_observed': len(self.received)/sent if sent else None,
            'pdr_confirmed': len(confirmed)/sent if sent else None,
            'goodput_kbps': self.bytes_received*8/max(elapsed,.001)/1000,
            'rtt_ms': float(np.mean(self.rtts)) if self.rtts else None,
            'rtt_p95_ms': float(np.percentile(self.rtts,95)) if self.rtts else None,
            'relay_ms': float(np.mean(self.relay_delays)) if self.relay_delays else None,
            'duplicates': self.duplicates, 'invalid': self.invalid, 'dropped_by_relay':len(self.dropped),
            'source_clock':'time.perf_counter_ns (high resolution, monotonic, same source process)',
            'report_note': 'Receiver telemetry may be incomplete; confirmed = union of sink receipts and valid ACK. RTT only acknowledged packets. Goodput includes drain-period receipts divided by configured send window.',
            'events': self.events[-100:]}

    def save(self):
        data = self.snapshot()
        data.pop('events',None)
        (self.folder/'summary.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')

    def close(self):
        self.finished = True
        self.save()
        # Keep log open for late reliable telemetry until next run or shutdown.
