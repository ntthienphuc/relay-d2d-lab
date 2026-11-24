import asyncio
import json
import time
from contextlib import asynccontextmanager
from dataclasses import fields
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .network import Engine, lan_ip
from .records import ROOT, RESULTS
from sim.model import Config, evaluate

engine = Engine()
simulation = None
sim_lock = asyncio.Lock()
run_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    global simulation
    await engine.open()
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
    destination_id: str = 'laptop'
    laptop_ip: str = '127.0.0.1'
    drop_every: int = Field(default=0,ge=0,le=100)


@app.get('/api/status')
async def status():
    devices = [dict(v,id=k,online=time.time()-v.get('last_seen',0)<8) for k,v in engine.devices.items()]
    return {'server_ip':lan_ip(),'http_port':8765,'udp_source_port':39001,'udp_sink_port':39002,
        'devices':devices,'run':engine.current.snapshot() if engine.current else None,
        'paused':engine.paused,'version':'1.0.0','notice':'LAN data plane via AP. Packet relay is not analog AF or RF full-duplex.'}


@app.post('/api/run')
async def run(request:RunRequest):
    config=request.model_dump()
    if config['environment'] not in ('local','live') or config['route'] not in ('direct','relay'):
        raise HTTPException(400,'Invalid environment or route')
    # No arbitrary external destination: peers must register on this lab first.
    if config['environment']=='live': config['laptop_ip']=lan_ip()
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
    engine.paused=not engine.paused
    if engine.current and engine.current.config['environment']=='live':
        key=engine.current.config['relay_id']
        control=engine.controls.setdefault(key,{})
        control.update(paused=engine.paused,version=control.get('version',0)+1)
    return {'paused':engine.paused}


@app.post('/api/device')
async def device(data:dict):
    if not isinstance(data.get('id'),str) or len(data['id'])>100: raise HTTPException(400,'Invalid device id')
    old=engine.devices.setdefault(data['id'],{})
    allowed=('model','role','local_ip','listen_port','pending_events','running','version','control_version')
    old.update({k:data[k] for k in allowed if k in data})
    old['http_seen']=time.time()
    return engine.controls.get(data['id'],{})


@app.post('/api/events')
async def events(data:dict):
    entries=data.get('events',[])
    if len(entries)>500: raise HTTPException(400,'Batch too large')
    touched=set()
    for e in entries:
        current=engine.runs.get(e.get('run'))
        if current and e.get('seq',-1) in current.sent:
            if e.get('node') not in ('R','D'): continue
            expected=current.config['relay_id'] if e['node']=='R' else current.config['destination_id']
            if e.get('device_id')!=expected: continue
            current.event(e);touched.add(current.id)
    for run_id in touched:
        if engine.runs[run_id].finished: engine.runs[run_id].save()
    return {'accepted':len(entries)}


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


@app.get('/api/history')
async def history():
    rows=[]
    for path in sorted(RESULTS.glob('run_*/summary.json'),reverse=True)[:40]:
        try:
            item=json.loads(path.read_text(encoding='utf-8'))
            if item['config']['environment']!='test':rows.append(item)
        except (ValueError,OSError): pass
    return rows


@app.get('/api/replay/{run_id}')
async def replay(run_id:int):
    folder=RESULTS/f'run_{run_id}'
    if not (folder/'summary.json').exists(): raise HTTPException(404,'Run not found')
    summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
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
        if filter=='missing':rows=[p for p in rows if not(p.get('ack') or p.get('receive')) or p.get('drop_paused') or p.get('drop_injected')]
        return {'id':run_id,'finished':finished,'total':len(packets),'matching':len(rows),'packets':rows[:120]}
    run=engine.runs.get(run_id)
    if run:
        return response(run.traces,run.finished)
    path=RESULTS/f'run_{run_id}'/'events.jsonl'
    if not path.exists():raise HTTPException(404,'Run not found')
    packets={}
    for line in path.read_text(encoding='utf-8').splitlines():
        e=json.loads(line);seq=e.get('seq')
        if not isinstance(seq,int):continue
        p=packets.setdefault(seq,{'seq':seq,'bytes':0,'events':[]})
        p['events'].append(e);p['events']=p['events'][-12:];p[e['type']]=True
        if e.get('bytes',0):p['bytes']=e['bytes']
        if 'rtt_ms' in e:p['rtt_ms']=e['rtt_ms']
        if 'processing_ms' in e:p['processing_ms']=e['processing_ms']
    return response(packets,True)


@app.get('/')
async def index(): return FileResponse(ROOT/'web'/'index.html')


app.mount('/src',StaticFiles(directory=ROOT/'web'/'src'),name='src')
app.mount('/vendor',StaticFiles(directory=ROOT/'web'/'vendor',check_dir=False),name='vendor')
app.mount('/results',StaticFiles(directory=RESULTS),name='results')
