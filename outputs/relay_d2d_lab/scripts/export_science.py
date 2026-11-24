"""Reproducible scientific artifacts; run from project root."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sim.model import Config,evaluate

out=Path(__file__).resolve().parents[1]/'results'/'science'
out.mkdir(exist_ok=True)
result=evaluate(Config(samples=1000000))
(out/'monte_carlo_1M.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
rows=result['rows'];x=[r['snr_db'] for r in rows]
colors={'Direct':'#6a788a','DF':'#00826d','AF-FG':'#bf6d08','AF-VG':'#5e5aca'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
fig,ax=plt.subplots(1,2,figsize=(11,4.1))
for m,c in colors.items():
    y=np.array([r['modes'][m]['outage'] for r in rows])
    lo=np.array([r['modes'][m]['ci95'][0] for r in rows]);hi=np.array([r['modes'][m]['ci95'][1] for r in rows])
    ax[0].semilogy(x,np.maximum(y,1e-6),'.-',color=c,label=m,markersize=4)
    ax[0].fill_between(x,np.maximum(lo,1e-6),hi,color=c,alpha=.13)
    ax[1].plot(x,[r['modes'][m]['throughput_bps_hz'] for r in rows],color=c,label=m)
ax[0].semilogy(x,[r['df_closed'] for r in rows],'k--',lw=1,label='DF closed form')
ax[0].set(xlabel='Reference SNR (dB)',ylabel='Outage probability',ylim=(1e-6,1),title='Independent fading events vs. closed form')
ax[1].set(xlabel='Reference SNR (dB)',ylabel='Useful throughput (bit/s/Hz)',title='Equal frame duration and expected TX energy')
for a in ax:a.grid(alpha=.22,which='both');a.legend(fontsize=8)
fig.suptitle('HD relay | Rayleigh | target 0.5 bit/s/Hz | 1,000,000 blocks / point',fontsize=11)
fig.tight_layout();fig.savefig(out/'outage_throughput.png');fig.savefig(out/'outage_throughput.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(6.5,4))
for m,c in colors.items():ax.plot(x,[r['modes'][m]['bits_per_joule']/1000 for r in rows],label=m,color=c)
ax.set(xlabel='Reference SNR (dB)',ylabel='Expected useful kbit/J',title='Illustrative energy model — not hardware measurements')
ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'energy_model.png');fig.savefig(out/'energy_model.pdf');plt.close(fig)
costs=np.linspace(0,1.5,16);grid=[];codes={'INFEASIBLE':0,'DF':1,'AF-FG':2,'AF-VG':3}
for cost in costs:
    landscape=evaluate(Config(samples=100000,seed=81773,processing_mj=float(cost)))
    grid.append([codes[r['selected']] for r in landscape['rows']])
from matplotlib.colors import ListedColormap,BoundaryNorm
fig,ax=plt.subplots(figsize=(7,4))
cmap=ListedColormap(['#e4e8ed',colors['DF'],colors['AF-FG'],colors['AF-VG']])
im=ax.imshow(grid,aspect='auto',origin='lower',extent=[-11,31,-.05,1.55],cmap=cmap,norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4))
bar=fig.colorbar(im,ax=ax,ticks=[0,1,2,3]);bar.ax.set_yticklabels(['Infeasible','DF','AF-FG','AF-VG'])
ax.set(xlabel='Reference SNR (dB)',ylabel='DF processing energy (mJ/frame)',title='Relay selection: maximize modeled bit/J, outage CI upper <= 10%')
fig.tight_layout();fig.savefig(out/'selection_map.png');fig.savefig(out/'selection_map.pdf');plt.close(fig)
with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f);writer.writerow(['snr_db','mode','outage','ci_low','ci_high','throughput_bps_hz','energy_mj','bits_per_joule','selection'])
    for r in rows:
        for m,v in r['modes'].items():writer.writerow([r['snr_db'],m,v['outage'],*v['ci95'],v['throughput_bps_hz'],v['energy_mj'],v['bits_per_joule'],r['selected']])
print(json.dumps({'folder':str(out),'samples_per_point':result['config']['samples'],'points':len(rows),'files':[p.name for p in out.iterdir()]}))

