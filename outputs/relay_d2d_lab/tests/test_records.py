import time
from lab.records import Run


def test_deduplicated_telemetry_and_trace_preserve_receiver_evidence():
    config={'duration':1,'rate':1,'payload':128,'environment':'test','route':'relay'}
    run=Run(int(time.time()*1000)%0x7fffffff,config,'PYTEST record reconciliation')
    try:
        run.sent[0]=time.perf_counter_ns()
        run.event({'type':'send','node':'S','seq':0,'bytes':128})
        e={'event_id':'receipt-0','type':'receive','node':'D','seq':0,'bytes':128}
        run.event(e);run.event(e)
        assert run.snapshot()['received_observed']==1
        assert run.snapshot()['delivery_confirmed']==1
        assert run.snapshot()['acked']==0  # ACK loss does not erase sink evidence.
        assert run.bytes_received==128
        assert len(run.traces[0]['events'])==2
        run.event({'type':'drop_paused','node':'R','seq':1})
        assert run.snapshot()['dropped_by_relay']==1
    finally:run.close();run.log.close()
