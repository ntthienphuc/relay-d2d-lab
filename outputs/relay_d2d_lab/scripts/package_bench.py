"""Create a portable local delivery from named project components and bench evidence."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

LAB=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paired",type=Path)
    parser.add_argument("--acceptance",type=Path)
    args=parser.parse_args()
    paired=args.paired.resolve()
    if paired.parent!=LAB/"results":raise ValueError("Expected the project's paired result folder")
    audit=json.loads((paired/"audit.json").read_text(encoding="utf-8"))
    paths=set()
    def tree(directory):
        for file in directory.rglob("*"):
            if file.is_file() and "__pycache__" not in file.parts:paths.add(file)
    for name in ("lab","sim","web","docs","research","scripts","tests","android/src","esp32/RelayBox"):
        tree(LAB/name)
    for name in ("README.md","requirements.txt","package.json","package-lock.json","START_READY.cmd","START_LAB.cmd",
                 "android/AndroidManifest.xml","android/build/relaylab.apk","esp32/README.md"):
        paths.add(LAB/name)
    paths.update((LAB/"esp32/build/cam").glob("*.bin"))
    tree(paired)
    for name in ("selection_study","validation_v2","hardware_20261126"):
        paths.update(f for f in (LAB/"results"/name).glob("*") if f.is_file() and f.suffix in (".json",".csv",".pdf",".png",".html"))
    run_ids={r["id"] for r in audit["runs"]}
    controls=paired/"controls.json"
    if controls.exists():run_ids.update(r["id"] for r in json.loads(controls.read_text(encoding="utf-8"))["runs"])
    if args.acceptance:
        extra=args.acceptance.resolve()
        if extra.parent!=LAB/"results":raise ValueError("Expected acceptance runs in results")
        tree(extra)
        run_ids.update(r["id"] for r in json.loads((extra/"trials.json").read_text(encoding="utf-8")) if "summary" in r)
    for rid in run_ids:tree(LAB/"results"/f"run_{rid}")
    package=LAB/"release"/"Relay_Lab_2.1_CAM.zip"
    package.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(package.with_suffix(".tmp"),"w",zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        manifest={}
        def add(file,name):
            data=file.read_bytes()
            z.writestr(name,data)
            manifest[name]=hashlib.sha256(data).hexdigest()
        for file in sorted(paths):
            add(file,"Relay_Lab/"+file.relative_to(LAB).as_posix())
        slides=LAB.parent/"relay_presentation"
        for name in ("Relay_D2D_Thuyet_trinh.pptx","Loi_thuyet_trinh_Relay_D2D.pdf"):
            add(slides/name,"Presentation/"+name)
        z.writestr("MANIFEST_SHA256.json",json.dumps(manifest,indent=2))
    with zipfile.ZipFile(package.with_suffix(".tmp")) as z:
        for name,digest in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest()==digest
    package.with_suffix(".tmp").replace(package)
    print(package,len(manifest),hashlib.sha256(package.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
