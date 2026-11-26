"""Paired two-phone field pilot. ADB operates the sink's Wi-Fi settings only.

Both networks must already be saved on the sink. All DATA and ACK use Wi-Fi.
The result directory keeps every attempt and the route order even on failure.
"""
import argparse
import json
import random
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def api(path, body=None):
    request = urllib.request.Request("http://127.0.0.1:8765/api/" + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def wait_for(check, seconds, message):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(.5)
    raise RuntimeError(message)


def adb(serial, *args):
    return subprocess.check_output(["adb", "-s", serial, "shell", *args],
        encoding="utf-8", errors="replace", timeout=12)


def attached(serial, ssid):
    status=adb(serial,"cmd","wifi","status")
    return (f'SSID: "{ssid}"' in status and "Supplicant state: COMPLETED" in status
            and re.search(r"IP: /(?!0\.0\.0\.0)\d+\.\d+\.\d+\.\d+",status) is not None)


def change_network(serial, ssid):
    if attached(serial, ssid):
        return
    adb(serial, "am", "start", "-a", "android.settings.WIFI_SETTINGS")
    # The settings screen reorders access points after its initial scan.
    time.sleep(4)
    previous_bounds=None
    def tap_saved():
        nonlocal previous_bounds
        path = "/data/local/tmp/relay-wifi.xml"
        try:
            adb(serial, "uiautomator", "dump", path)
            screen = ET.fromstring(adb(serial, "cat", path))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ET.ParseError):
            return False
        for item in screen.iter("node"):
            if "không kết nối với Internet" in item.get("text",""):
                reject=next((n for n in screen.iter("node") if n.get("text")=="Từ chối"),None)
                if reject is not None:
                    x1,y1,x2,y2=map(int,re.findall(r"\d+",reject.get("bounds","")))
                    adb(serial,"input","tap",str((x1+x2)//2),str((y1+y2)//2))
                    previous_bounds=None
                    return False
        for item in screen.iter("node"):
            if item.get("text") == ssid:
                if item.get("bounds") != previous_bounds:
                    previous_bounds=item.get("bounds")
                    return False
                x1,y1,x2,y2 = map(int,re.findall(r"\d+", item.get("bounds","")))
                adb(serial,"input","tap",str((x1+x2)//2),str((y1+y2)//2))
                return True
        return False
    wait_for(tap_saved, 25, "Open Wi-Fi settings and select the saved network " + ssid)
    wait_for(lambda: attached(serial, ssid), 25, "Sink did not join " + ssid)


def nodes():
    return {d['id']:d for d in api("status")["devices"]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for option in ("source","sink","relay","sink-usb","upstream","softap"):
        p.add_argument("--"+option,required=True)
    p.add_argument("--blocks",type=int,default=5,choices=range(1,31))
    p.add_argument("--duration",type=int,default=10,choices=range(1,121))
    p.add_argument("--rate",type=int,default=10,choices=range(1,51))
    p.add_argument("--payload",type=int,default=128,choices=(128,512,1024))
    p.add_argument("--placement",required=True)
    p.add_argument("--seed",type=int,default=20261126)
    p.add_argument("--resume",type=Path,help="Continue the saved order after a setup interruption")
    args=p.parse_args()
    folder=args.resume if args.resume else ROOT/"results"/time.strftime("paired_%Y%m%d_%H%M%S")
    pairs=[]
    rng=random.Random(args.seed)
    for block in range(1,args.blocks+1):
        routes=["direct","relay"]
        rng.shuffle(routes)
        pairs.extend((block,route) for route in routes)
    public={k:v for k,v in vars(args).items() if k not in ("sink_usb","resume")}
    if args.resume:
        plan=json.loads((folder/"plan.json").read_text(encoding="utf-8"))
        if public!=plan["parameters"]: raise ValueError("Parameters differ from the saved plan")
        runs=json.loads((folder/"trials.json").read_text(encoding="utf-8"))
        if any("id" in t and "summary" not in t for t in runs):
            raise ValueError("Recover the existing run before continuing. A started run cannot be replaced.")
    else:
        folder.mkdir()
        save(folder/"plan.json",{"parameters":public,"order":pairs,"unit":"paired block",
            "settle_seconds":4,"route_change":"Switch sink Wi-Fi only. Source and relay stay upstream."})
        runs=[]
    active=api("status")
    host=active["server_ip"]
    if active["run"] and not active["run"]["finished"]:
        raise RuntimeError("Finish the current run before starting paired measurements.")
    for block,route in pairs:
        if any(t["block"]==block and t["route"]==route and "summary" in t for t in runs):continue
        trial={"block":block,"route":route}
        runs.append(trial)
        save(folder/"trials.json",runs)
        try:
            relay_path=route=="relay"
            ssid=args.softap if relay_path else args.upstream
            prior=nodes().get(args.sink,{}).get("session")
            change_network(args.sink_usb,ssid)
            time.sleep(2)
            adb(args.sink_usb,"am","force-stop","vn.relaylab")
            adb(args.sink_usb,"am","start","-W","-f","0x10008000",
                "-a","android.intent.action.MAIN","-c","android.intent.category.LAUNCHER","-n","vn.relaylab/.MainActivity","--es","server",
                "192.168.50.1" if relay_path else host,"--es","role","sink","--ez","auto","true")
            def ready():
                current=nodes()
                sink=current.get(args.sink,{})
                return (sink.get("online") and sink.get("session")!=prior and sink.get("bridge_id","")== (args.relay if relay_path else "")
                    and bool(sink.get("management_ok")) and current[args.source]["online"]
                    and (not relay_path or current[args.relay]["online"]))
            wait_for(ready,25,"Sink registration does not match planned route.")
            time.sleep(4)
            if not ready(): raise RuntimeError("Route changed during settling")
            trial["before"]=nodes()
            config=dict(environment="live",route=route,source_id=args.source,destination_id=args.sink,
                relay_id=args.relay,study_id=folder.name,block=block,ap_ssid=args.upstream,location="bench",
                placement=args.placement,experiment_label=f"Pair {block} · {route}",duration=args.duration,
                rate=args.rate,payload=args.payload)
            run=api("run",config)
            trial["id"]=run["id"]
            save(folder/"trials.json",runs)
            def done():
                r=api("status")["run"]
                return r["id"]==run["id"] and r["finished"]
            wait_for(done,args.duration+32,"Run did not finish")
            def drained():
                current=nodes()
                return all(current[k]["online"] and current[k].get("pending_events",0)==0
                    for k in ([args.source,args.sink,args.relay] if relay_path else [args.source,args.sink]))
            wait_for(drained,15,"Telemetry still pending after run")
            trial["after"]=nodes()
            trial["summary"]=api("replay/"+str(run["id"]))["summary"]
            print(block,route,run["id"],trial["summary"]["delivery_confirmed"],flush=True)
        except Exception as exc:
            trial["error"]=str(exc)
            raise
        finally:
            save(folder/"trials.json",runs)
    print(folder,flush=True)


if __name__=="__main__":
    main()
