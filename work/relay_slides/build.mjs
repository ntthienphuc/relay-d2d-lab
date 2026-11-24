import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import {slides, sources, qa} from './content.mjs';

const ROOT=path.resolve('../..');
const OUT=path.join(ROOT,'outputs/relay_presentation');
const LAB=path.join(ROOT,'outputs/relay_d2d_lab');
const P=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#172D3B', muted:'#5B6E7D', teal:'#087F72', blue:'#3476AC', purple:'#7461A9', orange:'#B77518', red:'#B64C4A', pale:'#E3F3EE', line:'#D4DFE4', bg:'#FAFCFC'};
const mc=JSON.parse(await fs.readFile(path.join(LAB,'results/science/monte_carlo_1M.json'),'utf8'));
const bb=JSON.parse(await fs.readFile('baseband_results.json','utf8'));
const codeFile=await fs.readFile(path.join(OUT,'code/af_df_symbols.py'),'utf8');
await fs.mkdir('renders',{recursive:true});
const nativeTableSlides=[],nativeChartSlides=[];

function txt(s,str,x,y,w,h,size=26,color=C.ink,bold=false,align='left',font='Arial'){
 const t=s.shapes.add({geometry:'textbox',name:str.slice(0,54),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 t.text=str;t.text.style={typeface:font,fontSize:size,color,bold,alignment:align,verticalAlignment:'top',wrap:'square',autoFit:'none',insets:0};return t;
}
function box(s,str,x,y,w,h,fill=C.pale,color=C.ink,size=26){
 const b=s.shapes.add({geometry:'rect',name:str.slice(0,50),position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.line,width:1}});
 b.text=str;b.text.style={typeface:'Arial',fontSize:size,color,alignment:'center',verticalAlignment:'middle',autoFit:'none',insets:12};return b;
}
function arrow(s,a,b,opts={}){return s.shapes.connect(a,b,{kind:'straight',fromSide:'right',toSide:'left',line:{fill:C.teal,width:3},tail:{type:'triangle',width:'med',length:'med'},...opts});}
function line(s,x,y,w,h=0,color=C.line,dashed=false,reverse=false){return s.shapes.add({geometry:'connector',kind:'straight',position:{left:x,top:y,width:w,height:h},line:{fill:color,width:2,style:dashed?'dashed':'solid'},...(reverse?{head:{type:'triangle'}}:{})});}
function note(s,str,y=609,color=C.muted){txt(s,str,62,y,1150,50,23,color);}
function steps(s,labels,{x=62,y=255,w=220,h=105,gap=55,colors=[]}={}){
 const nodes=labels.map((t,i)=>box(s,t,x+i*(w+gap),y,w,h,colors[i]||C.pale));
 nodes.slice(1).forEach((n,i)=>arrow(s,nodes[i],n)); return nodes;
}
function code(s,str,x=66,y=190,w=800,h=355,size=25){
 const b=box(s,'',x-12,y-12,w+24,h+24,'#F0F4F6');
 txt(s,str,x,y,w,h,size,C.ink,false,'left','Consolas');return b;
}
function table(s,values,widths,y=200,h=350,size=25){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:62,top:y,width:1156,height:h,columnWidths:widths,values});
 t.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E7F1EF':'#FFFFFF';cell.text.style={typeface:'Arial',fontSize:size,color:C.ink,bold:r===0,verticalAlignment:'middle',insets:12};
 }
 nativeTableSlides.push(P.slides.items.length);return t;
}
function chart(s,series,categories,{x=62,y=185,w=840,h=380,ytitle='Tỷ lệ',ymax=1,yformat='0%',xtitle='SNR (dB)'}={}){
 series=series.map(row=>({...row,smooth:false,values:row.values.map(v=>Number(v.toFixed(10)))}));
 const ch=s.charts.add('line',{position:{left:x,top:y,width:w,height:h},categories,series,hasLegend:true,
  lineOptions:{smooth:false},
  legend:{position:'bottom',overlay:false,textStyle:{typeface:'Arial',fontSize:19,fill:C.ink}},
  xAxis:{title:{text:xtitle,textStyle:{typeface:'Arial',fontSize:20}},textStyle:{typeface:'Arial',fontSize:18,fill:C.muted},line:{fill:C.line,width:1}},
  yAxis:{title:{text:ytitle,textStyle:{typeface:'Arial',fontSize:20}},min:0,max:ymax,numberFormatCode:yformat,textStyle:{typeface:'Arial',fontSize:18,fill:C.muted},majorGridlines:{fill:C.line,width:1}},
  chartFill:C.bg,chartLine:{fill:'none',width:0},plotAreaFill:C.bg});
 nativeChartSlides.push(P.slides.items.length);return ch;
}
async function screenshot(s,file,x,y,w,h){const b=await fs.readFile(path.join('assets',file));s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt:'Ảnh chụp sản phẩm Relay Lab thật',fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function formula(s,str,y=465,size=34){txt(s,str,62,y,1156,70,size,C.teal,true);}

for(let i=0;i<slides.length;i++){
 const d=slides[i],s=P.slides.add();s.background.fill=C.bg;
 if(d.kind!=='cover'){
  txt(s,d.title,62,42,1156,68,42,C.ink,true);
  txt(s,d.subtitle,62,112,1156,50,24,C.muted);
 }
 line(s,62,675,1156);txt(s,'Relay Lab · Chủ đề 3',62,686,950,22,15,C.muted);txt(s,String(i+1).padStart(2,'0'),1156,682,62,28,21,C.teal,true,'right');
 s.speakerNotes.text=`LỜI THOẠI (${d.time} giây)\n${d.say}\n\nCHỈ VÀO HÌNH\n${d.point}\n\nCẦN NHỚ\n${d.key}\n\nNGUỒN\n${d.refs.map(k=>sources[k]).join('\n')||'Ví dụ giảng giải tự xây dựng.'}`;
 switch(d.kind){
 case 'cover':{
  txt(s,'MẠNG TRUYỀN THÔNG CỘNG TÁC',62,64,1100,40,23,C.teal,true);
  txt(s,d.title,62,165,1156,100,80,C.ink,true);
  txt(s,d.subtitle,66,284,1120,70,35,C.muted);
  steps(s,['S\nLaptop phát','R\nAndroid relay','D\nAndroid đích'],{y:430,w:300,h:118,gap:128,colors:[C.pale,'#E5EEF7','#EEE9F7']});
  note(s,'Nguyên lý tín hiệu, code minh họa và bằng chứng từ sản phẩm',594);break;
 }
 case 'roles':{
  const n=steps(s,['S\nNguồn dữ liệu','R\nNhận và chuyển tiếp','D\nKiểm tra và ACK'],{y:245,w:300,h:140,gap:128,colors:[C.pale,'#E5EEF7','#EEE9F7']});
  txt(s,'Laptop',62,407,300,50,27,C.teal,true,'center');txt(s,'Android 1',490,407,300,50,27,C.blue,true,'center');txt(s,'Android 2',918,407,300,50,27,C.purple,true,'center');
  txt(s,'Direct: nguồn gửi thẳng cho đích ở tầng ứng dụng',62,505,1156,48,29);
  note(s,'Pilot đã chạy: một S9+ làm R, laptop giữ cả S và D.');break;
 }
 case 'layers':{
  const top=steps(s,['Byte, sequence\nCRC, ACK','App UDP relay','Byte tới đích'],{y:210,w:300,h:105,gap:128});
  const bot=steps(s,['Mã kênh\nBPSK / QPSK','Kênh + nhiễu\nTín hiệu I/Q','Giải điều chế\nGiải mã'],{y:415,w:300,h:110,gap:128,colors:['#E5EEF7','#E5EEF7','#E5EEF7']});
  txt(s,'THIẾT BỊ THẬT',62,170,1100,30,19,C.teal,true);txt(s,'MÔ PHỎNG TẦNG TÍN HIỆU',62,373,1100,30,19,C.blue,true);
  note(s,'App Android nhận gói sau khi chip Wi-Fi đã xử lý phần vô tuyến.');break;
 }
 case 'chain':{
  const chain=steps(s,['Payload\n16 byte','Gắn CRC32\n+ 4 byte','Hamming (7,4)\n160 → 280 bit','BPSK\n280 symbol'],{y:240,w:246,h:120,gap:57});
  const a=box(s,'Kênh h và nhiễu n',320,440,640,80,'#E5EEF7');
  arrow(s,chain[3],a,{kind:'elbow',fromSide:'bottom',toSide:'right'});
  txt(s,'Bên thu làm ngược lại: bù kênh → quyết định bit → giải mã → CRC',62,560,1156,70,28);
  note(s,'Đây là PHY đơn giản để học nguyên lý; không mô phỏng đầy đủ chuẩn Wi-Fi.',630);break;
 }
 case 'bpsk':{
  txt(s,'bit 1',220,205,240,40,29,C.purple,true,'center');txt(s,'bit 0',820,205,240,40,29,C.teal,true,'center');
  line(s,160,330,960,0,C.muted);
  const points=[[-1,'−1',C.purple],[0,'0',C.muted],[1,'+1',C.teal]];
  points.forEach(([v,label,col])=>{let x=640+v*300;box(s,'',x-8,322,16,16,col);txt(s,label,x-60,355,120,46,32,col,true,'center');});
  txt(s,'Ngưỡng quyết định',490,420,300,42,24,C.muted,false,'center');
  const examples=[[-.85,280],[-1.18,285],[.76,276],[1.15,288],[-.16,275]];
  examples.forEach(([v,y],j)=>{const x=640+v*300;s.shapes.add({geometry:'ellipse',position:{left:x-7,top:y,width:14,height:14},fill:j===4?C.red:C.orange,line:{fill:'none',width:0}})});
  txt(s,'Ví dụ điểm nhận có nhiễu',62,485,1156,45,27,C.orange,true);note(s,'Sau bù kênh: real(y / h) < 0 thì quyết định bit 1.');break;
 }
 case 'df':{
  const a=box(s,'Thu yR',62,248,160,100);const b=box(s,'Giải điều chế\nGiải mã Hamming',280,248,280,100);const c=box(s,'CRC đạt?',625,248,210,100,'#E5EEF7');const e=box(s,'Mã hóa lại\nĐiều chế và phát',901,248,317,100);
  arrow(s,a,b);arrow(s,b,c);arrow(s,c,e);txt(s,'Có',846,205,60,32,23,C.teal,true);
  const drop=box(s,'Không phát khung',590,450,280,85,'#FCEBE9',C.red);arrow(s,c,drop,{fromSide:'bottom',toSide:'top',line:{fill:C.red,width:3}});txt(s,'Không',746,379,150,35,23,C.red);
  note(s,'Tín hiệu chặng hai được tái tạo từ dữ liệu vừa giải mã.');break;
 }
 case 'af':{
  steps(s,['Tín hiệu nguồn x','Kênh hSR\n+ nhiễu nR','Nhân G','Kênh hRD\n+ nhiễu nD'],{y:245,w:245,h:110,gap:58});
  formula(s,'yR = hSR x + nR        xR = G yR',425,35);
  formula(s,'yD = hRD G hSR x + hRD G nR + nD',510,32);
  note(s,'nR được khuếch đại ở relay; nD được cộng tại đích.',613);break;
 }
 case 'gain':{
  table(s,[['','AF fixed gain','AF variable gain'],['Thông tin dùng','Thống kê kênh','Kênh tức thời hSR'],['Gain trong code','√[P / (P + 1)]','√[P / (P |hSR|² + 1)]'],['Công suất relay','Chuẩn hóa trung bình','Chuẩn hóa theo kênh'],['Chi phí CSI','Ít thông tin tức thời hơn','Cần biết hSR']], [250,453,453],195,350,25);
  note(s,'Quy ước: Ps = Pr = P, E|hSR|² = 1, công suất nhiễu = 1.');break;
 }
 case 'compare':{
  table(s,[['Đặc điểm','AF','Selective DF'],['Relay xử lý','Mẫu tín hiệu I/Q','Bit và khung đã giải mã'],['Nhiễu chặng đầu','Đi theo tín hiệu phát lại','Không giữ nguyên nếu giải mã đúng'],['Chặng S–R quá yếu','Vẫn có thể phát tín hiệu xấu','Có thể loại khung tại relay'],['Chi phí xử lý','Gain và chuyển tiếp','Giải mã, kiểm tra, tái mã hóa']], [250,453,453],195,350,24);
  note(s,'So sánh trên cùng ngân sách công suất, thời gian và mục tiêu truyền.');break;
 }
 case 'duplex':{
  txt(s,'HD',62,230,120,60,39,C.teal,true);box(s,'Khe 1: S phát, R thu',210,220,470,100,C.pale);box(s,'Khe 2: R phát, D thu',704,220,470,100,'#E5EEF7');
  txt(s,'FD',62,430,120,60,39,C.purple,true);box(s,'R thu và phát đồng thời',210,410,964,100,'#EEE9F7');
  txt(s,'Tự nhiễu từ bộ phát quay vào bộ thu của R',210,535,970,48,27,C.red);
  note(s,'Mô hình hiện tại: HD. Hai luồng UDP đồng thời chưa chứng minh FD vô tuyến.');break;
 }
 case 'lan':{
  const ap=box(s,'Router / Access point',437,200,406,90,'#EEF2F4');
  const a=box(s,'Laptop S\nLAN hoặc Wi-Fi',62,410,300,115),b=box(s,'Android R\nWi-Fi',490,410,300,115,'#E5EEF7'),c=box(s,'Android D\nWi-Fi',918,410,300,115,'#EEE9F7');
  [a,b,c].forEach(n=>arrow(s,ap,n,{kind:'elbow',fromSide:'bottom',toSide:'top',line:{fill:'#9AAFB9',width:2},tail:{type:'none'}}));
  arrow(s,a,b);arrow(s,b,c);note(s,'Mũi tên xanh: đường ứng dụng. Đường xám: kết nối vật lý qua AP.');break;
 }
 case 'sequence':{
  const xs=[150,640,1130];['Nguồn S','Relay R','Đích D'].forEach((t,j)=>{txt(s,t,xs[j]-90,180,180,40,28,C.ink,true,'center');line(s,xs[j],235,0,290,C.line,true);});
  const msg=(x1,x2,y,label,col)=>{s.shapes.add({geometry:'connector',kind:'straight',position:{left:Math.min(x1,x2),top:y,width:Math.abs(x2-x1),height:0},line:{fill:col,width:3},...(x2>x1?{tail:{type:'triangle'}}:{head:{type:'triangle'}})});txt(s,label,Math.min(x1,x2)+20,y-39,Math.abs(x2-x1)-40,36,23,col,false,'center');};
  msg(150,640,280,'DATA: run, seq, CRC',C.teal);msg(640,1130,355,'DATA: hops + 1',C.teal);msg(1130,640,430,'ACK: cùng run, seq',C.purple);msg(640,150,505,'ACK về nguồn',C.purple);
  note(s,'RTT = thời điểm nguồn nhận ACK − thời điểm nguồn gửi DATA.');break;
 }
 case 'packetcode':{
  code(s,`p = Packet.decode(raw)\nif p.kind != DATA or p.hops >= 1:\n    raise ValueError("Sai loại/chặng")\nexpected = payload_for(p.run, p.seq,\n                       len(p.payload))\nif p.payload != expected:\n    raise ValueError("Payload sai")\np.hops += 1\nforwarded = p.encode()`,66,192,805,350,25);
  txt(s,'1  Kiểm tra CRC\n\n2  Kiểm tra dữ liệu\n\n3  Tăng số chặng\n\n4  Đóng gói gửi tiếp',920,210,290,340,26,C.teal);
  note(s,'File: code/packet_walkthrough.py. Socket UDP nằm trong ứng dụng Android.');break;
 }
 case 'afcode':{
  code(s,`if mode == "AF-VG":\n    gain = np.sqrt(P /\n        (P * np.abs(h_sr)**2 + 1))\nelse:  # AF-FG, E|h_sr|² = 1\n    gain = np.sqrt(P / (P + 1))\n\nx_r = gain * y_r\ny_d = h_rd * x_r + n_d`,66,192,805,350,25);
  txt(s,'y_r đã có nhiễu\n\nG nhân toàn bộ y_r\n\nĐích thêm n_d',920,220,290,300,27,C.teal);
  note(s,'File: code/af_df_symbols.py. P/N0 trên symbol BPSK đã mã hóa.');break;
 }
 case 'dfcode':{
  code(s,`decoded = receive(y_r,\n                  np.sqrt(P) * h_sr)\naccepted = crc_ok(decoded)\n\npayload = decoded[:, :-4]\nx_new = modulate(append_crc(payload))\nx_r = np.sqrt(P) * x_new\nx_r *= accepted[:, None]`,66,192,805,350,25);
  txt(s,'Khôi phục byte\n\nKiểm tra CRC\n\nTái mã hóa\n\nKhung lỗi: im lặng',920,200,290,340,26,C.teal);
  note(s,'receive gồm quyết định BPSK và giải mã Hamming; modulate gồm mã hóa + BPSK.');break;
 }
 case 'outage':{
  steps(s,['Lấy mẫu kênh','Tính SNR / tốc độ','So với R mục tiêu','Đếm outage'],{y:215,w:246,h:100,gap:57});
  formula(s,'C_DF = ½ log₂[1 + min(γSR, γRD)]',360,34);
  formula(s,'Outage khi C_DF < R       τ = 2^(2R) − 1',435,31);
  formula(s,'Pout,DF = 1 − exp[−τ(1/A + 1/B)]',510,31);
  note(s,'A, B: SNR trung bình hai chặng. Monte Carlo đếm tỷ lệ mẫu outage.');break;
 }
 case 'mcchart':{
  const rows=mc.rows.filter(r=>r.snr_db<=20);const colors=[C.muted,C.teal,C.orange,C.purple];
  const ss=['Direct','DF','AF-FG','AF-VG'].map((m,j)=>({name:m,values:rows.map(r=>r.modes[m].outage),line:{fill:colors[j],width:3},marker:{symbol:j===1?'circle':'none',size:5}}));
  ss.push({name:'DF dạng đóng',values:rows.map(r=>r.df_closed),line:{fill:C.ink,width:2,style:'dashed'},marker:{symbol:'none'}});
  chart(s,ss,rows.map(r=>String(r.snr_db)),{ytitle:'Outage',w:825,h:400});
  txt(s,'1.000.000',930,225,280,65,44,C.teal,true);txt(s,'mẫu / điểm',930,290,280,40,25,C.muted);txt(s,'0,000740',930,390,280,65,39,C.blue,true);txt(s,'Sai khác DF lớn nhất\ntrên 21 điểm đã xuất',930,450,280,90,25,C.muted);
  note(s,'R = 0,5 bit/s/Hz; relay ở giữa; pathloss exponent = 2,2; seed 20261124.');break;
 }
 case 'basebandchart':{
  const ss=['DF','AF-FG','AF-VG'].map((m,j)=>({name:m,values:bb.rows.map(r=>r.modes[m].frame_failure_rate),line:{fill:[C.teal,C.orange,C.purple][j],width:3},marker:{symbol:'circle',size:6}}));
  chart(s,ss,bb.rows.map(r=>String(r.snr_db)),{ytitle:'Tỷ lệ khung thất bại',w:825,h:400});
  txt(s,'16 byte payload\nCRC32\nHamming (7,4)\nBPSK',930,205,280,240,27,C.ink);
  txt(s,'Kể cả khung DF\nbị bỏ tại relay',930,465,280,85,26,C.red,true);
  note(s,'Kết quả mô phỏng baseband độc lập với đồ thị outage và phép đo UDP.');break;
 }
 case 'noma':{
  const a=box(s,'s₁ = ±1\nLuồng gần',62,220,260,100),b=box(s,'s₂ = ±1\nLuồng xa',62,430,260,100,'#E5EEF7');
  const w1=box(s,'× √0,2',410,220,220,100),w2=box(s,'× √0,8',410,430,220,100,'#E5EEF7');
  const sum=box(s,'+',760,320,100,100,'#EEE9F7',C.ink,48),out=box(s,'Tín hiệu x',980,320,238,100,'#EEE9F7');
  arrow(s,a,w1);arrow(s,b,w2);arrow(s,w1,sum,{kind:'elbow',toSide:'top'});arrow(s,w2,sum,{kind:'elbow',toSide:'bottom'});arrow(s,sum,out);
  note(s,'Với P = 1: x có bốn mức −1,342; −0,447; +0,447; +1,342.');break;
 }
 case 'sic':{
  steps(s,['Giải mã luồng 2','Dựng lại √0,8 s₂','Trừ khỏi y','Giải mã luồng 1'],{y:205,w:246,h:95,gap:57});
  code(s,`b2_hat = (y < 0).astype(int)\ns2_hat = 1 - 2 * b2_hat\nresidual = y - np.sqrt(0.8) * s2_hat\nb1_hat = (residual < 0).astype(int)`,66,368,800,170,26);
  txt(s,'Ví dụ không nhiễu\n\n+0,447 − 0,894\n= −0,447',920,365,290,170,27,C.teal,true);
  note(s,'Mẫu tại bộ thu gần, h = 1 đã biết; code/noma_sic.py.');break;
 }
 case 'paper':{
  steps(s,['Mô hình kênh','Biểu thức phân tích','Monte Carlo','Chọn giao thức'],{y:220,w:246,h:95,gap:57});
  txt(s,'6 tổ hợp',62,390,320,70,45,C.teal,true);txt(s,'HD/FD × DF/AF-FG/AF-VG',62,466,545,90,27);
  txt(s,'10⁶ mẫu kênh',660,390,558,70,45,C.blue,true);txt(s,'Outage, throughput, hiệu quả năng lượng',660,466,558,90,27);
  note(s,'Bản demo hiện tại dùng mô hình SISO HD đơn giản; chưa tái lập toàn bộ paper.');break;
 }
 case 'productsim':{
  await screenshot(s,'dashboard_simulation.png',62,173,856,473);
  txt(s,'Đổi SNR',954,220,264,45,29,C.teal,true);txt(s,'Quan sát kênh tốt / xấu',954,274,264,80,25);
  txt(s,'Dịch relay',954,390,264,45,29,C.teal,true);txt(s,'Xem hai chặng thay đổi',954,444,264,80,25);
  txt(s,'Ảnh màn hình sản phẩm',954,580,264,60,21,C.muted);break;
 }
 case 'productlive':{
  await screenshot(s,'dashboard_live_light.png',62,174,858,474);
  txt(s,'LIVE',956,210,260,50,35,C.teal,true);txt(s,'Gói UDP qua\nAndroid vật lý',956,275,260,100,27);
  txt(s,'Log theo sequence',956,423,260,65,28,C.blue,true);txt(s,'Nguồn, relay,\nđích và ACK',956,505,260,100,26);break;
 }
 case 'productandroid':{
  await screenshot(s,'android_light.png',75,169,330,485);
  txt(s,'1   Nhập IP laptop',475,205,720,65,31,C.ink,true);txt(s,'Địa chỉ trên mạng LAN hiện tại',525,270,670,55,26,C.muted);
  txt(s,'2   Chọn RELAY hoặc DESTINATION',475,355,720,80,30,C.ink,true);
  txt(s,'3   Khởi động và quan sát bộ đếm',475,470,720,80,30,C.ink,true);
  txt(s,'Ảnh chụp S9+; máy thứ hai dùng cùng APK.',475,588,720,60,23,C.muted);break;
 }
 case 'evidence':{
  table(s,[['Điều kiện / kết quả','Pilot relay 50 giây'],['Topology','Laptop S → S9+ R → Laptop D'],['Tải phát','20 gói/s, payload 128 byte'],['Gửi / xác nhận đích','1.000 / 1.000'],['RTT trung bình / p95','14,21 ms / 21,62 ms'],['Thử dừng relay riêng','60 gói bị bỏ trong 3 giây']], [450,706],185,385,26);
  note(s,'Một phiên chức năng; chưa kết luận về hai Android đồng thời hoặc vùng phủ.');break;
 }
 case 'demo':{
  const items=[['00:00','Chỉ ba vai trò và kiểm tra thiết bị online'],['00:30','Chạy qua relay, mở chi tiết một sequence'],['01:10','Tạm dừng relay rồi cho chuyển tiếp lại'],['01:50','Đổi SNR ở mô phỏng, giải thích AF/DF'],['02:40','Mở log đã lưu và nêu giới hạn phép thử']];
  items.forEach((r,j)=>{const y=195+j*78;txt(s,r[0],62,y,160,50,30,C.teal,true);txt(s,r[1],250,y,968,62,29);if(j<4)line(s,250,y+65,968);});
  note(s,'Dự phòng: dùng pilot một Android hoặc REPLAY, giữ đúng nhãn nguồn dữ liệu.',622);break;
 }
 case 'coverage':{
  steps(s,['Router\nWi-Fi A','Android R\nSTA + hotspot','Android D\nWi-Fi B'],{y:240,w:300,h:125,gap:128,colors:[C.pale,'#E5EEF7','#EEE9F7']});
  txt(s,'Đối chứng: giữ nguyên vị trí D, đổi điểm kết nối',62,440,1156,60,32,C.ink,true);
  txt(s,'Phiên 1: D nối router       Phiên 2: D nối hotspot của R',62,518,1156,60,28);
  note(s,'Chưa kiểm chứng STA/AP trên thiết bị hiện có; cần kiểm tra subnet và routing.');break;
 }
 case 'extension':{
  const n=steps(s,['Ước tính outage\nvà CI 95%','Giữ giao thức\nđạt ngưỡng QoS','So bit hữu ích/J\ntheo mô hình'],{y:230,w:300,h:120,gap:128});
  const bad=box(s,'Không có giao thức đạt: báo không khả thi',350,455,710,90,'#FCEBE9',C.red);arrow(s,n[1],bad,{fromSide:'bottom',toSide:'top',line:{fill:C.red,width:2}});
  note(s,'Bước nghiên cứu tiếp: seed độc lập, sai số CSI, chi phí chuyển giao thức.');break;
 }
 case 'qa':{
  table(s,[['Thầy có thể hỏi','Câu trả lời ngắn'],[qa[0][0],qa[0][1]],[qa[2][0],qa[2][1]],[qa[3][0],qa[3][1]],[qa[5][0],qa[5][1]]],[470,686],190,390,24);
  note(s,'Script đi kèm có thêm câu hỏi và cách trả lời.');break;
 }
 case 'references':{
  const list=[['[1] Cooperative NOMA, AF/DF, HD/FD','Tran & Voznak, Sensors 2019. DOI: 10.3390/s19081845'],['[2] AF/DF thực nghiệm trên SDR','Electronics 2021. DOI: 10.3390/electronics10050570'],['[3] Android D2D nhiều chặng','Oide et al., Sensors 2018. DOI: 10.3390/s18030776'],['[4] NOMA và SIC qua sóng thật','Qi et al., IEEE Access 2021. DOI: 10.1109/ACCESS.2021.3116613'],['[5] Android STA/AP concurrency','source.android.com/docs/core/connect/wifi-sta-ap-concurrency']];
  list.forEach((r,j)=>{let y=179+j*83;txt(s,r[0],62,y,1156,37,26,C.ink,true);txt(s,r[1],62,y+39,1156,35,22,C.muted);});
  note(s,'Mã mẫu và lời thoại theo từng slide nằm trong gói trình bày.',620);break;
 }
 }
}

const manifest={title:'Relay D2D — Nguyên lý và demo Android',slide_count:slides.length,main_slides:26,appendix_slides:[27,28,29,30],sources,slides,qa,nativeTableSlides,nativeChartSlides};
await fs.writeFile('deck_manifest.json',JSON.stringify(manifest,null,2),'utf8');
await (await PresentationFile.exportPptx(P)).save('candidate.pptx');
console.log('PPTX exported');
for(let i=0;i<P.slides.items.length;i++){
 const s=P.slides.items[i];const blob=await P.export({slide:s,format:'png',scale:1});
 await fs.writeFile(`renders/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await blob.arrayBuffer()));
 await fs.writeFile(`renders/slide-${String(i+1).padStart(2,'0')}.json`,await (await s.export({format:'layout'})).text());
 console.log(`rendered ${i+1}/${slides.length}`);
}
await fs.writeFile('presentation.json',JSON.stringify(P.toProto()));
console.log(JSON.stringify({slides:slides.length,nativeTableSlides,nativeChartSlides}));
