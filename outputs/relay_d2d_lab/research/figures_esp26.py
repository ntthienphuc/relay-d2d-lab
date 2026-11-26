"""Rebuild the 2.6 system diagram and empirical RTT figure from the two archived runs."""
from pathlib import Path
import argparse
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import PercentFormatter
import numpy as np

LAB = Path(__file__).resolve().parents[1]
RUNS = (405451643, 405462659)
plt.rcParams.update({"font.family":"DejaVu Sans","pdf.fonttype":42,"svg.fonttype":"none"})

def topology(output, slide):
    ink, accent = ("#303128", "#9e411f") if slide else ("0.1", "0.27")
    fig, ax = plt.subplots(figsize=(10.1, 2.72))
    fig.subplots_adjust(left=.008,right=.992,bottom=.025,top=.98)
    ax.set(xlim=(0,12),ylim=(0,3));ax.axis("off")
    nodes=[(.05,2.66,"C","Đích · tầng 3"),(4.32,2.97,"B · ESP32","Relay · tầng 2"),(9.31,2.62,"Router","Wi-Fi · tầng 1")]
    for x,w,title,subtitle in nodes:
        ax.add_patch(FancyBboxPatch((x,1.29),w,1.05,boxstyle="round,pad=0.012,rounding_size=0.095",fc="0.98",ec=ink,lw=1.3))
        ax.text(x+w/2,1.95,title,ha="center",va="center",fontsize=16,weight="bold",color=ink)
        ax.text(x+w/2,1.53,subtitle,ha="center",va="center",fontsize=11.5,color=ink)
    for x1,x2,label in ((2.74,4.29,"RelayBox"),(7.32,9.28,"Wi-Fi gốc")):
        ax.add_patch(FancyArrowPatch((x1,1.81),(x2,1.81),arrowstyle="<->",mutation_scale=13,color=accent,lw=1.8))
        ax.text((x1+x2)/2,2.08,label,ha="center",fontsize=10.7,weight="bold",color=accent)
    ax.text(1.38,.91,"192.168.50.2",ha="center",fontsize=11)
    ax.text(5.81,.91,"AP   .50.1     |     STA   .4.122",ha="center",fontsize=11)
    ax.text(10.62,.91,"192.168.4.1",ha="center",fontsize=11)
    ax.text(5.81,.28,"DHCP cấp IP cho C     ·     NAPT tại B     ·     Router đưa gói ra Internet",ha="center",fontsize=12,color=ink)
    save(fig,output,"esp_topology",slide)

def rtt(output, slide):
    fig,ax=plt.subplots(figsize=(9.2,3.15))
    fig.subplots_adjust(left=.105,right=.975,bottom=.24,top=.93)
    all_values=[]
    for index,(rid,label) in enumerate(zip(RUNS,("Laptop → Samsung","Samsung → laptop"))):
        folder=LAB/"results"/f"run_{rid}"
        rows=[json.loads(s) for s in (folder/"events.jsonl").read_text("utf8").splitlines()]
        acks={e["seq"]:e["rtt_ms"] for e in rows if e["node"]=="S" and e["type"]=="ack"}
        t=np.sort(list(acks.values()))
        assert len(t)==40
        q=np.percentile(t,95)
        assert np.isclose(q,json.loads((folder/"summary.json").read_text("utf8"))["rtt_p95_ms"])
        y=np.arange(1,len(t)+1)/len(t)
        all_values.append(t[-1])
        color=("#242720","#ad5029")[index] if slide else ("0.10","0.40")[index]
        ax.step(np.r_[0,t],np.r_[0,y],where="post",color=color,lw=2,ls=("-","--")[index],
                label=f"{label}    p95 {q:.1f} ms".replace(".",","))
    bound=25*np.ceil(max(all_values)/25)
    ax.set(xlim=(0,bound),ylim=(0,1.035),xlabel="RTT của gói có ACK (ms)",ylabel="Tỷ lệ tích lũy")
    ax.set_yticks([0,.25,.5,.75,1]);ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.grid(axis="y",color=".83",lw=.7);ax.spines[["top","right"]].set_visible(False)
    ax.tick_params(labelsize=11);ax.xaxis.label.set_size(12);ax.yaxis.label.set_size(12)
    ax.legend(loc="lower right",fontsize=11,frameon=True,edgecolor=".85",framealpha=1)
    save(fig,output,"esp_rtt",slide)

def save(fig,out,name,slide):
    fig.savefig(out/(name+("_slide.png" if slide else ".pdf")),dpi=250,facecolor="white")
    plt.close(fig)

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument("output",type=Path)
    target=cli.parse_args().output;target.mkdir(exist_ok=True,parents=True)
    for slide in (False,True):
        topology(target,slide);rtt(target,slide)

