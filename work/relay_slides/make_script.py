"""Create the speaker script PDF and editable HTML from the deck's actual notes."""
from pathlib import Path
import json
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'outputs'/'relay_presentation'
M=json.loads((HERE/'deck_manifest.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold',r'C:\Windows\Fonts\arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold')
W,H=A4
styles={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=11.5,leading=17,textColor=colors.HexColor('#172D3B')),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=9.2,leading=13,textColor=colors.HexColor('#4B6170')),
 'title':ParagraphStyle('title',fontName='Arial-Bold',fontSize=20,leading=26),
 'label':ParagraphStyle('label',fontName='Arial-Bold',fontSize=11,leading=16),
}

def para(c,text,x,y,w,style='body'):
    p=Paragraph(escape(text).replace('\n','<br/>'),styles[style]);_,height=p.wrap(w,1000)
    p.drawOn(c,x,y-height)
    return y-height

target=OUT/'Loi_thuyet_trinh_Relay_D2D.pdf'
c=canvas.Canvas(str(target),pagesize=A4)
c.setTitle('Lời thuyết trình Relay D2D theo từng slide')
c.setAuthor('Relay Lab')
for i,s in enumerate(M['slides'],1):
    c.bookmarkPage(f'slide{i}');c.addOutlineEntry(f'{i:02d} {s["title"]}',f'slide{i}',0)
    y=H-45
    y=para(c,f'Slide {i:02d}  {s["title"]}',43,y,W-86,'title')-8
    y=para(c,f'Thời lượng gợi ý {s["time"]} giây' + ('  •  Phụ lục' if i>=27 else ''),43,y,W-86,'small')-13
    image_h=(W-86)*720/1280
    c.drawImage(str(HERE/'renders'/f'slide-{i:02d}.png'),43,y-image_h,W-86,image_h,mask='auto');y-=image_h+17
    y=para(c,'LỜI NÓI GỢI Ý',43,y,W-86,'label')-6
    y=para(c,s['say'],43,y,W-86)-14
    y=para(c,'CHỈ VÀO HÌNH',43,y,W-86,'label')-4
    y=para(c,s['point'],43,y,W-86,'small')-10
    y=para(c,'CẦN NHỚ',43,y,W-86,'label')-4
    y=para(c,s['key'],43,y,W-86,'small')
    if y<46: raise ValueError(f'Page {i} too full: {y}')
    c.setFont('Arial',9);c.setFillColor(colors.HexColor('#607583'))
    c.drawString(43,24,'Relay D2D  •  Script để luyện nói, không cần đọc nguyên văn')
    c.drawRightString(W-43,24,str(i));c.showPage()

# Additional rehearsal help, on a readable single page.
y=H-45;y=para(c,'Câu hỏi thường gặp',43,y,W-86,'title')-18
for question,answer in M['qa']:
    y=para(c,question,43,y,W-86,'label')-3
    y=para(c,answer,43,y,W-86,'small')-13
if y<42:raise ValueError('Q&A page overflow')
c.setFont('Arial',9);c.drawRightString(W-43,24,'31');c.showPage()
y=H-45;y=para(c,'Cách chuẩn bị và chạy demo',43,y,W-86,'title')-20
for title,body in [
 ('Trước buổi trình bày','Mở START_LAB.cmd trong relay_d2d_lab. Cài APK trên hai Android. Cùng mạng LAN, nhập IP laptop hiện tại, chọn RELAY và DESTINATION. Giữ app ở phía trước. Kiểm tra log của một phiên ngắn trước khi bắt đầu.'),
 ('Bản nói 20 đến 25 phút','Dùng slide 1 đến 26. Slide 27 đến 30 là phụ lục, mở khi cần. Nói nguyên lý trước, sau đó mở giao diện. Các mốc thời gian chỉ là gợi ý; không cần đọc hết từng câu.'),
 ('Bản nói 12 đến 15 phút','Dùng các slide 1, 2, 3, 6, 7, 9, 11, 12, 17, 21, 23, 25, 26. Giữ các trang code để trả lời câu hỏi. Nếu thầy yêu cầu NOMA, thêm slide 19 và 20.'),
 ('Chạy code minh họa','Mở thư mục code. Cài NumPy bằng python -m pip install -r requirements.txt nếu môi trường chưa có. Chạy lần lượt packet_walkthrough.py, af_df_symbols.py, noma_sic.py và monte_carlo_outage.py. Các file JSON chứa kết quả tái lập.'),
 ('Nếu thiết bị thứ hai chưa chạy','Dùng pilot một Android: laptop vừa là S vừa là D. Hoặc mở log REPLAY đã ghi. Nêu đúng cấu hình, không trình bày phát lại như phép đo LIVE.'),
 ('Thuật ngữ nên nói rõ','Giải mã ở DF là khôi phục dữ liệu/mã kênh, khác với giải mã bảo mật. BER đo lỗi bit. Lỗi khung tính cả khung không được giao đúng. Outage xét không đạt tốc độ trong mô hình. PDR xét gói nhận được trong phép đo mạng.')]:
    y=para(c,title,43,y,W-86,'label')-5;y=para(c,body,43,y,W-86,'body')-15
if y<42:raise ValueError('Guide page overflow')
c.setFont('Arial',9);c.drawRightString(W-43,24,'32');c.showPage();c.save()

html=['<!doctype html><html lang="vi"><meta charset="utf-8"><title>Lời thuyết trình Relay D2D</title><style>body{font:18px/1.7 Arial,sans-serif;color:#172d3b;max-width:900px;margin:40px auto;padding:0 24px;background:#fbfcfc}h1{font-size:32px}h2{font-size:25px;margin-top:45px}small{color:#607583}section{border-top:1px solid #d4dfe4;padding:20px 0}nav{columns:2}a{color:#087f72}pre{white-space:pre-wrap;font-size:16px} @media print{nav{display:none}section{break-inside:avoid}body{font-size:12pt}}</style><h1>Lời thuyết trình Relay D2D</h1><p>30 slide, lời thoại và gợi ý chỉ vào hình. Trình bày chính: slide 1–26. Phụ lục: slide 27–30. Có thể chỉnh trực tiếp nội dung HTML hoặc dùng Speaker Notes trong PowerPoint.</p><nav>']
for i,s in enumerate(M['slides'],1):html.append(f'<p><a href="#s{i}">{i:02d}. {escape(s["title"])}</a></p>')
html.append('</nav>')
for i,s in enumerate(M['slides'],1):
    html.append(f'<section id="s{i}"><h2>{i:02d}. {escape(s["title"])}</h2><small>Gợi ý {s["time"]} giây</small><p>{escape(s["say"])}</p><p><b>Chỉ vào hình:</b> {escape(s["point"])}</p><p><b>Cần nhớ:</b> {escape(s["key"])}</p>')
    for k in s['refs']:html.append(f'<small>{escape(M["sources"][k])}</small><br>')
    html.append('</section>')
html.append('<h2>Câu hỏi thường gặp</h2>')
for q,a in M['qa']:html.append(f'<p><b>{escape(q)}</b><br>{escape(a)}</p>')
html.append('</html>');(OUT/'Loi_thuyet_trinh_Relay_D2D.html').write_text('\n'.join(html),encoding='utf-8')

doc=pdfium.PdfDocument(str(target));render_dir=HERE/'script_renders';render_dir.mkdir(exist_ok=True)
for i in range(len(doc)):doc[i].render(scale=1.25).to_pil().save(render_dir/f'page-{i+1:02d}.png')
print(json.dumps({'pdf':str(target),'pages':len(doc),'html':'Loi_thuyet_trinh_Relay_D2D.html'},ensure_ascii=False))
