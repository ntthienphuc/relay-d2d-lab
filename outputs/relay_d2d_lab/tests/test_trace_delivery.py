import asyncio
from pathlib import Path

from lab import records, server

def test_live_forward_duration_survives_ack_telemetry(tmp_path, monkeypatch):
    monkeypatch.setattr(records, 'RESULTS', tmp_path)
    run = records.Run(42, {'duration': 1, 'route': 'relay', 'rate': 1, 'payload': 128}, 'test')
    try:
        run.event({'node': 'R', 'type': 'forward', 'seq': 0, 'processing_ms': .537})
        run.event({'node': 'R', 'type': 'ack_forward', 'seq': 0, 'processing_ms': 0})
        assert run.traces[0]['processing_ms'] == .537
    finally:
        run.log.close()

def test_archived_replay_preserves_forward_and_rejection():
    data = asyncio.run(server.trace(376666629, 'all'))
    packets = {row['seq']: row for row in data['packets']}
    assert -1 not in packets and len(packets) == 100
    assert packets[0]['processing_ms'] == .537
    assert packets[0]['rtt_ms'] == 46.794231
    assert packets[4]['invalid'] and 'forward' not in packets[4]
    assert 'ack' not in packets[4]



def test_missing_ack_includes_data_received_at_destination():
    run_id = 382833268
    missing = asyncio.run(server.trace(run_id, 'missing'))
    acknowledged = asyncio.run(server.trace(run_id, 'ack'))
    assert missing['total'] == 40 and missing['matching'] == 8
    assert {p['seq'] for p in missing['packets']} == set(range(3, 11))
    assert all(p['receive'] and not p.get('ack') for p in missing['packets'])
    assert acknowledged['matching'] == 32
    assert all(p['ack'] for p in acknowledged['packets'])
