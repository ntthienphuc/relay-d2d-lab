"""Two-user BPSK superposition and ideal-CSI SIC, software AWGN example.
This is a teaching example, not the full cooperative-NOMA paper model.
"""
import json
from pathlib import Path
import numpy as np


def run(n=100000, seed=20261124):
    rng = np.random.default_rng(seed)
    b1 = rng.integers(0, 2, n)
    b2 = rng.integers(0, 2, n)
    s1, s2 = 1 - 2*b1, 1 - 2*b2
    a1, a2 = 0.2, 0.8
    mixed = np.sqrt(a1)*s1 + np.sqrt(a2)*s2
    # At the near receiver, h=1 is known. N0=1/rho; real noise var=N0/2.
    def decode(y):
        b2_hat = (y < 0).astype(int)
        residual = y - np.sqrt(a2)*(1 - 2*b2_hat)
        b1_hat = (residual < 0).astype(int)
        return b1_hat, b2_hat, residual
    b1_clean, b2_clean, _ = decode(mixed)
    assert np.array_equal(b1, b1_clean) and np.array_equal(b2, b2_clean)
    rows = []
    for snr_db in [0, 4, 8, 12, 16]:
        y = mixed + rng.normal(0, np.sqrt(1/(2*10**(snr_db/10))), n)
        bh1, bh2, _ = decode(y)
        rows.append({'snr_db': snr_db, 'ber_near_without_sic': float(np.mean((y<0) != b1)),
                     'ber_near_after_sic': float(np.mean(bh1 != b1)),
                     'ber_far_stream_at_near': float(np.mean(bh2 != b2))})
    return {'seed': seed, 'samples': n, 'alpha_near': a1, 'alpha_far': a2,
            'scope': 'uncoded BPSK, AWGN, near receiver only, no relay hop or RF hardware', 'rows': rows}


if __name__ == '__main__':
    result = run()
    Path('noma_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('PASS: noiseless SIC recovers both independent bit streams')
    print(json.dumps(result['rows'], indent=2))
