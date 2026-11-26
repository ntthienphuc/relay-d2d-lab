"""Independent replay of the ESP32 teaching experiment against raw /compare results."""
import json
from pathlib import Path
import numpy as np

def check(path):
    result=json.loads(Path(path).read_text("utf8"))
    n=result["samples"]
    assert n==result["done"]==32768 and result["seed"]==20261126
    state=result["seed"]
    samples=[]
    for _ in range(3*n):
        state=state*48271%2147483647
        samples.append(state/2147483647)
    u,v,w=-np.log(np.array(samples).reshape(n,3).T)
    assert [r["snr_db"] for r in result["rows"]]==[0,8,16]
    for row in result["rows"]:
        rho=10**(row["snr_db"]/10)
        hop=rho*result["x"]**(-result["alpha"])
        a,b=hop*u,hop*v
        rate=result["rate"]
        values={"Direct":np.log2(1+rho*w),"DF":.5*np.log2(1+np.minimum(a,b)),
                "AF-FG":.5*np.log2(1+a*b/(1+b+hop)),"AF-VG":.5*np.log2(1+a*b/(1+a+b))}
        counted={name:int(np.count_nonzero(x<rate)) for name,x in values.items()}
        assert counted==row["failures"],(row["snr_db"],counted,row["failures"])
        assert abs(row["df_closed"]+np.expm1(-(2**(2*rate)-1)*2/hop))<1e-6
    print("ESP32 model replay: exact outage counts at all three SNRs for all four schemes.")

if __name__=="__main__":
    check(Path(__file__).resolve().parents[1]/"results/internet_26/board-model.json")

