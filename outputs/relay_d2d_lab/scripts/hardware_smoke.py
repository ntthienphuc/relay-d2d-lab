from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description="Đo hai chiều qua một ESP32 với điện thoại đang nối RelayBox")
parser.add_argument("--serial",required=True)
args=parser.parse_args()
import httpx as requests,subprocess,time,json,sys
url='http://127.0.0.1:8765'
adb=['adb','-s',args.serial]
def status():return requests.get(url+'/api/status',timeout=5).json()
def wait_for(test,seconds=15):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        value=test(status())
        if value:return value
        time.sleep(.3)
    raise RuntimeError('Device or run did not become ready')
current=status()
assert not current.get('run') or current['run']['finished']
board=wait_for(lambda snap:next((n for n in snap['devices'] if n['platform']=='esp32' and n['online']),None))
result=[];version=current['version']
for role in ['sink','source']:
    subprocess.run(adb+['shell','am','start','-S','-n','vn.relaylab/.MainActivity','--es','server','192.168.50.1','--es','role',role,'--ez','auto','true'],check=True,stdout=subprocess.DEVNULL)
    phone=wait_for(lambda snap:next((n for n in snap['devices'] if n['platform']=='android' and n['role']==role and n['online'] and n.get('bridge_id')==board['id']),None),30)
    ask=dict(environment='live',route='relay',relay_kind='esp32',duration=4,rate=10,payload=128,relay_id=board['id'],source_id=phone['id'] if role=='source' else 'laptop',destination_id=phone['id'] if role=='sink' else 'laptop',experiment_label='Hai đầu và một ESP32 · '+role)
    rsp=requests.post(url+'/api/run',json=ask,timeout=18);rsp.raise_for_status();rid=rsp.json()['id']
    row=wait_for(lambda snap:snap['run'] if snap.get('run') and snap['run']['id']==rid and snap['run']['finished'] else None,30)
    assert row['sent']==40 and row['received_observed']>0 and row['acked']>0,row['id']
    result.append({k:row[k] for k in ['id','sent','received_observed','acked','rtt_p95_ms','goodput_kbps','config']})
    print(role,rid,row['sent'],row['received_observed'],row['acked'],flush=True)
print(json.dumps(dict(pc=version,android=phone['version'],esp=board['version'],runs=result),ensure_ascii=False,indent=2))
