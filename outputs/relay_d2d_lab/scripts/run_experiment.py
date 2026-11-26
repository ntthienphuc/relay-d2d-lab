"""Repeat real measurements in randomised route order and preserve every result."""
import argparse
import csv
import json
import random
import time
import urllib.request
from pathlib import Path
from analyze_sessions import summarize

parser=argparse.ArgumentParser()
parser.add_argument('--source',default='laptop');parser.add_argument('--relay',required=True)
parser.add_argument('--destination',default='laptop');parser.add_argument('--repeats',type=int,default=5)
parser.add_argument('--duration',type=int,default=60);parser.add_argument('--rate',type=int,default=20)
parser.add_argument('--payload',type=int,default=128);parser.add_argument('--label',default='bench')
parser.add_argument('--routes',nargs='+',choices=['direct','relay'],default=['direct','relay'])
parser.add_argument('--seed',type=int,default=20261125)
parser.add_argument('--ssid',default='')
parser.add_argument('--location',default='bench')
parser.add_argument('--placement',default='')
parser.add_argument('--study-id',default='')
args=parser.parse_args()
if not 1<=args.repeats<=30:parser.error('repeats must be 1..30')
def api(path,data=None):
    req=urllib.request.Request('http://127.0.0.1:8765/api/'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
rng=random.Random(args.seed)
plan=[]
for repeat in range(1,args.repeats+1):
    routes=list(args.routes)
    rng.shuffle(routes)
    plan.extend((repeat,route) for route in routes)
out=Path(__file__).resolve().parents[1]/'results'/('experiment_'+time.strftime('%Y%m%d_%H%M%S'))
out.mkdir();(out/'plan.json').write_text(json.dumps({'config':vars(args),'order':plan},indent=2),encoding='utf-8')
results=[]
for repeat,route in plan:
    run=api('run',dict(environment='live',route=route,source_id=args.source,relay_id=args.relay,destination_id=args.destination,
                       duration=args.duration,rate=args.rate,payload=args.payload,study_id=args.study_id,block=repeat,
                       ap_ssid=args.ssid,location=args.location,placement=args.placement,experiment_label=f'{args.label} / {route} / {repeat}'))
    deadline=time.time()+args.duration+30
    while time.time()<deadline:
        time.sleep(.5);status=api('status')['run']
        if status['id']==run['id'] and status['finished']:break
    else:raise RuntimeError('Timed out; preserve existing logs and inspect the active run')
    time.sleep(1);result=api('replay/'+str(run['id']))['summary'];result['repeat']=repeat;results.append(result)
    (out/'results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    print(route,repeat,result['sent'],result['delivery_confirmed'],result['rtt_p95_ms'],flush=True)
columns=['route','repeat','run_id','sent','confirmed','pdr','rtt_p95_ms','goodput_kbps','complete_send']
with (out/'metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(columns)
    for r in results:writer.writerow([r['config']['route'],r['repeat'],r['id'],r['sent'],r['delivery_confirmed'],r['pdr_confirmed'],r['rtt_p95_ms'],r['goodput_kbps'],r['complete_send']])
(out/'session_statistics.json').write_text(json.dumps(summarize(results,args.seed),indent=2),encoding='utf-8')
print(out)
