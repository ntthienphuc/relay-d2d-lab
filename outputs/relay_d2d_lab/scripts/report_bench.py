"""Rebuild the bench receipt from the original packet events and paired run plan."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LAB=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(trial, folder, ids):
    run_dir=folder.parent/f"run_{trial['id']}"
    summary=read(run_dir/"summary.json")
    events=[json.loads(line) for line in (run_dir/"events.jsonl").read_text(encoding="utf-8").splitlines()]
    c=summary["config"]
    relay=c["route"]=="relay"
    hops=int(relay)
    assert c["source_id"]==ids["source"] and c["destination_id"]==ids["sink"]
    assert c["block"]==trial["block"] and c["study_id"]==folder.name and c["route"]==trial["route"]
    assert summary["source_done"] and summary["complete_send"] and not summary["stop_reason"]
    assert trial["before"][ids["sink"]].get("bridge_id","")== (ids["relay"] if relay else "")
    for key in (["source","relay","sink"] if relay else ["source","sink"]):
        a,b=trial["before"][ids[key]],trial["after"][ids[key]]
        assert a["session"]==b["session"] and a["queue_lost"]==b["queue_lost"] and b["pending_events"]==0
    role_ids={"S":ids["source"],"D":ids["sink"],"R":ids["relay"]}
    seen={}
    for e in events:
        assert e["device_id"]==role_ids[e["node"]]
        if e["type"]=="source_done":continue
        if e["type"] in ("receive","ack","forward","ack_forward"):
            assert e["hops"]==hops
        seen.setdefault(e["type"],set()).add((e["seq"],e["sent_ns"]))
    sent=seen["send"]
    assert all(e["run"] == trial["id"] for e in events)
    ack_rtts = {}
    receive_sizes = {}
    for e in events:
        key = (e.get("seq"), e.get("sent_ns"))
        if e["type"] == "ack" and e["node"] == "S":
            value = e["rtt_ms"]
            assert np.isfinite(value) and value >= 0
            assert key not in ack_rtts or ack_rtts[key] == value
            ack_rtts[key] = value
        elif e["type"] == "receive" and e["node"] == "D":
            assert e["bytes"] == c["payload"]
            receive_sizes[key] = e["bytes"]
    assert len(sent) == round(c["rate"] * c["duration"])
    assert set(ack_rtts) <= sent and set(receive_sizes) <= sent
    p95 = float(np.percentile(list(ack_rtts.values()), 95)) if ack_rtts else None
    goodput = sum(receive_sizes.values()) * 8 / (1000 * c["duration"])
    assert (p95 is None and summary["rtt_p95_ms"] is None) or np.isclose(p95, summary["rtt_p95_ms"], rtol=0, atol=1e-9)
    assert np.isclose(goodput, summary["goodput_kbps"], rtol=0, atol=1e-9)
    received=seen.get("receive",set())
    acked=seen.get("ack",set())
    assert received<=sent and acked<=sent
    if relay:
        assert received<=seen.get("forward",set())<=seen.get("relay_receive",set())<=sent
        assert acked<=seen.get("ack_forward",set())
    else:
        assert not any(e["node"]=="R" for e in events)
    assert len(sent)==summary["sent"] and len(received)==summary["received_observed"] and len(acked)==summary["acked"]
    assert len(received|acked)==summary["delivery_confirmed"]
    return {"block":c["block"],"route":c["route"],"id":trial["id"],"sent":len(sent),"received":len(received),
        "acked":len(acked),"forwarded":len(seen.get("forward",set())),"pdr":100*len(received)/len(sent),
        "p95":p95,"goodput":goodput,
        "events_sha256":hashlib.sha256((run_dir/"events.jsonl").read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    args=p.parse_args()
    folder=args.folder.resolve()
    plan=read(folder/"plan.json")
    trials=read(folder/"trials.json")
    rows=[audit(t,folder,plan["parameters"]) for t in trials if "summary" in t]
    assert [[r["block"],r["route"]] for r in rows]==plan["order"]
    n=plan["parameters"]["blocks"]
    rng=np.random.default_rng(plan["parameters"]["seed"])
    sample=rng.integers(0,n,(10000,n))
    metrics={}
    fig,axes=plt.subplots(1,2,figsize=(9,3.9),layout="constrained")
    for ax,(key,label) in zip(axes,[("pdr","Gói nhận tại đích (%)"),("p95","RTT p95 của phiên (ms)")]):
        values=[[next(r[key] for r in rows if r["block"]==b and r["route"]==route) for route in ("direct","relay")] for b in range(1,n+1)]
        v=np.asarray(values)
        change=v[:,1]-v[:,0]
        metrics[key]={"direct_mean":float(v[:,0].mean()),"relay_mean":float(v[:,1].mean()),
            "relay_minus_direct":float(change.mean()),"paired_bootstrap95":np.quantile(change[sample].mean(axis=1),[.025,.975]).tolist() if n > 1 else None}
        for pair in values:ax.plot([0,1],pair,"o-",color="#8d9bbb",alpha=.7)
        ax.plot([0,1],v.mean(axis=0),"D-",color="#304dc8",lw=2.4,label="Trung bình")
        ax.set(xticks=[0,1],xticklabels=["Direct","Relay"],ylabel=label,xlim=(-.3,1.3))
        ax.grid(axis="y",alpha=.2);ax.spines[["right","top"]].set_visible(False)
    fig.suptitle(f"{n} cặp đo trên bàn · mỗi đường mảnh nối hai phiên cùng cặp")
    fig.savefig(folder/"paired.png",dpi=170);plt.close(fig)
    record={"runs":rows,"paired":metrics,"setup_interruptions":[t for t in trials if "error" in t],
        "method":"Receiver-observed PDR. Paired resampling of blocks, 10000 draws, percentile 95%. Descriptive bench pilot." if n > 1 else "Single paired trial for functional acceptance. No interval estimated."}
    (folder/"audit.json").write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8")
    rows_html="".join(f'<tr><td>{r["block"]}</td><td>{r["route"]}</td><td>{r["sent"]}</td><td>{r["forwarded"] if r["route"]=="relay" else "—"}</td><td>{r["received"]}</td><td>{r["acked"]}</td><td>{r["p95"]:.1f}</td><td><a href="../run_{r["id"]}/events.jsonl">{r["id"]}</a></td></tr>' for r in rows)
    template=(LAB/"docs/bench_template.html").read_text(encoding="utf-8")
    items=[]
    for key, label, unit in [("pdr","PDR tại đích (%)","điểm phần trăm"), ("p95","RTT p95 (ms)","ms")]:
        metric = metrics[key]
        ci = metric["paired_bootstrap95"]
        interval = f"KTC bootstrap 95% từ {ci[0]:+.2f} đến {ci[1]:+.2f}" if ci else "Một cặp kiểm tra chức năng, chưa ước lượng khoảng tin cậy"
        items.append(f'<li>{label}. Direct {metric["direct_mean"]:.2f}, Relay {metric["relay_mean"]:.2f}. Chênh lệch Relay − Direct {metric["relay_minus_direct"]:+.2f} {unit}. {interval}.</li>')
    info = "".join(items)
    controls=""
    if (folder/"controls.json").exists():
        cases=read(folder/"controls.json")["runs"]
        items=[]
        for case in cases:
            detail="Làm hỏng CRC mỗi gói thứ 5" if case["kind"]=="crc" else "Bấm tạm dừng, sau đó bật lại relay"
            items.append(f'<li>{detail}. Nguồn gửi {case["sent"]}, ESP loại hoặc giữ lại khi tạm dừng {case["invalid_or_paused"]}, ESP chuyển {case["forward"]}, đích nhận {case["received"]}, nguồn nhận {case["acked"]} ACK. <a href="../run_{case["id"]}/events.jsonl">Log phiên {case["id"]}</a>.</li>')
        controls='<section><h2>Hai phép kiểm chứng đường truyền</h2><ul>'+''.join(items)+'</ul><p>Phiên bản của từng nút được ghi trong metadata của lượt tương ứng. Các lỗi được tạo chủ đích thuộc thí nghiệm riêng.</p><nav><a href="source.png">Màn hình Samsung</a><a href="sink.png">Màn hình OPPO</a><a href="portal.png">Trang ESP32 thật</a><a href="dashboard.png">Dashboard trên laptop</a></nav></section>'
    replacements={"{{controls}}":controls,"{{rows}}":rows_html,"{{stats}}":info,"{{blocks}}":str(n),"{{duration}}":str(plan["parameters"]["duration"]),
        "{{rate}}":str(plan["parameters"]["rate"]),"{{payload}}":str(plan["parameters"]["payload"]),"{{seed}}":str(plan["parameters"]["seed"])}
    for k,v in replacements.items():template=template.replace(k,v)
    (folder/"REPORT.html").write_text(template,encoding="utf-8")
    print(json.dumps(metrics))


if __name__=="__main__":
    main()
