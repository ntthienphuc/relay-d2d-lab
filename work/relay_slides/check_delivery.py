from pathlib import Path
import json,zipfile,hashlib
from xml.etree import ElementTree as ET
from pypdf import PdfReader

root=Path(__file__).resolve().parents[2]
out=root/'outputs/relay_presentation'
manifest=json.loads((root/'work/relay_slides/deck_manifest.json').read_text(encoding='utf-8'))
presentation=out/'Relay_D2D_Thuyet_trinh.pptx'
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(presentation) as z:
    slide_names=[x for x in z.namelist() if x.startswith('ppt/slides/slide') and x.endswith('.xml')]
    notes=[x for x in z.namelist() if x.startswith('ppt/notesSlides/notesSlide') and x.endswith('.xml')]
    assert len(slide_names)==30 and len(notes)==30
    for i,s in enumerate(manifest['slides'],1):
        slide=ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        note=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
        st=''.join(e.text or '' for e in slide.findall('.//a:t',ns))
        nt=''.join(e.text or '' for e in note.findall('.//a:t',ns))
        assert s['title'] in st,(i,'title')
        assert s['say'] in nt,(i,'speaker script')
    charts=[x for x in z.namelist() if '/charts/chart' in x and x.endswith('.xml')]
    embeds=[x for x in z.namelist() if x.startswith('ppt/embeddings/')]
    assert len(charts)==2 and len(embeds)>=2
pdf=PdfReader(out/'Loi_thuyet_trinh_Relay_D2D.pdf')
assert len(pdf.pages)==32
for i,s in enumerate(manifest['slides']):
    text=pdf.pages[i].extract_text()
    assert 'LỜI NÓI GỢI Ý' in text and s['say'][:30] in text,(i,'pdf script')
    assert '\ufffd' not in text
files=[p for p in out.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
receipt={'slide_count':30,'notes_count':30,'pdf_pages':32,'editable_charts':2,'chart_workbooks':len(embeds),'scope':'One physical Android pilot; two Android simultaneously not verified; baseband and NOMA are software-only.',
         'files':{str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
(root/'work/relay_slides/delivery_check.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='files'},ensure_ascii=False))
