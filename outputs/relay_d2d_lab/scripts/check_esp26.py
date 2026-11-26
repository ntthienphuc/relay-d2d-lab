"""Audit ESP32 HTTPS observations and the source, relay, sink and Android journals."""
import json
from pathlib import Path

def check(lab):
    results = Path(lab) / "results"
    folder = results / "internet_26"
    def record(name):
        return json.loads((folder / name).read_text("utf8"))
    def rows(path):
        return [json.loads(l) for l in path.read_text("utf8").splitlines()]
    old = record("esp-before.json")
    assert not old["ok"] and old["gateway"] == "192.168.50.1"
    board = record("esp-status.json")
    assert board["version"] == "2.6.0" and board["ipv4_forwarding"] and board["internet_mode"] == "routing_ipv4"
    phone = rows(folder / "esp-https.jsonl")
    assert len({entry["time_ms"] for entry in phone}) == 3
    assert all(entry["ok"] and entry["http_status"] == 204 and entry["gateway"] == board["ap_ip"] for entry in phone)
    final = record("esp-flow.json")
    assert final["relay"] == board["id"] and final["firmware"] == board["version"] and final["http_status"] == 204
    pc = record("esp-pc.json")
    assert (pc["gateway"],pc["dns"],pc["http"],pc["tls"]) == (board["ap_ip"],board["dhcp_dns"],204,"TLSv1.3")
    for rid, phone_node in ((405451643,"D"),(405462659,"S")):
        run = results / f"run_{rid}"
        events, android = rows(run/"events.jsonl"), rows(run/"android.jsonl")
        for node,kind in (("S","send"),("R","forward"),("D","receive"),("S","ack")):
            expected = set(range(40))
            seq = {e["seq"] for e in events if e["node"] == node and e["type"] == kind}
            assert seq == expected
            if node == phone_node:
                assert {e["seq"] for e in android if e["node"] == node and e["type"] == kind} == seq
    final_phone=record("esp-final-flow.json")
    final_pc=record("esp-final-pc.json")
    assert final_phone["ok"] and final_phone["relay"]==board["id"] and final_phone["http_status"]==204
    assert final_pc["gateway"]==board["ap_ip"] and final_pc["http"]==204
    for case in record("latest-cases.json"):
        run=results/f'run_{case["id"]}'
        journal=rows(run/"events.jsonl")
        for kind,node,num in (("send","S","sent"),("forward","R","forwarded"),("receive","D","received"),("ack","S","acked")):
            assert len({e["seq"] for e in journal if e["type"]==kind and e["node"]==node})==case[num]
        rejected={e["seq"] for e in journal if e["type"]=="invalid" and e["node"]=="R"}
        assert rejected==set(case["invalid"])
        assert rejected.isdisjoint({e["seq"] for e in journal if e["type"]=="forward"})
    print("ESP32 2.6: phone and Windows HTTPS observations verified; both 40-packet runs match Android logs.")

if __name__=="__main__":
    check(Path(__file__).resolve().parents[1])

