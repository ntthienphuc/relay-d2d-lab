"""Render the outage comparison reported by RelayBox /compare."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def plot(board_path, target):
    report=json.loads(board_path.read_text("utf8"))
    rows=report["rows"];x=[r["snr_db"] for r in rows];n=report["samples"]
    plt.rcParams.update({"font.family":"DejaVu Sans","pdf.fonttype":42})
    for slide in (False,True):
        fig,ax=plt.subplots(figsize=(8.9,3.32))
        fig.subplots_adjust(left=.105,right=.72,bottom=.22,top=.91)
        modes=("Direct","DF","AF-FG","AF-VG")
        for i,(mode,marker,ls) in enumerate(zip(modes,("o","s","^","D"),("-","--","-.",":"))):
            y=[100*r["failures"][mode]/n for r in rows]
            color=(("#38474c","#955530","#444b3f","#a34724") if slide else ("0.12",".28",".42",".53"))[i]
            ax.semilogy(x,y,marker=marker,ls=ls,color=color,ms=7,mfc="white",lw=1.6,label=mode)
        ax.semilogy(x,[100*r["df_closed"] for r in rows],ls="none",marker="x",ms=9,mew=1.5,color=".12",label="DF dạng đóng")
        ax.set(xticks=x,xlim=(-.6,16.6),xlabel="SNR tham chiếu (dB)",ylabel="Xác suất outage (%)",ylim=(.65,100))
        ax.set_yticks([1,3,10,30,100],labels=["1","3","10","30","100"])
        ax.grid(axis="y",which="major",color=".84",lw=.7);ax.spines[["right","top"]].set_visible(False)
        ax.tick_params(labelsize=12);ax.xaxis.label.set_size(12);ax.yaxis.label.set_size(12)
        ax.legend(loc="center left",bbox_to_anchor=(1.04,.54),fontsize=11.5,frameon=False)
        fig.savefig(target/("board_model_slide.png" if slide else "board_model.pdf"),dpi=255)
        plt.close(fig)

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument("output",type=Path);args=cli.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    plot(Path(__file__).resolve().parents[1]/"results/internet_26/board-model.json",args.output)

