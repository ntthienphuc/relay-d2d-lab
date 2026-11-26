"""Predeclared, independent-seed validation of a simple EE/QoS selector.

This is a course extension of the SISO HD model, not a NOMA paper reproduction.
No hardware energy measurement is inferred from the configured costs.
"""
import csv
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from sim.model import Config,evaluate
OUT=ROOT/'results/selection_study';OUT.mkdir(parents=True,exist_ok=True)
profiles=[('low_processing',0.05,0.02),('reference',0.2,0.1),('high_processing',1.0,0.4)]
plan={'train_samples':100000,'validation_samples':1000000,'train_seed':20261125,'validation_seeds':[20261126,20261127,20261128],
      'snr_db':list(range(-10,31,2)),'qos':.1,'profiles':profiles,'predeclared':True,
      'scope':'SISO HD Rayleigh, modeled energy only; independent validation seeds; no claimed new algorithm'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
records=[];max_error=0
for name,processing,csi in profiles:
    common=dict(processing_mj=processing,csi_mj=csi,qos=plan['qos'])
    train=evaluate(Config(samples=plan['train_samples'],seed=plan['train_seed'],**common))
    for seed in plan['validation_seeds']:
        valid=evaluate(Config(samples=plan['validation_samples'],seed=seed,**common))
        for a,b in zip(train['rows'],valid['rows']):
            max_error=max(max_error,abs(b['modes']['DF']['outage']-b['df_closed']))
            choices={'Fixed DF':'DF','Fixed AF-FG':'AF-FG','Fixed AF-VG':'AF-VG','Outage only':a['outage_choice'],'EE + QoS':a['selected']}
            for policy,mode in choices.items():
                m=b['modes'].get(mode)
                records.append({'profile':name,'seed':seed,'snr_db':b['snr_db'],'policy':policy,'selected':mode,
                    'feasible_in_training':mode!='INFEASIBLE','outage_validation':m['outage'] if m else None,
                    'outage_ci95_validation':m['ci95'] if m else None,'bits_per_joule_validation':m['bits_per_joule'] if m else None,
                    'qos_exceeded_validation':m['outage']>plan['qos'] if m else None})
    print(name,'done',flush=True)
result={'plan':plan,'records':records,'df_mc_closed_max_abs_error':max_error,
        'interpretation':'INFEASIBLE means abstention, never zero outage. Validation does not guarantee QoS under shifted channels. Costs are assumptions; report both gains and losses.'}
(OUT/'holdout_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
with (OUT/'holdout_metrics.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors={'Fixed DF':'#237a61','Fixed AF-FG':'#ce8b32','Fixed AF-VG':'#627bb2','Outage only':'#985b96','EE + QoS':'#142e3d'}
fig,axes=plt.subplots(1,3,figsize=(14,4.3),sharey=True)
for ax,(profile,_,_) in zip(axes,profiles):
    for policy,color in colors.items():
        xs=[];ys=[]
        for snr in plan['snr_db']:
            values=[r['bits_per_joule_validation'] for r in records if r['profile']==profile and r['policy']==policy and r['snr_db']==snr and r['feasible_in_training']]
            xs.append(snr);ys.append(np.mean(values)/1000 if values else np.nan)
        ax.plot(xs,ys,label=policy,color=color,linewidth=2 if policy=='EE + QoS' else 1.2,marker='o' if policy=='EE + QoS' else None,markersize=3)
    ax.set_title(profile.replace('_',' '));ax.set_xlabel('Reference SNR (dB)');ax.grid(alpha=.15)
axes[0].set_ylabel('Useful kbit / modeled joule')
handles,labels=axes[-1].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=5,frameon=False)
fig.suptitle('Independent-seed validation: selection from 100k samples; evaluation on 3 x 1M samples')
fig.tight_layout(rect=(0,.1,1,.92))
for ext in ['png','pdf']:fig.savefig(OUT/f'heldout_selection.{ext}',dpi=180)
plt.close(fig)
print(json.dumps({'records':len(records),'df_closed_error':max_error,'output':str(OUT)}))
