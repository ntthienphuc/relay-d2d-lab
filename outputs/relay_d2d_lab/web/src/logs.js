import {state} from './state.js';
import {api} from './api.js';
const $=id=>document.getElementById(id);
let selected=null,packets=[],lastRun=null,busy=false;
const names={send:'Nguồn gửi DATA',relay_receive:'Relay nhận & kiểm tra',forward:'Relay chuyển tiếp',receive:'Đích nhận hợp lệ',ack_forward:'Relay chuyển ACK',ack:'Nguồn nhận ACK',drop_paused:'Relay đang tạm dừng',drop_injected:'Mất gói do thử nghiệm',drop_capacity:'Relay không thể chuyển gói (bộ đệm hoặc gửi UDP)',invalid:'Nút nhận loại gói không hợp lệ'};
function cell(text,cls=''){const td=document.createElement('td');td.textContent=text;td.className=cls;return td;}
function mark(ok,dropped=false){const n=cell(dropped?'×':ok?'✓':'—',dropped?'mark fail':ok?'mark success':'mark pending');return n;}
function detail(packet){
  selected=packet.seq;const panel=$('packetDetail');panel.replaceChildren();
  const label=document.createElement('span');label.className='eyebrow';label.textContent='CHI TIẾT MỘT GÓI';
  const title=document.createElement('h3');title.textContent=`#${packet.seq} · ${packet.bytes} bytes`;
  panel.append(label,title);
  const order=['send','relay_receive','forward','invalid','drop_capacity','drop_paused','drop_injected','receive','ack_forward','ack'];
  const ordered=[...packet.events].sort((a,b)=>order.indexOf(a.type)-order.indexOf(b.type));
  for(const e of ordered){const line=document.createElement('div');line.className='event-line';
    const dot=document.createElement('i');dot.className=(e.type.startsWith('drop')||e.type==='invalid')?'fail-dot':'';
    const text=document.createElement('div');const name=document.createElement('b');name.textContent=names[e.type]||e.type;
    const t=document.createElement('small');t.textContent=e.node+' · '+(e.corrupted_deliberately?'đã chủ động làm sai payload · ':'')+new Date(e.server_time*1000).toLocaleTimeString('vi-VN',{hour12:false})+' · log tại laptop';
    text.append(name,t);line.append(dot,text);panel.append(line);}
  const footer=document.createElement('p');footer.className='detail-metrics';footer.textContent=`RTT ${packet.rtt_ms==null?'—':packet.rtt_ms.toFixed(2)+' ms'} · Xử lý relay ${packet.processing_ms==null?'—':packet.processing_ms.toFixed(2)+' ms'}`;panel.append(footer);
}
function draw(){
  const filter=$('traceFilter').value;
  const rows=packets.filter(p=>filter==='ack'?p.ack:filter==='missing'?(!p.ack&&!p.receive)||p.drop_paused||p.drop_injected:true);
  const body=$('packetRows');body.replaceChildren();$('traceEmpty').classList.toggle('hidden',rows.length>0);
  for(const p of rows){const row=document.createElement('tr');row.tabIndex=0;row.classList.toggle('selected',selected===p.seq);
    row.append(cell('#'+p.seq,'seq'),cell(p.bytes+' B'),mark(p.send),mark(p.forward,p.drop_paused||p.drop_injected||p.drop_capacity||p.events.some(e=>e.node==='R'&&e.type==='invalid')),mark(p.receive,p.events.some(e=>e.node==='D'&&e.type==='invalid')),mark(p.ack),cell(p.rtt_ms==null?'—':p.rtt_ms.toFixed(1)+' ms','number'));
    const choose=()=>{detail(p);body.querySelectorAll('tr').forEach(r=>r.classList.remove('selected'));row.classList.add('selected');};row.onclick=choose;row.onkeydown=e=>{if(e.key==='Enter')choose();};body.append(row);}
  const chosen=rows.find(p=>p.seq===selected);if(chosen)detail(chosen);else if(rows.length)detail(rows[0]);else $('packetDetail').textContent='Không có gói khớp bộ lọc.';
}
export function refreshLogs(){
  const mode=state.mode,run=mode==='live'?state.status?.run:state.activeRun;
  $('traceSection').classList.toggle('hidden',mode==='simulation');$('analysisSection').classList.toggle('hidden',mode!=='simulation');
  if(mode==='simulation'||!run||busy)return;
  busy=true;
  api('trace/'+run.id+'?filter='+$('traceFilter').value).then(data=>{
    if(state.mode!==mode||(mode==='live'?state.status?.run:state.activeRun)?.id!==run.id)return;
    if(lastRun!==run.id){selected=null;lastRun=run.id;}
    packets=data.packets;$('traceCaption').textContent=`Run ${run.id} · Đích ${run.received_observed}/${run.sent} · ACK ${run.acked} · ${packets.length}/${data.matching} gói theo bộ lọc · ${run.finished?'Đã kết thúc':'Đang nhận log'}`;
    $('rawLog').href=`/results/run_${run.id}/events.jsonl`;draw();
  }).catch(()=>{}).finally(()=>busy=false);
}
export function setupLogs(){
  $('traceFilter').onchange=()=>{draw();refreshLogs();};setInterval(refreshLogs,900);refreshLogs();
}
