import json
import time

import pytest
from fastapi.testclient import TestClient

from lab import network, records, server
from scripts.reset_practice import archive_runs


@pytest.fixture
def desk(tmp_path, monkeypatch):
    results = tmp_path / "results"
    (results / "final").mkdir(parents=True)
    (results / "final/evidence_ids.json").write_text("[]")
    for module in (records, network, server):
        monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(server, "engine", network.Engine())
    monkeypatch.setenv("RELAY_LAB_PRACTICE", "1")
    with TestClient(server.app) as client:
        yield client


def test_repeatable_archive_preserves_evidence_and_partial_runs(tmp_path):
    results = tmp_path / "results"
    (results / "final").mkdir(parents=True)
    (results / "final/evidence_ids.json").write_text("[42]")
    for name in ("run_42", "run_43", "run_44", "run_misc", "paired_1"):
        (results / name).mkdir()
        (results / name / "events.jsonl").write_text(name)
    backup, count = archive_runs(results, tmp_path / "archive")
    assert count == 2
    assert (backup / "run_43/events.jsonl").read_text() == "run_43"
    assert (backup / "run_44/events.jsonl").read_text() == "run_44"
    assert sorted(p.name for p in results.iterdir()) == ["final", "paired_1", "run_42", "run_misc"]
    assert archive_runs(results, tmp_path / "archive") == (None, 0)


@pytest.mark.parametrize(("path", "payload", "code"), [
    ("run", {"environment": "live"}, 400),
    ("run", {"route": "other"}, 400),
    ("run", {"duration": 0}, 422),
    ("simulation", {"samples": 10}, 400),
    ("simulation", {"unknown": 1}, 400),
    ("network", {"server_ip": "not-an-ip"}, 400),
    ("events", {"events": [None] * 501}, 400),
])
def test_invalid_request_leaves_room_ready(desk, path, payload, code):
    assert desk.post("/api/" + path, json=payload).status_code == code
    assert desk.get("/api/status").json()["run"] is None


def test_pause_resume_stop_replay_and_start_again(desk):
    status = desk.get("/api/status").json()
    assert status["http_port"] == 8877 and status["practice"]
    assert desk.post("/api/pause-relay").status_code == 400
    config = {"environment": "local", "route": "relay", "rate": 25, "duration": 8}
    rid = desk.post("/api/run", json=config).json()["id"]
    assert desk.post("/api/run", json=config).status_code == 400
    assert desk.post("/api/pause-relay").json() == {"paused": True}
    deadline = time.monotonic() + 4
    while not desk.get("/api/status").json()["run"]["dropped_by_relay"]:
        assert time.monotonic() < deadline
        time.sleep(.05)
    assert desk.post("/api/pause-relay").json() == {"paused": False}
    assert desk.post("/api/stop").is_success
    saved = desk.get(f"/api/replay/{rid}").json()
    assert saved["summary"]["stop_reason"] == "operator_stop"
    assert desk.post("/api/pause-relay").status_code == 400
    assert any(e["type"] == "drop_paused" for e in saved["events"])
    assert desk.get(f"/api/trace/{rid}?filter=missing").json()["matching"] > 0
    assert desk.get("/api/history?scope=evidence").json() == []
    assert desk.get("/api/history?scope=new").json()[0]["id"] == rid
    again = desk.post("/api/run", json={**config, "route": "direct"})
    assert again.is_success and again.json()["id"] != rid
    assert desk.post("/api/stop").is_success

