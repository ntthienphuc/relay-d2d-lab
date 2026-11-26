import {state,selectedRow,consumeEvent} from './state.js';
import {api,toast} from './api.js';
import {outageChart} from './charts.js';
import {renderBench} from './bench.js';
import {updateRouteControls, selectedRoute} from './routes.js';
const $=id=>document.getElementById(id);
const explanations={DF:['Giải mã','Kiểm tra','Tái tạo','DF tái tạo tín hiệu sau giải mã; chặng đầu không giải mã được thì liên lạc thất bại. Mô hình này giả định giải mã lý tưởng theo ngưỡng tốc độ.'],
  'AF-FG':['Nhận yᵣ','Gain cố định','Phát lại','AF khuếch đại cả tín hiệu và nhiễu. Gain cố định dựa vào công suất kênh trung bình; công suất phát relay tức thời có thể thay đổi.'],
  'AF-VG':['Nhận yᵣ','Ước lượng CSI','Đổi gain','AF điều chỉnh gain theo kênh S→R để chuẩn hóa công suất relay. Mô hình CSI lý tưởng; năng lượng CSI là một tham số khảo sát.'],
  Direct:['Nguồn S','Kênh S→D','Đích D','Truyền trực tiếp dùng toàn bộ khung. Relay HD dùng hai khe bằng nhau; các phương án có cùng năng lượng phát RF kỳ vọng trong khung.']};
let dirty=false;

const pages={
  simulation:['Mô phỏng kênh truyền','Thay đổi SNR và vị trí relay để so sánh Direct, DF và AF.'],
  practice:['Tập gửi gói trên laptop','Ba nút phần mềm trao đổi UDP ngay trên máy này.'],
  live:['Đo trên thiết bị','Chọn hai đầu truyền để đo DATA, ACK và độ trễ qua Wi-Fi.'],
  replay:['Nhật ký gói tin','Chọn một phiên đã lưu để xem đường đi của từng gói.']
};
let pageRequest=0,historyRequest=0,roomKnown=false,starting=false;
// Keep practice faults and payload settings out of the next physical measurement.
const formFields=['route','duration','pps','payload','experimentLabel','dropEvery','corruptEvery'];
const roomForms={};
function readForm(){return Object.fromEntries(formFields.map(id=>[id,$(id).value]));}
function currentRun(){
  const run=state.status?.run;
  return run?.config?.environment===$('environment').value ? run : null;
}
export function setMode(page){
  if(!pages[page])page='live';
  if(page==='live'&&state.status?.practice)page='practice';
  if(state.page==='live'||state.page==='practice')roomForms[state.page]=readForm();
  if(!roomForms.defaults)roomForms.defaults=readForm();
  if(page==='practice'||page==='live'){
    const saved=roomForms[page]||roomForms.defaults;
    for(const id of formFields)$(id).value=saved[id];
  }
  pageRequest++;
  state.page=page;
  const mode=page==='practice'?'live':page;
  state.mode=mode;
  const lab=page==='practice'||page==='simulation';
  $('environment').value=page==='practice'?'local':'live';
  document.body.dataset.view=page;
  [$('viewTitle').textContent,$('viewDescription').textContent]=pages[page];
  for(const b of document.querySelectorAll('[data-mode]')){
    const chosen=b.dataset.mode===(lab?'simulation':page);
    b.setAttribute('aria-pressed',String(chosen));b.classList.toggle('active',chosen);
  }
  for(const b of document.querySelectorAll('[data-lab]'))b.setAttribute('aria-pressed',String(b.dataset.lab===page));
  $('labSwitch').classList.toggle('hidden',!lab);
  $('traceSection').classList.toggle('hidden',mode==='simulation');
  $('analysisSection').classList.toggle('hidden',mode!=='simulation');
  $('topologyLine').classList.toggle('hidden',mode==='simulation');
  $('simPanel').classList.toggle('hidden',mode!=='simulation');
  $('livePanel').classList.toggle('hidden',mode!=='live');
  $('historyPanel').classList.toggle('hidden',mode!=='replay');
  $('liveHeading').textContent=page==='practice'?'Tập điều khiển phiên':'Chuẩn bị thiết bị';
  $('route').options[0].textContent=page==='practice'?'Qua relay nội bộ':'Qua ESP32-CAM';
  $('route').options[1].textContent=page==='practice'?'Hai đầu trực tiếp':'Direct · cùng Wi-Fi';
  $('route').options[2].hidden=page==='practice';
  if(page==='practice'&&$('route').value==='android')$('route').value='relay';
  for(const id of ['espSetup','apkLink','hardwareNote'])$(id).hidden=page==='practice';
  $('deviceList').closest('details').hidden=page==='practice';
  state.pulses=[];state.replay=null;state.activeRun=null;state.eventsSeen.clear();
  $('modeBadge').className='badge '+page;
  $('modeBadge').textContent={simulation:'Mô hình',practice:'UDP nội bộ',live:'Wi-Fi thật',replay:'Đã ghi'}[page];
  $('sceneTitle').textContent=mode==='simulation'?'Mô hình đường truyền':'Đường đi của gói';
  $('sceneCaption').textContent=mode==='simulation'?'Kênh Rayleigh · hai khe':mode==='replay'?'Dữ liệu của phiên đã lưu':'';
  updateRouteControls(state.status);
  if(mode==='simulation'){
    for(const [id,name] of [['S','NGUỒN MÔ HÌNH'],['R','RELAY'],['D','ĐÍCH MÔ HÌNH']])$('label'+id).querySelector('small').textContent=name;
    renderSimulation();
  }else if(mode==='live')renderLive(currentRun());
  else{renderLive(null);loadHistory();}
}
function metric(i,label,value,unit=''){$('metricLabel'+i).textContent=label;$('metric'+i).replaceChildren(document.createTextNode(value));if(unit){const s=document.createElement('small');s.textContent=unit;$('metric'+i).append(s);}}
function steps(items){$('pipeline').replaceChildren();items.forEach((v,i)=>{if(i){const a=document.createElement('i');a.textContent='→';$('pipeline').append(a);}const n=document.createElement('span');n.textContent=v;$('pipeline').append(n);});}
export function renderSimulation(){
  if(state.mode!=='simulation')return;const row=selectedRow();if(!row)return;
  const m=row.modes[state.protocol];
  const formula={DF:['DF · Giải mã rồi phát lại','γ = min(a, b)'],'AF-FG':['AF · Gain cố định','γ = ab / (b + E[a] + 1)'],'AF-VG':['AF · Gain biến đổi','γ = ab / (a + b + 1)'],Direct:['Direct · Một chặng','C = log₂(1 + γSD)']}[state.protocol];
  const box=$('formula');box.querySelector('span').textContent=formula[0];box.querySelector('p').textContent=formula[1];
  box.querySelector('small').textContent=state.protocol==='Direct'?'Nguồn dùng trọn khung thời gian.':'a, b là SNR hai chặng. C = ½ log₂(1 + γ).';
  metric(1,'Xác suất hụt tốc độ',`${(m.outage*100).toFixed(2)}%`);metric(2,'Tốc độ hữu ích',m.throughput_bps_hz.toFixed(3),'bit/s/Hz');metric(3,'Hiệu quả năng lượng',(m.bits_per_joule/1000).toFixed(1),'kbit/J');metric(4,'Relay được chọn',row.selected==='INFEASIBLE'?'Chưa đạt':row.selected);
  $('plotTitle').textContent='Xác suất hụt tốc độ';$('plotSubtitle').textContent='Dải mờ: CI 95% · Tròn rỗng: 0 lỗi quan sát';
  outageChart($('chart'),state.simulation,state.palette,state.snr);
  $('legend').replaceChildren();for(const [name,color]of Object.entries({...state.palette,'DF dạng đóng':'#213547'})){const s=document.createElement('span');const i=document.createElement('i');i.style.background=color;s.append(i,document.createTextNode(name));$('legend').append(s);}
  $('inspectorTitle').textContent='Cơ chế chuyển tiếp';$('inspectorHint').textContent=state.protocol;
  const e=explanations[state.protocol];steps(e.slice(0,3));$('explanation').textContent=e[3];
  $('confidence').textContent=dirty?'Tham số đã đổi — bấm Chạy Monte Carlo để cập nhật kết quả.':`CI 95%: [${m.ci95.map(x=>(100*x).toFixed(3)+'%').join('; ')}] · ${m.failures.toLocaleString()}/${state.simulation.config.samples.toLocaleString()} mẫu outage. Seed ${state.simulation.config.seed}.`;
  $('footerStatus').textContent=`Mô phỏng · ${state.simulation.config.samples.toLocaleString()} mẫu/điểm · Kết quả năng lượng giả định, không phải số đo điện thoại`;
}

function renderLive(run){
  if(state.mode==='simulation')return;state.activeRun=run;
  if(state.mode==='live'){
    $('sceneCaption').textContent=state.page==='practice'?'Gói chỉ chạy trên laptop':'UDP ứng dụng · DATA và ACK';
  }
  const cfg=run?.config;
  state.preview=state.mode==='replay'?null:{route:selectedRoute(),relay_kind:$('route').value==='relay'?'esp32':'android',source_id:$('sourceDevice').value,destination_id:$('destinationDevice').value};
  const practice=cfg?.environment==='local'||state.page==='practice';
  const src=cfg?.source_id||$('sourceDevice').value;
  const dst=cfg?.destination_id||$('destinationDevice').value;
  const route=cfg?.route||selectedRoute();
  const isEsp=cfg?String(cfg.relay_id).startsWith('esp32-'):$('route').value==='relay';
  const online=state.status?.devices||[];
  const name=(id,fallback)=>id==='laptop'?'Laptop':online.find(d=>d.id===id)?.model||fallback;
  const relay=practice?'Relay nội bộ':isEsp?'RelayBox':'Android relay';
  const source=practice?'Nguồn nội bộ':name(src,'Điện thoại nguồn'),dest=practice?'Đích nội bộ':name(dst,'Điện thoại đích');
  const empty=state.mode==='replay'&&!cfg;
  $('labelS').querySelector('small').textContent=empty?'—':source;
  $('labelR').querySelector('small').textContent=empty||route==='direct'?'—':relay;
  $('labelD').querySelector('small').textContent=empty?'—':dest;
  $('topologyLine').textContent=empty?'Chọn phiên trong Nhật ký.':source+' → '+(route==='relay'?relay+' → ':'')+dest;
  const p=run?.pdr_observed;
  metric(1,'Nguồn đã phát',run?String(run.sent):'—','gói');metric(2,'Đích nhận được',p===null||p===undefined?'—':(100*p).toFixed(1)+'%');
  metric(3,'RTT p95',run?.rtt_p95_ms==null?'—':run.rtt_p95_ms.toFixed(1),'ms');metric(4,'Tốc độ tải hữu ích',run?run.goodput_kbps.toFixed(2):'—','kbit/s');
  $('footerStatus').textContent=run?`${state.mode.toUpperCase()} · ${run.config.environment.toUpperCase()} · ${run.finished?'Đã kết thúc':'Đang đo'} · ${run.elapsed.toFixed(1)} / ${run.config.duration}s · ${run.config.payload} bytes/gói`:'Sẵn sàng · Mở Relay Lab trên Android để kết nối';
  updateRouteControls(state.status,starting||!roomKnown);

}

function options(select,items){const previous=select.value;select.replaceChildren();for(const [id,label]of items){const o=document.createElement('option');o.value=id;o.textContent=label;select.append(o);}if(items.some(x=>x[0]===previous))select.value=previous;}
async function poll(){
  try{state.status=await api('status');
    if(!roomKnown){roomKnown=true;setMode(state.status.practice?'practice':state.page||'live');}
    const hardwareTab=document.querySelector('[data-mode="live"]');hardwareTab.disabled=state.status.practice;
    hardwareTab.title=state.status.practice?'Mở Relay Lab từ Desktop để đo Wi-Fi.':'';
$('connection').textContent='Máy chủ trực tuyến';$('connection').classList.add('online');$('serverAddress').textContent=`http://${state.status.server_ip}:${state.status.http_port}`;
    renderBench($('deviceList'),state.status.devices);
    updateRouteControls(state.status);
    const net=state.status.network;
    if(net){
      const box=$('benchAddress'),addresses=[...new Set([net.server_ip,...net.addresses])];
      if(box.dataset.signature!==addresses.join(',')){options(box,addresses.map(ip=>[ip,ip]));box.value=net.server_ip;box.dataset.signature=addresses.join(',');}
    }
    if(state.mode==='live'){
      const run=currentRun();renderLive(run);
      if(run&&!run.finished)for(const e of run.events)consumeEvent(e);
    }
  }catch(e){$('startRun').disabled=true;$('pauseRelay').disabled=true;$('stopRun').disabled=true;$('connection').textContent='Mất kết nối máy chủ';$('connection').classList.remove('online');}
  setTimeout(poll,600);
}

async function loadHistory(){
  const request=++historyRequest;try{const rows=await api('history?scope='+$('historyScope').value);if(request!==historyRequest||state.mode!=='replay')return;$('historyList').replaceChildren();
    if(!rows.length)$('historyList').textContent='Chưa có lượt đo mới. Mở Đo trên thiết bị để bắt đầu hoặc chọn Phiên minh chứng.';
    for(const r of rows){const item=document.createElement('div');item.className='history-item';
      const title=document.createElement('b');title.textContent=`${r.config.environment==='local'?'Tập UDP':'Đo Wi-Fi'} · ${r.config.experiment_label||r.config.route} · ${r.id}`;
      const info=document.createElement('small');info.textContent=`${r.sent} gửi · ${r.delivery_confirmed} xác nhận · RTT p95 ${r.rtt_p95_ms?.toFixed(1)??'—'} ms`;
      const b=document.createElement('button');b.textContent='▶ Phát lại';b.onclick=()=>replay(r.id);
      const a=document.createElement('a');a.href=`/results/run_${r.id}/summary.json`;a.textContent='JSON';a.target='_blank';
      item.append(title,info,b,a);$('historyList').append(item);}
  }catch(e){toast(e.message,true);}
}
export async function replay(id){
  const request=++pageRequest;try{const data=await api('replay/'+id);if(state.mode!=='replay'||request!==pageRequest)return;state.eventsSeen.clear();state.activeRun=data.summary;
    const events=data.events;const origin=events[0]?.server_time||0;
    state.replay={events,index:0,start:performance.now()/1000,origin,summary:data.summary};
    renderLive(data.summary);$('sceneCaption').textContent=`Phiên ${id} · phát lại ×1`;
  }catch(e){toast(e.message,true);}
}
export function advanceReplay(time){
  const r=state.replay;if(state.mode!=='replay'||!r)return;
  while(r.index<r.events.length&&r.events[r.index].server_time-r.origin<=time-r.start){const e=r.events[r.index++];consumeEvent(e);}
  if(r.index===r.events.length){state.replay=null;toast('Đã phát hết log của phiên '+r.summary.id);}
}

export async function setupUI(camera){
  setMode('live');
  for(const b of document.querySelectorAll('[data-lab]'))b.onclick=()=>setMode(b.dataset.lab);
  for(const id of ['pilot','route','sourceDevice','relayDevice','destinationDevice']){
    $(id).addEventListener('change',()=>{
      $(id).dataset.pinned='1';
      updateRouteControls(state.status);
    });
  }
  const protocolButtons=[...document.querySelectorAll('[data-protocol]')];
  function selectProtocol(name){
    state.protocol=name;
    $('protocol').value=name;
    protocolButtons.forEach(btn=>btn.setAttribute('aria-pressed',String(btn.dataset.protocol===name)));
    renderSimulation();
  }
  protocolButtons.forEach(btn=>btn.onclick=()=>selectProtocol(btn.dataset.protocol));
  selectProtocol(state.protocol);
  $('useBenchAddress').onclick=async()=>{try{const net=await api('network',{server_ip:$('benchAddress').value});toast('IP quản lý · '+net.server_ip);}catch(e){toast(e.message,true);}};
  document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));$('resetCamera').onclick=()=>camera?.reset();
  $('protocol').onchange=e=>selectProtocol(e.target.value);
  $('snr').oninput=e=>{state.snr=+e.target.value;$('snrValue').textContent=state.snr+' dB';renderSimulation();};
  $('position').oninput=e=>{state.relayPosition=+e.target.value/100;$('positionValue').textContent=e.target.value+'%';dirty=true;renderSimulation();};
  for(const id of ['rate','samples','qos','processing','csi'])$(id).onchange=()=>{dirty=true;renderSimulation();};
  $('simulate').onclick=async()=>{
    for(const input of $('simPanel').querySelectorAll('input[type=number]'))if(!input.reportValidity())return;
    $('simulate').disabled=true;$('footerStatus').textContent='Đang sinh kênh và đếm sự kiện outage…';
    try{state.simulation=await api('simulation',{samples:+$('samples').value,rate:+$('rate').value,relay_position:state.relayPosition,qos:+$('qos').value,processing_mj:+$('processing').value,csi_mj:+$('csi').value});dirty=false;renderSimulation();toast('Đã hoàn tất Monte Carlo và khoảng tin cậy.');}catch(e){toast(e.message,true);}finally{$('simulate').disabled=false;}
  };
  $('startRun').onclick=async()=>{if(starting)return;for(const input of $('livePanel').querySelectorAll('input[type=number]'))if(!input.reportValidity())return;starting=true;$('startRun').disabled=true;try{if($('environment').value==='live'&&selectedRoute()==='relay'&&!$('relayDevice').value){$('routeDevices').open=true;throw new Error('Kết nối thiết bị chuyển tiếp trước khi bắt đầu.');}state.eventsSeen.clear();state.pulses=[];const run=await api('run',{environment:$('environment').value,route:selectedRoute(),relay_kind:$('route').value==='android'?'android':$('route').value==='relay'?'esp32':'',source_id:$('sourceDevice').value,experiment_label:$('experimentLabel').value,corrupt_every:+$('corruptEvery').value,drop_every:+$('dropEvery').value,duration:+$('duration').value,rate:+$('pps').value,payload:+$('payload').value,relay_id:$('relayDevice').value,destination_id:$('destinationDevice').value});state.status.run=run;state.activeRun=run;renderLive(run);toast('Đang đo phiên '+run.id);}catch(e){toast(e.message,true);}finally{starting=false;}};
  $('pauseRelay').onclick=async()=>{try{const r=await api('pause-relay',{});toast(r.paused?'Đã tạm dừng chuyển gói.':'Relay tiếp tục chuyển gói.');}catch(e){toast(e.message,true);}};
  $('stopRun').onclick=async()=>{try{await api('stop',{});}catch(e){toast(e.message,true);}};
  $('refreshHistory').onclick=loadHistory;
  $('historyScope').onchange=loadHistory;
  $('lookupRun').onsubmit=e=>{
    e.preventDefault();
    const id=Number($('runNumber').value);
    if(Number.isSafeInteger(id)&&id>0)replay(id);
  };
  try{state.simulation=await api('simulation');const c=state.simulation.config;
    $('samples').value=c.samples;$('rate').value=c.rate;$('qos').value=c.qos;$('processing').value=c.processing_mj;$('csi').value=c.csi_mj;
    state.relayPosition=c.relay_position;$('position').value=Math.round(c.relay_position*100);$('positionValue').textContent=Math.round(c.relay_position*100)+'%';
    renderSimulation();}catch(e){toast(e.message,true);}poll();
}
