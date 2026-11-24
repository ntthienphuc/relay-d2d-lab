"""Exercise the connected authorized Android. Only manages vn.relaylab."""
import json
import pathlib
import subprocess
import time
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8765'

def api(path,data=None):
    payload=None if data is None else json.dumps(data).encode()
    request=urllib.request.Request(BASE+'/api/'+path,data=payload,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=20) as r:return json.load(r)

def adb(*args):return subprocess.check_output(['adb',*args],text=True,encoding='utf-8').strip()

def activate(role):
    adb('shell','am','force-stop','vn.relaylab')
    host=api('status')['server_ip']
    adb('shell','am','start','-n','vn.relaylab/.MainActivity','--es','server',host,'--es','role',role,'--ez','auto','true')
    deadline=time.time()+15
    while time.time()<deadline:
        for d in api('status')['devices']:
            if d.get('online') and d.get('role')==role and time.time()-d['last_seen']<2:
                return d['id']
        time.sleep(.5)
    raise RuntimeError('Android registration failed: '+role)

def wait_run(run_id):
    deadline=time.time()+80
    while time.time()<deadline:
        r=api('status')['run']
        if r and r['id']==run_id and r['finished']:
            time.sleep(1.5)
            r=api('replay/'+str(run_id))['summary'];return r
        time.sleep(.5)
    raise RuntimeError('Run timeout')

results=[]
device=activate('relay')
r=api('run',{'environment':'live','route':'relay','duration':50,'rate':20,'payload':128,'relay_id':device,'destination_id':'laptop'})
results.append(wait_run(r['id']))
assert results[-1]['sent']==1000 and results[-1]['delivery_confirmed']>0,'Run incomplete or no data forwarded'
print('relay_1000',results[-1]['sent'],results[-1]['delivery_confirmed'],flush=True)
r=api('run',{'environment':'live','route':'relay','duration':12,'rate':20,'payload':128,'relay_id':device,'destination_id':'laptop'})
time.sleep(3);api('pause-relay',{});time.sleep(3);api('pause-relay',{})
results.append(wait_run(r['id']))
assert 0<results[-1]['delivery_confirmed']<results[-1]['sent'],'Pause did not interrupt delivery'
print('relay_pause',results[-1]['sent'],results[-1]['delivery_confirmed'],flush=True)
device=activate('sink')
r=api('run',{'environment':'live','route':'direct','duration':10,'rate':20,'payload':512,'relay_id':'','destination_id':device})
results.append(wait_run(r['id']))
assert results[-1]['delivery_confirmed']>0 and results[-1]['received_observed']>0,'Android sink did not report reception'
print('android_sink',results[-1]['sent'],results[-1]['received_observed'],flush=True)
activate('relay')
raw=subprocess.check_output(['adb','exec-out','run-as','vn.relaylab','cat','files/events.jsonl'])
(ROOT/'results'/'android_events.jsonl').write_bytes(raw)
receipt={'scope':'One physical SM-G965F; second physical Android not tested. UDP over Wi-Fi/LAN; no USB data tunnel.',
         'cases':results,'date':time.strftime('%Y-%m-%d'),'checks':'Positive receipt; pause causes missing packets; Android sink reports receive. Raw counts preserved, no forced PDR threshold.'}
(ROOT/'results'/'hardware_smoke.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
