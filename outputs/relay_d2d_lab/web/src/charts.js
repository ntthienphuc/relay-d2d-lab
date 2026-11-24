const NS='http://www.w3.org/2000/svg';
function el(tag,attrs={},text=''){const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text)n.textContent=text;return n;}

export function outageChart(container,result,palette,snr){
  if(!result)return;
  const W=600,H=175,L=44,R=12,T=10,B=26,w=W-L-R,h=H-T-B;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Outage theo SNR, Monte Carlo và công thức DF'});
  const floor=1/result.config.samples;
  const bottom=Math.max(-6,Math.floor(Math.log10(floor)));
  const x=v=>L+(v+10)/40*w,y=v=>T+Math.log10(Math.max(v,10**bottom))/bottom*h;
  for(let p=0;p>=bottom;p--){const yy=y(10**p);svg.append(el('line',{x1:L,x2:W-R,y1:yy,y2:yy,stroke:'#22364b','stroke-width':1}));svg.append(el('text',{x:L-7,y:yy+3,fill:'#7892ad','font-size':9,'text-anchor':'end'},p===0?'1':`10${['⁰','⁻¹','⁻²','⁻³','⁻⁴','⁻⁵','⁻⁶'][-p]}`));}
  for(let v=-10;v<=30;v+=10)svg.append(el('text',{x:x(v),y:H-8,fill:'#7892ad','font-size':9,'text-anchor':'middle'},`${v}`));
  svg.append(el('text',{x:W-8,y:H-8,fill:'#7892ad','font-size':9,'text-anchor':'end'},'dB'));
  svg.append(el('line',{x1:x(snr),x2:x(snr),y1:T,y2:T+h,stroke:'#5e809b','stroke-dasharray':'3 4'}));
  for(const[mode,color]of Object.entries(palette)){
    const rows=result.rows;
    const band=rows.map(r=>`${x(r.snr_db)},${y(r.modes[mode].ci95[1])}`).concat([...rows].reverse().map(r=>`${x(r.snr_db)},${y(r.modes[mode].ci95[0])}`));
    svg.append(el('polygon',{points:band.join(' '),fill:color,opacity:.09}));
    svg.append(el('polyline',{points:rows.map(r=>`${x(r.snr_db)},${y(r.modes[mode].outage)}`).join(' '),fill:'none',stroke:color,'stroke-width':1.8}));
    for(const r of rows){const v=r.modes[mode].outage;svg.append(el('circle',{cx:x(r.snr_db),cy:y(v),r:v===0?2.8:1.7,fill:v===0?'#0b1726':color,stroke:color,'stroke-width':1}));}
  }
  svg.append(el('polyline',{points:result.rows.map(r=>`${x(r.snr_db)},${y(r.df_closed)}`).join(' '),fill:'none',stroke:'#213547','stroke-dasharray':'4 4','stroke-width':1.1}));
  container.replaceChildren(svg);
}

export function packetChart(container,events,sent){
  const svg=el('svg',{viewBox:'0 0 600 175',role:'img','aria-label':'Các sự kiện nhận và chuyển tiếp của 50 gói gần nhất'});
  const rows={send:0,relay_receive:1,forward:2,receive:3,ack:4};
  const labels=['S gửi','R nhận','R chuyển','D nhận','S ACK'];
  const last=Math.max(49,sent-1),first=Math.max(0,last-49);
  for(let i=0;i<5;i++){
    const yy=19+i*28;
    svg.append(el('text',{x:55,y:yy+3,'text-anchor':'end',fill:'#8fa4bc','font-size':10},labels[i]));
    svg.append(el('line',{x1:65,x2:590,y1:yy,y2:yy,stroke:'#203348'}));
  }
  for(const e of events){if(!(e.type in rows)||e.seq<first||e.seq>last)continue;
    svg.append(el('rect',{x:68+(e.seq-first)/50*520,y:13+rows[e.type]*28,width:6,height:11,rx:2,fill:e.type==='ack'?'#e5c569':e.type==='receive'?'#a89dfb':'#40d9b8'}));}
  svg.append(el('text',{x:68,y:166,fill:'#7892ad','font-size':9},`Sequence ${first} → ${last} · mỗi dấu là sự kiện ghi nhận, không phải thời gian bay`));
  container.replaceChildren(svg);
}
