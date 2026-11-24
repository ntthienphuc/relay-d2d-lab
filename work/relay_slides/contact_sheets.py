from PIL import Image
from pathlib import Path
root=Path(__file__).resolve().parent
for folder,prefix,w,h,cols,rows in [('script_renders','page-',372,526,4,2),('powerpoint_renders','Slide',640,360,2,3)]:
    source=root/folder
    files=list(source.glob('*.png'))
    def num(p):
        return int(''.join(c for c in p.stem if c.isdigit()))
    files.sort(key=num)
    out=root/(folder+'_contacts');out.mkdir(exist_ok=True)
    for k in range(0,len(files),cols*rows):
        canvas=Image.new('RGB',(w*cols,h*rows),'white')
        for j,f in enumerate(files[k:k+cols*rows]):
            im=Image.open(f);im.thumbnail((w,h))
            canvas.paste(im,((j%cols)*w,(j//cols)*h))
        canvas.save(out/f'pages-{k+1:02d}.jpg')
    print(folder,len(files))
