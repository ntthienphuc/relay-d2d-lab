"""Recompute the final report's channel model and audit its two bench series."""
import json
import hashlib
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
sys.path.insert(1, str(LAB / "scripts"))
from sim.model import Config, evaluate
from report_bench import audit

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check_channel():
    folder = LAB / "results" / "final"
    reference = load(folder / "monte_carlo_final.json")
    config = Config(**reference["config"])
    snr = [row["snr_db"] for row in reference["rows"]]
    assert snr == list(range(-8, 23, 2)), "Incomplete or reordered SNR grid"
    assert config.samples == 1000000 and config.seed == 20261126
    repeated = evaluate(config, snr)
    assert repeated["rows"] == reference["rows"], "SNR model fields differ"
    for old, new in zip(reference["rows"], repeated["rows"]):
        assert old["selected"] == new["selected"]
        assert np.isclose(old["df_closed"], new["df_closed"])
        for mode in old["modes"]:
            assert old["modes"][mode]["failures"] == new["modes"][mode]["failures"]
    checks = load(folder / "relay_positions.json")
    assert len(checks) == 7, "Expected seven relay positions"
    for x, old in zip((.15, .25, .35, .50, .65, .75, .85), checks):
        row = evaluate(Config(samples=250000, seed=20261126, relay_position=x), [8])["rows"][0]
        assert row == old, f"Position {x} differs"
        for mode in old["modes"]:
            assert row["modes"][mode]["failures"] == old["modes"][mode]["failures"]
    print("Reproduced all 16 SNR points and seven relay positions.")

def check_hardware():
    manifest = load(LAB / "results/final/verification.json")
    studies = list(manifest["paired"])
    acceptance = manifest.get("ui_acceptance", {})
    if acceptance.get("study"):
        studies.append(acceptance["study"])
    release = load(LAB / "results/final/release24.json")
    for run_id, digest in release["raw_event_sha256"].items():
        assert hashlib.sha256((LAB / f"results/run_{run_id}/events.jsonl").read_bytes()).hexdigest() == digest
    studies.append(release["study"])
    assert len(studies) == len(set(studies)) == 4
    for name in studies:
        folder = LAB / "results" / name
        plan = load(folder / "plan.json")
        trials = load(folder / "trials.json")
        rebuilt = [audit(t, folder, plan["parameters"]) for t in trials if "summary" in t]
        assert [(r["block"], r["route"]) for r in rebuilt] == [tuple(pair) for pair in plan["order"]]
        assert len(rebuilt) == 2 * plan["parameters"]["blocks"]
        historical = load(folder / "audit.json")["runs"]
        assert len(rebuilt) == len(historical)
        for new, old in zip(rebuilt, historical):
            assert new.keys() == old.keys()
            for field, value in new.items():
                if field in ("p95", "goodput"):
                    assert np.isclose(value, old[field], rtol=0, atol=1e-9)
                else:
                    assert value == old[field]
        print(name, len(rebuilt), "sessions match the raw events.")
    delivery = load(LAB / "results/final/release25.json")
    assert len(delivery["new_ui_probes"]) == 2
    for case in delivery["new_ui_probes"]:
        folder = LAB / f'results/run_{case["id"]}'
        raw = folder / "events.jsonl"
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == case["sha256"]
        event_rows = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
        groups = {}
        for node, kind in (("S","send"),("D","receive"),("S","ack"),("R","forward")):
            groups[kind] = {e["seq"]: e for e in event_rows if e["node"] == node and e["type"] == kind}
        assert groups["receive"].keys() <= groups["send"].keys()
        assert groups["ack"].keys() <= groups["send"].keys()
        assert [len(groups[k]) for k in ("send","receive","ack","forward")] == [case[k] for k in ("sent","received","acks","forwarded")]
        invalid = {e["seq"] for e in event_rows if e["node"] == "R" and e["type"] == "invalid"}
        assert len(invalid) == case["invalid_relay"] and invalid.isdisjoint(groups["forward"])
        config = load(folder / "config.json")
        assert config["corrupt_every"] == case["corrupt_every"]
        assert config["route"] == case["route"]
        assert np.isclose(np.percentile([e["rtt_ms"] for e in groups["ack"].values()], 95), case["p95_ms"], rtol=0, atol=1e-9)
        goodput = sum(e["bytes"] for e in groups["receive"].values()) * 8 / (1000 * config["duration"])
        assert np.isclose(goodput, case["goodput_kbps"], rtol=0, atol=1e-9)
    print("Relay Lab 2.5: retained Direct and ESP32 UI probes match the raw events.")
    apk = LAB / "android/build/relaylab.apk"
    internet_release = load(LAB / "results/final/release26.json")
    assert hashlib.sha256(apk.read_bytes()).hexdigest() == load(LAB / "results/final/release27.json")["apk_sha256"]
    firmware = LAB / "esp32/build/cam/RelayBox.ino.bin"
    assert hashlib.sha256(firmware.read_bytes()).hexdigest() == internet_release["esp_cam_bin_sha256"]
    for case in manifest["alternate_payloads"]:
        s = load(LAB / "results" / ("run_" + str(case["id"])) / "summary.json")
        assert (case["sent"],case["received"],case["acked"]) == (s["sent"],s["received_observed"],s["acked"])

def check_ux_sessions():
    results = LAB / "results"
    release = load(results / "ux_261/acceptance.json")
    assert len(release["runs"]) == 5 and not release["browser_errors"]
    for trial in release["runs"]:
        folder = results / f'run_{trial["id"]}'
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text("utf8").splitlines()]
        for node, kind, field in (("S", "send", "sent"), ("D", "receive", "received_observed"), ("S", "ack", "acked")):
            seqs = {e["seq"] for e in events if e["node"] == node and e["type"] == kind}
            assert len(seqs) == trial[field], (trial["id"], field, len(seqs))
        rtt = {e["seq"]: e["rtt_ms"] for e in events if e["node"] == "S" and e["type"] == "ack"}
        assert np.isclose(np.percentile(list(rtt.values()), 95), trial["rtt_p95_ms"])
        if trial["environment"] == "live":
            phone = [json.loads(line) for line in (folder / "android.jsonl").read_text("utf8").splitlines()]
            event_ids = {e["event_id"] for e in events if e.get("event_id")}
            assert phone and all(e["run"] == trial["id"] for e in phone)
            # The sink records ACK transmission locally. The source reports ACK arrival separately.
            assert all(e["event_id"] in event_ids for e in phone if e["type"] != "ack_sent")
            if any(e["node"] == "D" for e in phone):
                local_packets = lambda kind: {(e["seq"], e["sent_ns"]) for e in phone if e["type"] == kind}
                assert local_packets("ack_sent") == local_packets("receive")
    print("PC 2.6.1: retained sessions match the packet traces and endpoint journals.")


if __name__ == "__main__":
    check_channel()
    check_hardware()
    check_ux_sessions()
    from check_phone_room import check
    check()

    from check_esp26 import check as check_esp
    check_esp(LAB)
    from check_board_model import check as check_model
    check_model(LAB / 'results/internet_26/board-model.json')
