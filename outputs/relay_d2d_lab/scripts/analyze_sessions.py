"""Summarise repeated sessions, keeping the experimental session as the unit."""
import argparse
import json
from pathlib import Path
import numpy as np


def summarize(results, seed=20261125, resamples=10000):
    rng=np.random.default_rng(seed)
    groups={}
    for r in results:
        groups.setdefault(r['config']['route'],[]).append(r)
    summary={'unit':'session, not packet','bootstrap_seed':seed,'resamples':resamples,
             'limits':'Descriptive pilot intervals; independent representative sessions are required for inference. '
                      'A zero-width interval with all sessions at 100% does not establish perfect reliability.',
             'routes':{}}
    for route,runs in groups.items():
        good=[r for r in runs if r['complete_send'] and not r.get('stop_reason')]
        row={'total_sessions':len(runs),'complete_sessions':len(good),
             'excluded_incomplete_ids':[r['id'] for r in runs if r not in good],'metrics':{}}
        for key in ('pdr_confirmed','goodput_kbps','rtt_p95_ms'):
            values=np.array([r[key] for r in good if r[key] is not None],dtype=float)
            if not len(values):continue
            means=values[rng.integers(0,len(values),size=(resamples,len(values)))].mean(axis=1)
            row['metrics'][key]={'session_values':values.tolist(),'mean':float(values.mean()),
                'min':float(values.min()),'max':float(values.max()),
                'mean_bootstrap95':np.quantile(means,[.025,.975]).tolist() if len(values)>=3 else None}
        summary['routes'][route]=row
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('results_json',type=Path)
    args=parser.parse_args();target=args.results_json.with_name('session_statistics.json')
    target.write_text(json.dumps(summarize(json.loads(args.results_json.read_text(encoding='utf-8'))),indent=2),encoding='utf-8')
    print(target)
