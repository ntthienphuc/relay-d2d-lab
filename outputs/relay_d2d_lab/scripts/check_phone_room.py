"""Compare source, relay, sink and local Android logs for the November 26 bench."""
from pathlib import Path
import json

RESULTS = Path(__file__).resolve().parents[1] / "results"
CASES = ((395570653, "sink", 0), (395590684, "source", 0), (395604760, "source", 5))

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line]

def packets(events, kind):
    return {e["seq"]: e for e in events if e["type"] == kind}

def check():
    sent = set(range(50))
    for run, role, drop in CASES:
        folder = RESULTS / f"run_{run}"
        events = rows(folder / "events.jsonl")
        local = rows(folder / "android-local.jsonl")
        assert all(e["run"] == run for e in events + local)
        lost = {i for i in sent if drop and (i + 1) % drop == 0}
        delivered = sent - lost
        for kind in ("send", "relay_receive"):
            assert set(packets(events, kind)) == sent
        assert set(packets(events, "drop_injected")) == lost
        for kind in ("forward", "receive", "ack_forward", "ack"):
            assert set(packets(events, kind)) == delivered
        for kind, expected in ([("receive", delivered), ("ack_sent", delivered)] if role == "sink"
                               else [("send", sent), ("ack", delivered)]):
            assert set(packets(local, kind)) == expected
        for seq in delivered:
            origin = packets(events, "send")[seq]
            ack = packets(events, "ack")[seq]
            assert ack["sent_ns"] == origin["sent_ns"] and ack["hops"] == 1
        print(f"{run} Android {role}: {len(delivered)}/50, {len(lost)} injected drops")
    room = RESULTS / "phone_room_396250058"
    receiver = rows(room / "pc-peer.jsonl")
    phone = rows(room / "android-local.jsonl")
    acks = packets(phone, "ack")
    assert set(acks) == sent == {e["seq"] for e in receiver}
    assert all(e["run"] == 396250058 and e["hops"] == 1 and
               e["sent_ns"] == acks[e["seq"]]["sent_ns"] for e in receiver)
    print("396250058 Android room host: 50 matching DATA/ACK with PC receiver")

if __name__ == "__main__":
    check()

