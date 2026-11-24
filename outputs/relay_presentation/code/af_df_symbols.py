"""Educational baseband relay: Hamming(7,4), BPSK, CRC32, HD Rayleigh.

This simulates complex I/Q samples in software. It does not control Android RF.
P_s=P_r=rho, E|h|^2=1, E|n|^2=1. Each relay frame uses two equal slots.
No direct-link combining, perfect channel knowledge, no synchronization error.
CRC detects errors; it does not correct them. Hamming corrects one bit/codeword.
"""
from pathlib import Path
import argparse
import json
import zlib
import numpy as np


def hamming_encode(bits):
    shape = bits.shape
    d = bits.reshape(-1, 4).astype(np.uint8)
    c = np.zeros((len(d), 7), dtype=np.uint8)
    c[:, [2, 4, 5, 6]] = d
    c[:, 0] = d[:, 0] ^ d[:, 1] ^ d[:, 3]
    c[:, 1] = d[:, 0] ^ d[:, 2] ^ d[:, 3]
    c[:, 3] = d[:, 1] ^ d[:, 2] ^ d[:, 3]
    return c.reshape(*shape[:-1], shape[-1] // 4 * 7)


def hamming_decode(coded):
    shape = coded.shape
    c = coded.reshape(-1, 7).copy().astype(np.uint8)
    s1 = c[:, 0] ^ c[:, 2] ^ c[:, 4] ^ c[:, 6]
    s2 = c[:, 1] ^ c[:, 2] ^ c[:, 5] ^ c[:, 6]
    s4 = c[:, 3] ^ c[:, 4] ^ c[:, 5] ^ c[:, 6]
    syndrome = s1 + 2 * s2 + 4 * s4
    rows = np.flatnonzero(syndrome)
    c[rows, syndrome[rows] - 1] ^= 1
    return c[:, [2, 4, 5, 6]].reshape(*shape[:-1], shape[-1] // 7 * 4)


def append_crc(payload):
    raw = [bytes(row) + zlib.crc32(bytes(row)).to_bytes(4, 'big') for row in payload]
    return np.stack([np.frombuffer(row, dtype=np.uint8) for row in raw])


def crc_ok(frame_bytes):
    return np.array([zlib.crc32(bytes(row[:-4])) == int.from_bytes(row[-4:], 'big')
                     for row in frame_bytes], dtype=bool)


def modulate(frame_bytes):
    coded = hamming_encode(np.unpackbits(frame_bytes, axis=1))
    return 1.0 - 2.0 * coded  # BPSK: 0 -> +1, 1 -> -1


def receive(samples, effective_channel):
    hard_bits = (np.real(samples / effective_channel) < 0).astype(np.uint8)
    decoded_bits = hamming_decode(hard_bits)
    return np.packbits(decoded_bits, axis=1)


def af_forward(y_r, h_sr, power, mode):
    if mode == 'AF-VG':
        gain = np.sqrt(power / (power * np.abs(h_sr)**2 + 1.0))
    elif mode == 'AF-FG':
        gain = np.sqrt(power / (power + 1.0))
    else:
        raise ValueError(mode)
    return gain * y_r, gain


def df_forward(y_r, h_sr, power):
    decoded = receive(y_r, np.sqrt(power) * h_sr)
    accepted = crc_ok(decoded)
    # Regenerate from the decoded payload, NEVER from the known source payload.
    regenerated = modulate(append_crc(decoded[:, :-4]))
    transmitted = np.sqrt(power) * regenerated * accepted[:, None]
    return transmitted, accepted


def metrics(reference, recovered, sent):
    exact = np.all(reference == recovered[:, :-4], axis=1)
    accepted = sent & crc_ok(recovered)
    successful = accepted & exact
    errors = np.unpackbits(reference ^ recovered[:, :-4], axis=1)
    return {
        'frame_failure_rate': float(1 - successful.mean()),
        'relay_drop_rate': float(1 - sent.mean()),
        'crc_accept_rate': float(accepted.mean()),
        'undetected_bad_frames': int(np.count_nonzero(accepted & ~exact)),
        'payload_ber_given_forwarded': float(errors[sent].mean()) if sent.any() else None,
        'correct_frames': int(successful.sum()),
        'frames': len(reference),
    }


def experiment(frames=3000, seed=20261124, payload_bytes=16):
    rng = np.random.default_rng(seed)
    payload = rng.integers(0, 256, (frames, payload_bytes), dtype=np.uint8)
    x = modulate(append_crc(payload))
    cn = lambda shape: (rng.normal(size=shape) + 1j*rng.normal(size=shape)) / np.sqrt(2)
    # Common random channels/noise for the protocol comparison at each SNR.
    h1, h2 = cn((frames, 1)), cn((frames, 1))
    n1, n2 = cn(x.shape), cn(x.shape)
    rows = []
    for snr_db in [-2, 2, 6, 10, 14, 18, 22]:
        power = 10**(snr_db / 10)
        y_r = np.sqrt(power) * h1 * x + n1
        row = {'snr_db': snr_db, 'modes': {}}
        for mode in ['AF-FG', 'AF-VG']:
            x_r, gain = af_forward(y_r, h1, power, mode)
            y_d = h2 * x_r + n2
            decoded = receive(y_d, h2 * gain * h1 * np.sqrt(power))
            row['modes'][mode] = metrics(payload, decoded, np.ones(frames, bool))
        x_r, forwarded = df_forward(y_r, h1, power)
        y_d = h2 * x_r + n2
        decoded = receive(y_d, h2 * np.sqrt(power))
        row['modes']['DF'] = metrics(payload, decoded, forwarded)
        rows.append(row)
    return {'seed': seed, 'payload_bytes': payload_bytes, 'frames_per_point': frames,
            'model': 'complex Rayleigh block fading; Hamming(7,4); CRC32; BPSK; perfect CSI; equal HD slots',
            'snr_definition': 'P/N0 per transmitted coded BPSK symbol, NOT information-bit Eb/N0',
            'metric_note': 'Frame failure counts relay erasures and destination failures. Conditional BER excludes erased frames; do not compare it alone.',
            'rows': rows}


def self_test():
    messages = ((np.arange(16)[:, None] >> np.arange(3, -1, -1)) & 1).astype(np.uint8)
    coded = hamming_encode(messages)
    np.testing.assert_array_equal(hamming_decode(coded), messages)
    for bit in range(7):
        bad = coded.copy(); bad[:, bit] ^= 1
        np.testing.assert_array_equal(hamming_decode(bad), messages)
    payload = np.arange(32, dtype=np.uint8).reshape(2, 16)
    framed = append_crc(payload)
    assert crc_ok(framed).all()
    bad = framed.copy(); bad[0, 0] ^= 1
    assert not crc_ok(bad)[0]
    x = modulate(framed)
    h1 = np.array([[0.8 + 0.4j], [0.5 - 0.2j]])
    h2 = np.array([[0.7 - 0.1j], [0.9 + 0.3j]])
    power = 3.0
    y_r = h1 * np.sqrt(power) * x
    for mode in ['AF-FG', 'AF-VG']:
        x_r, g = af_forward(y_r, h1, power, mode)
        np.testing.assert_array_equal(receive(h2*x_r, h2*g*h1*np.sqrt(power)), framed)
    x_r, ok = df_forward(y_r, h1, power)
    assert ok.all()
    np.testing.assert_array_equal(receive(h2*x_r, h2*np.sqrt(power)), framed)
    # A different valid received frame must be forwarded as decoded, not oracle-corrected.
    alternate = append_crc(payload ^ 7)
    x_r, ok = df_forward(h1*np.sqrt(power)*modulate(alternate), h1, power)
    assert ok.all()
    np.testing.assert_array_equal(receive(h2*x_r, h2*np.sqrt(power)), alternate)
    print('PASS: 16 Hamming messages, every single-bit error, CRC, noiseless AF/DF, no-oracle forwarding')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=int, default=3000)
    parser.add_argument('--out', type=Path, default=Path('baseband_results.json'))
    args = parser.parse_args()
    self_test()
    result = experiment(args.frames)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    for row in result['rows']:
        print(row['snr_db'], {m: round(v['frame_failure_rate'], 4) for m,v in row['modes'].items()})
