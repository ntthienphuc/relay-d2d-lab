"""System-level HD relay outage, separate from coded frame-error simulation."""
import json
from pathlib import Path
import numpy as np


def run(n=1000000, seed=20261124, rate=0.5, relay_position=0.5):
    rng = np.random.default_rng(seed)
    u, v, w = rng.exponential(1, (3, n))
    osr = relay_position**-2.2
    ord_ = (1 - relay_position)**-2.2
    threshold = 2**(2*rate) - 1
    rows = []
    for snr_db in range(-10, 31, 2):
        rho = 10**(snr_db/10)
        a, b = rho*osr*u, rho*ord_*v
        c_df = 0.5*np.log2(1 + np.minimum(a, b))
        c_fg = 0.5*np.log2(1 + a*b/(b + rho*osr + 1))
        c_vg = 0.5*np.log2(1 + a*b/(a + b + 1))
        c_direct = np.log2(1 + rho*w)
        row = {'snr_db': snr_db}
        for name, capacity in [('DF',c_df),('AF-FG',c_fg),('AF-VG',c_vg),('Direct',c_direct)]:
            k = int(np.count_nonzero(capacity < rate))
            p, z = k/n, 1.959963984540054
            den = 1 + z*z/n
            mid = (p + z*z/(2*n))/den
            half = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
            row[name] = {'outage':p, 'ci95':[max(0.,mid-half),min(1.,mid+half)]}
        row['df_closed'] = float(-np.expm1(-threshold*(1/(rho*osr)+1/(rho*ord_))))
        rows.append(row)
    return {'samples':n,'seed':seed,'rate_bps_hz_full_frame':rate,'rows':rows,
            'assumptions':'SISO; independent Rayleigh; equal HD slots; perfect CSI and ideal DF; no direct-path combining'}


if __name__ == '__main__':
    result = run()
    Path('outage_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    difference=max(abs(r['DF']['outage']-r['df_closed']) for r in result['rows'])
    print('Max absolute DF Monte Carlo / closed-form difference:',difference)
    assert difference < 0.003, 'Unexpected mismatch; inspect assumptions and sampling'
