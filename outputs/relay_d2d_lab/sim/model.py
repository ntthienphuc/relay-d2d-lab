"""Rayleigh block fading, HD AF/DF; no PHY claim about the UDP experiment."""
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class Config:
    samples: int = 100000
    seed: int = 20261124
    rate: float = 0.5  # bit/s/Hz over whole frame
    relay_position: float = 0.5
    pathloss: float = 2.2
    qos: float = 0.1
    processing_mj: float = 0.2
    csi_mj: float = 0.1


def wilson(k, n):
    p = k / n
    z = 1.959963984540054
    d = 1 + z*z/n
    mid = (p + z*z/(2*n))/d
    half = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return float(max(0, mid-half)), float(min(1, mid+half))


def evaluate(config=None, snrs=None):
    c = config or Config()
    if not 1000 <= c.samples <= 2000000:
        raise ValueError('samples must be 1000..2000000')
    if not 0.1 <= c.relay_position <= 0.9 or not 0.1 <= c.rate <= 3:
        raise ValueError('Invalid relay position or rate')
    if not 1 <= c.pathloss <= 4 or not 0 < c.qos < 1:
        raise ValueError('Invalid pathloss/QoS')
    if not 0 <= c.processing_mj <= 20 or not 0 <= c.csi_mj <= 20:
        raise ValueError('Invalid modeled energy')
    rng = np.random.default_rng(c.seed)
    # Exponential power gains equivalent to squared circular-complex Gaussian.
    u, v, w = rng.exponential(1, (3, c.samples))
    osr, ord_ = c.relay_position**(-c.pathloss), (1-c.relay_position)**(-c.pathloss)
    tau = np.expm1(2*c.rate*np.log(2))
    rows = []
    for snr_db in (snrs if snrs is not None else np.arange(-10, 31, 2)):
        rho = 10**(float(snr_db)/10)
        a, b, direct = rho*osr*u, rho*ord_*v, rho*w
        # N_R=N_D=1. P_S=P_R=P_D=rho for equal expected TX energy/frame.
        vg = a*b/(a+b+1)
        fg = a*b/(b+rho*osr+1)
        rates = {'Direct': np.log2(1+direct), 'DF': .5*np.log2(1+np.minimum(a,b)),
                 'AF-FG': .5*np.log2(1+fg), 'AF-VG': .5*np.log2(1+vg)}
        # Illustrative model: T=10ms, W=100kHz, N=0.01mW, PA efficiency .35.
        # Relay totals: source TX half, relay RX/TX halves, dest RX half.
        rf_mj = rho * .01 * .01 / .35
        energies = {'Direct': rf_mj+.4, 'DF': rf_mj+.6+c.processing_mj+c.csi_mj,
                    'AF-FG': rf_mj+.6+.02, 'AF-VG': rf_mj+.6+.02+c.csi_mj}
        row = {'snr_db': float(snr_db), 'modes': {}}
        for mode, rate in rates.items():
            k = int(np.count_nonzero(rate < c.rate))
            outage = k/c.samples
            lo, hi = wilson(k,c.samples)
            row['modes'][mode] = {'outage': outage, 'failures': k, 'ci95': [lo,hi],
                'throughput_bps_hz': c.rate*(1-outage), 'energy_mj': energies[mode],
                'bits_per_joule': c.rate*100000*.01*(1-outage)/(energies[mode]/1000)}
        row['df_closed'] = float(-np.expm1(-tau*(1/(rho*osr)+1/(rho*ord_))))
        row['direct_closed'] = float(-np.expm1(-np.expm1(c.rate*np.log(2))/rho))
        relay_modes = ['DF','AF-FG','AF-VG']
        feasible = [m for m in relay_modes if row['modes'][m]['ci95'][1] <= c.qos]
        row['selected'] = max(feasible,key=lambda m:row['modes'][m]['bits_per_joule']) if feasible else 'INFEASIBLE'
        row['outage_choice'] = min(relay_modes,key=lambda m:row['modes'][m]['outage'])
        rows.append(row)
    return {'config': asdict(c), 'rows': rows, 'units': 'end-to-end bit/s/Hz; energy modeled, not measured',
            'model': 'SISO Rayleigh independent blocks; equal HD slots; no S-D combining; ideal CSI/DF',
            'energy_assumption': 'Illustrative sensitivity model, not calibrated hardware. Circuit: Direct .4mJ, relay .6mJ; AF processing .02mJ/frame. Costs non-overlapping.',
            'selection': 'Relay candidates only; upper Wilson 95% outage <= QoS. In-sample choice, no performance superiority claim.',
            'frame_s': .01, 'bandwidth_hz': 100000}
