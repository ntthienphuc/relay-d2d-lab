const NS='http://www.w3.org/2000/svg';
function el(tag,attrs={},text=''){const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text)n.textContent=text;return n;}

export function outageChart(container,result,palette,snr){
  if(!result)return;
  const W=600,H=175,L=44,R=12,T=10,B=26,w=W-L-R,h=H-T-B;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Outage theo SNR, Monte Carlo và công thức DF'});
  const floor=1/result.config.samples;
  const bottom=Math.max(-6,Math.floor(Math.log10(floor)));
  const x=v=>L+(v+10)/40*w,y=v=>T+Math.log10(Math.max(v,10**bottom))/bottom*h;
  for(let p=0;p>=bottom;p--){const yy=y(10**p);svg.append(el('line',{x1:L,x2:W-R,y1:yy,y2:yy,stroke:'#cbd3e3','stroke-width':1}));svg.append(el('text',{x:L-7,y:yy+3,fill:'#526580','font-size':9,'text-anchor':'end'},p===0?'1':`10${['⁰','⁻¹','⁻²','⁻³','⁻⁴','⁻⁵','⁻⁶'][-p]}`));}
  for(let v=-10;v<=30;v+=10)svg.append(el('text',{x:x(v),y:H-8,fill:'#526580','font-size':9,'text-anchor':'middle'},`${v}`));
  svg.append(el('text',{x:W-8,y:H-8,fill:'#526580','font-size':9,'text-anchor':'end'},'dB'));
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
