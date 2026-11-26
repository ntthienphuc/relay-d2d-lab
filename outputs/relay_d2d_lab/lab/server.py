import asyncio
import os
import json
import time
from contextlib import asynccontextmanager
from dataclasses import fields
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .network import Engine
from .records import ROOT, RESULTS
from .devices import register
from . import settings
from sim.model import Config, evaluate

engine = Engine()
simulation = None
sim_lock = asyncio.Lock()
run_lock = asyncio.Lock()


def relay_peer():
    """Use the interface receiving the board's UDP HELLO on multi-NIC laptops."""
    peers = {d['endpoint'][0] for d in engine.devices.values()
             if d.get('platform') == 'esp32' and d.get('endpoint')
             and time.time() - d.get('last_seen', 0) < 8}
    return next(iter(peers)) if len(peers) == 1 else None


def lan_ip():
    return settings.selected_address(relay_peer())[0]


@asynccontextmanager
async def lifespan(app):
    global simulation
    await engine.open(practice=os.getenv('RELAY_LAB_PRACTICE') == '1')
    simulation = await asyncio.to_thread(evaluate,Config(samples=100000))
    yield
    engine.close()


app = FastAPI(title='Relay Lab — local research demo',lifespan=lifespan)


class RunRequest(BaseModel):
    environment: str = 'local'
    route: str = 'relay'
    duration: float = Field(default=10,ge=1,le=120)
    rate: int = Field(default=20,ge=1,le=200)
    payload: int = Field(default=128,ge=16,le=1024)
    relay_id: str = 'local'
    relay_kind: Literal['','esp32'] = ''
    source_id: str = 'laptop'
    destination_id: str = 'laptop'
    laptop_ip: str = '127.0.0.1'
    drop_every: int = Field(default=0,ge=0,le=100)
    corrupt_every: int = Field(default=0,ge=0,le=100)
    experiment_label: str = Field(default='',max_length=120)
    study_id: str = Field(default='',max_length=80)
    location: str = Field(default='bench',max_length=80)
    block: int = Field(default=0,ge=0,le=999)
    ap_kind: str = Field(default='router',max_length=24)
    ap_ssid: str = Field(default='',max_length=64)
    placement: str = Field(default='',max_length=240)
    condition: str = Field(default='natural',max_length=40)


@app.get('/api/status')
async def status():
    devices = [dict(v,id=k,online=time.time()-v.get('last_seen',0)<8) for k,v in engine.devices.items()]
    return {'server_ip':lan_ip(),'http_port':8877 if os.getenv('RELAY_LAB_PRACTICE') == '1' else 8765,
        'udp_source_port':engine.source.transport.get_extra_info('sockname')[1],
        'udp_sink_port':engine.local_sink[1],
        'devices':devices,'run':engine.current.snapshot() if engine.current else None,
        'paused':engine.paused,'practice':os.getenv('RELAY_LAB_PRACTICE') == '1','version':'2.7.0','network':settings.snapshot(relay_peer()),'notice':'LAN/ESP32 SoftAP packet relay. AF/DF PHY is simulated; no RF mesh claim.'}


@app.post('/api/network')
async def network_config(data:dict):
    if engine.current and not engine.current.finished: raise HTTPException(409,'Kết thúc phiên đo trước khi đổi IP quản lý')
    try: settings.select_address(data.get('server_ip',''))
    except (ValueError,OSError): raise HTTPException(400,'IP không thuộc laptop; chọn đúng interface mạng lab')
    return settings.snapshot()


@app.post('/api/run')
async def run(request:RunRequest):
    config=request.model_dump()
    if config['corrupt_every'] or config['drop_every']:
        config['condition']='injected'
    if config['environment'] not in ('local','live') or config['route'] not in ('direct','relay'):
        raise HTTPException(400,'Invalid environment or route')
    # No arbitrary external destination: peers must register on this lab first.
    if config['environment']=='live':
        if os.getenv('RELAY_LAB_PRACTICE') == '1': raise HTTPException(400,'Đây là phòng tập. Chọn Tập chạy trên laptop hoặc mở dashboard phần cứng.')
        config['laptop_ip']=lan_ip()
    if run_lock.locked(): raise HTTPException(409,'A run is being configured')
    async with run_lock:
        try: return await engine.start(config)
        except (ValueError,OSError) as ex: raise HTTPException(400,str(ex))


@app.post('/api/stop')
async def stop():
    if engine.task and not engine.task.done():
        engine.task.cancel()
        await engine.task
    return {'stopped':True}


@app.post('/api/pause-relay')
async def pause():
    if not engine.current or engine.current.finished or engine.current.config['route'] != 'relay':
        raise HTTPException(400,'Không có phiên relay để tạm dừng')
    engine.paused=not engine.paused
    if engine.current and engine.current.config['environment']=='live':
        key=engine.current.config['relay_id']
        control=engine.controls.setdefault(key,{})
        control.update(paused=engine.paused,version=control.get('version',0)+1)
    return {'paused':engine.paused}


@app.post('/api/device')
async def device(data:dict):
    try: register(engine.devices, data)
    except (ValueError,TypeError): raise HTTPException(400,'Invalid device identity')
    return engine.controls.get(data['id'],{})


@app.post('/api/events')
async def events(data:dict):
    entries=data.get('events',[])
    if not isinstance(entries,list) or len(entries)>500: raise HTTPException(400,'Invalid event batch')
    touched=set()
    accepted=0
    for e in entries:
        if not isinstance(e,dict): continue
        current=engine.runs.get(e.get('run'))
        if not current or e.get('node') not in ('S','R','D'): continue
        expected={'S':current.config.get('source_id','laptop'), 'R':current.config['relay_id'],
                  'D':current.config['destination_id']}[e['node']]
        if expected == 'laptop' or e.get('device_id')!=expected: continue
        if e.get('type')!='source_done':
            seq=e.get('seq')
            if not isinstance(seq,int) or not 0<=seq<round(current.config['duration']*current.config['rate']): continue
        try:
            if e['node']=='S': current.source_event(e)
            elif e.get('type') in ('receive','relay_receive','forward','ack_forward','invalid','drop_paused','drop_injected','drop_capacity'):
                current.event(e)
            else: continue
        except (KeyError,ValueError,TypeError): continue
        touched.add(current.id);accepted+=1
    for run_id in touched:
        if engine.runs[run_id].finished: engine.runs[run_id].save()
    return {'accepted':accepted}


@app.get('/api/preflight')
async def preflight():
    devices=[dict(d,online=time.time()-d.get('last_seen',0)<8) for d in engine.devices.values()]
    return {'version':'2.7.0','server_ip':lan_ip(),'devices':devices,
            'checks':{'android_apk':(ROOT/'android/build/relaylab.apk').exists(),
                      'esp32_firmware':(ROOT/'esp32/build/cam/RelayBox.ino.bin').exists(),
                      'local_udp':len(engine.transports)==3},
            'limits':['One radio on ESP32; AP and STA share a channel.',
                      'No automatic RF mesh, analog AF, SWIPT or NOMA hardware claim.',
                      'Source/relay/sink devices must be distinct, except explicit laptop pilot.']}


@app.get('/docs/THAO_TAC.html')
@app.get('/guide')
async def guide(): return FileResponse(ROOT/'Huong_dan_va_kich_ban_demo.pdf', media_type='application/pdf')


@app.get('/research')
async def research(): return FileResponse(ROOT/'research'/'PAPER_REVIEW.html')


@app.get('/api/simulation')
async def get_simulation(): return simulation


@app.post('/api/simulation')
async def simulate(data:dict):
    global simulation
    if sim_lock.locked(): raise HTTPException(409,'Simulation is running')
    allowed={f.name for f in fields(Config)}
    if any(k not in allowed for k in data): raise HTTPException(400,'Unknown parameter')
    async with sim_lock:
        try:
            c=Config(**data)
            simulation=await asyncio.to_thread(evaluate,c)
        except (ValueError,TypeError) as e: raise HTTPException(400,str(e))
        (RESULTS/'simulation_latest.json').write_text(json.dumps(simulation,indent=2),encoding='utf-8')
        return simulation


def supported_session(item):
    config = item['config']
    if config.get('environment') != 'live' or config.get('route') != 'relay':
        return True
    return config.get('relay_kind') == 'esp32' or str(config.get('relay_id', '')).startswith('esp32-')


@app.get('/api/history')
async def history(scope: str = 'all'):
    rows=[]
    reference = set(json.loads((RESULTS/'final/evidence_ids.json').read_text(encoding='utf-8')))
    if scope not in ('all','new','evidence'):
        raise HTTPException(400, 'Unknown history scope')
    for path in RESULTS.glob('run_*/summary.json'):
        archived = int(path.parent.name[4:]) in reference
        if (scope == 'new' and archived) or (scope == 'evidence' and not archived): continue
        try:
            item=json.loads(path.read_text(encoding='utf-8'))
            if item['config']['environment']!='test' and supported_session(item):rows.append(item)
        except (ValueError,OSError): pass
    return sorted(rows, key=lambda row: row.get('started_wall', (RESULTS/f"run_{row['id']}"/'config.json').stat().st_mtime), reverse=True)[:40]


@app.get('/api/replay/{run_id}')
async def replay(run_id:int):
    folder=RESULTS/f'run_{run_id}'
    if not (folder/'summary.json').exists(): raise HTTPException(404,'Run not found')
    summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    if not supported_session(summary): raise HTTPException(404,'Phiên thuộc cấu hình đã ngừng sử dụng.')
    log=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    return {'summary':summary,'events':log}


@app.get('/download/android')
async def apk():
    path=ROOT/'android'/'build'/'relaylab.apk'
    if not path.exists(): raise HTTPException(404,'APK not built')
    return FileResponse(path,filename='RelayLab.apk',media_type='application/vnd.android.package-archive')


@app.get('/api/trace/{run_id}')
async def trace(run_id:int,filter:str='all'):
    if filter not in ('all','missing','ack'):raise HTTPException(400,'Invalid trace filter')
    def response(packets,finished):
        rows=[packets[k] for k in sorted(packets,reverse=True)]
        if filter=='ack':rows=[p for p in rows if p.get('ack')]
        if filter=='missing':rows=[p for p in rows if not p.get('ack') or any(e['type']=='invalid' or e['type'].startswith('drop') for e in p['events'])]
        return {'id':run_id,'finished':finished,'total':len(packets),'matching':len(rows),'packets':rows[:120]}
    run=engine.runs.get(run_id)
    if run:
        return response(run.traces,run.finished)
    path=RESULTS/f'run_{run_id}'/'events.jsonl'
    summary = path.with_name('summary.json')
    if summary.is_file() and not supported_session(json.loads(summary.read_text(encoding='utf-8'))):
        raise HTTPException(404,'Phiên thuộc cấu hình đã ngừng sử dụng.')
    if not path.exists():raise HTTPException(404,'Run not found')
    packets={}
    for line in path.read_text(encoding='utf-8').splitlines():
        e=json.loads(line);seq=e.get('seq')
        if not isinstance(seq,int) or seq < 0:continue
        p=packets.setdefault(seq,{'seq':seq,'bytes':0,'events':[]})
        p['events'].append(e);p['events']=p['events'][-12:];p[e['type']]=True
        if e.get('bytes',0):p['bytes']=e['bytes']
        if 'rtt_ms' in e:p['rtt_ms']=e['rtt_ms']
        if e.get('type') == 'forward' and 'processing_ms' in e:p['processing_ms']=e['processing_ms']
    return response(packets,True)


@app.get('/')
async def index(): return FileResponse(ROOT/'web'/'index.html')


app.mount('/src',StaticFiles(directory=ROOT/'web'/'src'),name='src')
app.mount('/vendor',StaticFiles(directory=ROOT/'web'/'vendor',check_dir=False),name='vendor')
app.mount('/results',StaticFiles(directory=RESULTS),name='results')
app.mount('/docs',StaticFiles(directory=ROOT/'docs'),name='docs')
app.mount('/research',StaticFiles(directory=ROOT/'research'),name='research_files')
