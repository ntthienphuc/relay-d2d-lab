from pathlib import Path
import zipfile, json, hashlib
root=Path(__file__).resolve().parents[2]
out=root/'outputs'/'relay_presentation'
target=out/'Relay_D2D_Tron_bo.zip'
files=[p for p in out.rglob('*') if p.is_file() and p.suffix!='.zip' and '__pycache__' not in p.parts]
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
    for p in files:z.write(p,p.relative_to(out))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert 'Relay_D2D_Thuyet_trinh.pptx' in z.namelist()
    assert 'code/af_df_symbols.py' in z.namelist()
    for p in files:assert z.read(str(p.relative_to(out)).replace('\\','/'))==p.read_bytes()
print(json.dumps({'zip':str(target),'files':len(files),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},ensure_ascii=False))
