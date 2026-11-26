"""Check a real RelayBox portal and CRC rejection over Wi-Fi (not a relay coverage test)."""
import argparse
import json
import socket
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab.packet import DATA, Packet, payload_for


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='192.168.50.1')
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path):
        with http.open('http://' + args.host + path, timeout=5) as response:
            return response.read()

    page = get('/').decode('utf-8')
    assert 'hotspot' in page and 'name="ssid"' in page and 'name="server"' in page
    before = json.loads(get('/status'))
    assert before['flash_bytes'] == 4194304
    assert before['ap_ip'] == args.host
    # Use only on an idle bench. No DATA packet with a valid CRC is injected.
    assert before['received'] == 0 and before['forwarded'] == 0, 'Stop active experiments before this bench check'
    run = int(time.time()) & 0xffffffff
    attempts = 6
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        for sequence in range(attempts):
            raw = bytearray(Packet(DATA, run, sequence, time.monotonic_ns(), payload_for(run, sequence, 128)).encode())
            raw[-1] ^= 1
            udp.sendto(raw, (args.host, 39010))
            time.sleep(0.1)
    samples = []
    deadline = time.monotonic() + args.seconds
    previous = before
    while True:
        current = json.loads(get('/status'))
        assert current['session'] == before['session'], 'Board rebooted'
        assert current['uptime_ms'] >= previous['uptime_ms'], 'Uptime decreased'
        assert current['queue_lost'] == before['queue_lost'], 'Telemetry queue overflow'
        samples.append(current)
        previous = current
        if time.monotonic() >= deadline:
            break
        time.sleep(min(3, max(0, deadline-time.monotonic())))
    after = samples[-1]
    assert after['invalid'] - before['invalid'] == attempts, 'Not all malformed packets were accounted for'
    assert after['forwarded'] == before['forwarded'], 'Malformed DATA forwarded'
    assert after['received'] == before['received'], 'Malformed DATA accepted'
    result = dict(tested_at_utc=datetime.now(timezone.utc).isoformat(), transport='Actual Wi-Fi from laptop to ESP32 SoftAP',
                  scope='Portal, status, uptime and CRC rejection only; not upstream AP+STA or two-Android forwarding',
                  passed=True, flash_bytes=before['flash_bytes'], psram_bytes=before['psram_bytes'],
                  bad_crc_sent=attempts, bad_crc_rejected=after['invalid']-before['invalid'],
                  observed_uptime_delta_ms=after['uptime_ms']-before['uptime_ms'],
                  session_unchanged=True, sample_count=len(samples), before=before, after=after, samples=samples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('before', 'after', 'samples')}))


if __name__ == '__main__':
    main()
