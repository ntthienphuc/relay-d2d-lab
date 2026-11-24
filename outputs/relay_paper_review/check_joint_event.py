"""Narrow independent check of U1 outage, not a reproduction of the full paper.

Source: Tran & Voznak, Sensors 2019, 19, 1845, equations (3)-(5), (16)-(17).
Both SIC decoding events use the SAME channel realization within a block.
"""
import json
from pathlib import Path

import numpy as np


def main():
    seed, n = 20261114, 1_000_000
    rng = np.random.default_rng(seed)
    x = rng.exponential(5.0, n)
    y = rng.exponential(0.01, n)
    rho0 = rho1 = 1.0
    a1, a2 = 0.25, 0.75
    r1 = r2 = 0.2
    t1, t2 = 2 ** (2 * r1) - 1, 2 ** (2 * r2) - 1
    c1, c2 = t1 / (a1 * rho0), t2 / ((a2 - a1 * t2) * rho0)
    result = {"seed": seed, "samples": n, "snr_db": 0, "results": []}
    for mode, eps in [("HD", 0), ("FD", 1)]:
        noise = 1 + eps * rho1 * y
        sinr12 = a2 * rho0 * x / (a1 * rho0 * x + noise)
        sinr11 = a1 * rho0 * x / noise
        fail = (sinr12 < t2) | (sinr11 < t1)
        p_mc = float(np.mean(fail))
        c = max(c1, c2)
        p_joint = 1 - np.exp(-c / 5) / (1 + c * eps * rho1 * 0.01 / 5)
        s1 = np.exp(-c1 / 5) / (1 + c1 * eps * rho1 * 0.01 / 5)
        s2 = np.exp(-c2 / 5) / (1 + c2 * eps * rho1 * 0.01 / 5)
        p_product = 1 - s1 * s2
        z = 1.959963984540054
        den = 1 + z * z / n
        center = (p_mc + z * z / (2 * n)) / den
        half = z * np.sqrt(p_mc * (1 - p_mc) / n + z * z / (4 * n * n)) / den
        result["results"].append({
            "mode": mode,
            "direct_event_monte_carlo": p_mc,
            "wilson_95_ci": [float(center-half), float(center+half)],
            "joint_threshold_closed_form": float(p_joint),
            "product_of_marginals_as_printed_eq17": float(p_product),
        })
    path = Path(__file__).with_name("joint_event_check.json")
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
