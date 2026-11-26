import {state,selectedRow,consumeEvent} from './state.js';
import {api,toast} from './api.js';
import {outageChart,packetChart} from './charts.js';
import {renderBench} from './bench.js';
import {updateRouteControls, selectedRoute} from './routes.js';
const $=id=>document.getElementById(id);
const explanations={DF:['Giải mã','Kiểm tra','Tái tạo','DF tái tạo tín hiệu sau giải mã; chặng đầu không giải mã được thì liên lạc thất bại. Mô hình này giả định giải mã lý tưởng theo ngưỡng tốc độ.'],
  'AF-FG':['Nhận yᵣ','Gain cố định','Phát lại','AF khuếch đại cả tín hiệu và nhiễu. Gain cố định dựa vào công suất kênh trung bình; công suất phát relay tức thời có thể thay đổi.'],
  'AF-VG':['Nhận yᵣ','Ước lượng CSI','Đổi gain','AF điều chỉnh gain theo kênh S→R để chuẩn hóa công suất relay. Mô hình CSI lý tưởng; năng lượng CSI là một tham số khảo sát.'],
  Direct:['Nguồn S','Kênh S→D','Đích D','Truyền trực tiếp dùng toàn bộ khung. Relay HD dùng hai khe bằng nhau; các phương án có cùng năng lượng phát RF kỳ vọng trong khung.']};
let dirty=false,historyTimer,latestEvents=[];

export function setMode(mode){
  state.mode=mode;
  $('traceSection').classList.toggle('hidden',mode==='simulation');
  $('analysisSection').classList.toggle('hidden',mode!=='simulation');
  $('topologyLine').classList.toggle('hidden',mode==='simulation');
  document.body.dataset.view=mode;
  const pages={simulation:['Mô phỏng kênh truyền','Theo dõi tín hiệu giữa nguồn, trạm chuyển tiếp và đích.'],live:['Đo trên thiết bị','Chọn đường truyền, gửi gói và xem đích nhận được bao nhiêu.'],replay:['Nhật ký gói tin','Mở một phiên để lần theo DATA và ACK.']};
  [$('viewTitle').textContent,$('viewDescription').textContent]=pages[mode];
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
  state.pulses=[];state.replay=null;state.eventsSeen.clear();
  document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));
  $('simPanel').classList.toggle('hidden',mode!=='simulation');$('livePanel').classList.toggle('hidden',mode!=='live');$('historyPanel').classList.toggle('hidden',mode!=='replay');
  $('modeBadge').textContent=mode.toUpperCase();$('modeBadge').className='badge '+mode;
  $('sceneCaption').textContent=mode==='simulation'?'SISO · Rayleigh · Half-duplex':mode==='live'?'UDP tầng ứng dụng · LAN qua AP':'Sự kiện đã lưu · không phải đo trực tiếp';
  if(mode==='simulation'){$('labelD').querySelector('small').textContent='ĐÍCH MÔ HÌNH';$('labelS').querySelector('small').textContent='NGUỒN MÔ HÌNH';$('labelR').querySelector('small').textContent='RELAY';renderSimulation();}
  else if(mode==='live')renderLive(state.status?.run);
  else{loadHistory();renderLive(null);}
}

function metric(i,label,value,unit=''){$('metricLabel'+i).textContent=label;$('metric'+i).replaceChildren(document.createTextNode(value));if(unit){const s=document.createElement('small');s.textContent=unit;$('metric'+i).append(s);}}
function steps(items){$('pipeline').replaceChildren();items.forEach((v,i)=>{if(i){const a=document.createElement('i');a.textContent='→';$('pipeline').append(a);}const n=document.createElement('span');n.textContent=v;$('pipeline').append(n);});}
export function renderSimulation(){
  if(state.mode!=='simulation')return;const row=selectedRow();if(!row)return;
  const m=row.modes[state.protocol];
  metric(1,'Xác suất hụt tốc độ',`${(m.outage*100).toFixed(2)}%`);metric(2,'Tốc độ hữu ích',m.throughput_bps_hz.toFixed(3),'bit/s/Hz');metric(3,'Hiệu quả năng lượng',(m.bits_per_joule/1000).toFixed(1),'kbit/J');metric(4,'Relay được chọn',row.selected==='INFEASIBLE'?'Chưa đạt':row.selected);
  $('plotTitle').textContent='Xác suất hụt tốc độ';$('plotSubtitle').textContent='Dải mờ: CI 95% · Tròn rỗng: 0 lỗi quan sát';
  outageChart($('chart'),state.simulation,state.palette,state.snr);
  $('legend').replaceChildren();for(const [name,color]of Object.entries({...state.palette,'DF dạng đóng':'#213547'})){const s=document.createElement('span');const i=document.createElement('i');i.style.background=color;s.append(i,document.createTextNode(name));$('legend').append(s);}
  $('inspectorTitle').textContent='Cơ chế chuyển tiếp';$('inspectorHint').textContent=state.protocol;
  const e=explanations[state.protocol];steps(e.slice(0,3));$('explanation').textContent=e[3];
  $('confidence').textContent=dirty?'Tham số đã đổi — bấm Chạy Monte Carlo để cập nhật kết quả.':`CI 95%: [${m.ci95.map(x=>(100*x).toFixed(3)+'%').join('; ')}] · ${m.failures.toLocaleString()}/${state.simulation.config.samples.toLocaleString()} mẫu outage. Seed ${state.simulation.config.seed}.`;
  $('footerStatus').textContent=`SIMULATION · ${state.simulation.config.samples.toLocaleString()} mẫu/điểm · Kết quả năng lượng giả định, không phải số đo điện thoại`;
}

function renderLive(run){
  if(state.mode==='simulation')return;state.activeRun=run;
  if(state.mode==='live'){
    const local=run?.config?.environment==='local'||$('environment').value==='local';
    $('modeBadge').textContent=local?'LOOPBACK':'LIVE';
    $('sceneCaption').textContent=local?'UDP cục bộ · các nút phần mềm trên laptop':'UDP tầng ứng dụng · LAN qua AP';
    const rd=state.status?.devices?.find(d=>d.id===run?.config?.relay_id);
    $('labelR').querySelector('small').textContent=local?'LOCAL PROCESS':rd?.platform==='esp32'?'ESP32 RELAYBOX':'ANDROID RELAY';
    $('labelS').querySelector('small').textContent=run?.config?.source_id&&run.config.source_id!=='laptop'?'ANDROID SOURCE':'LAPTOP';
  }
  const localRun=run?.config?.environment==='local';
  const bench=run?.config?.source_id!=='laptop'&&run?.config?.destination_id!=='laptop';
  const esp=String(run?.config?.relay_id).startsWith('esp32-');
  const nodes=run?.config?.route==='direct'?'Nguồn → AP gốc → Đích':esp?'Nguồn → AP gốc → ESP (STA / SoftAP) → Đích':'Nguồn → Android relay → Đích · Chung Wi-Fi gốc';
  $('topologyLine').textContent=!run?'Chọn một phiên để xem tuyến DATA và đường về của ACK.':localRun?'Loopback trên laptop · Các nút trao đổi gói UDP cục bộ.':(bench||run.config.route==='relay'?nodes:run.topology)+' · ACK về theo chiều ngược.';
  const p=run?.pdr_observed;
  metric(1,'Nguồn đã phát',run?String(run.sent):'—','gói');metric(2,'Đích nhận được',p===null||p===undefined?'—':(100*p).toFixed(1)+'%');
  metric(3,'RTT p95',run?.rtt_p95_ms==null?'—':run.rtt_p95_ms.toFixed(1),'ms');metric(4,'Tốc độ tải hữu ích',run?run.goodput_kbps.toFixed(2):'—','kbit/s');
  $('plotTitle').textContent='Dấu vết gói tin';$('plotSubtitle').textContent='Sequence được đối chiếu ở từng nút';$('legend').textContent='DATA và ACK theo sequence';
  packetChart($('chart'),run?.events||latestEvents,run?.sent||0);
  $('inspectorTitle').textContent='Kiểm tra / chuyển tiếp';$('inspectorHint').textContent=run?`RUN ${run.id}`:'Chưa có phiên đo';steps(run?.config?.route==='direct'?['Nguồn','AP gốc / loopback','Đích trả ACK']:['Kiểm tra tại R','Chuyển DATA','Trả ACK']);
  $('explanation').textContent=run?(run.topology+' · Đích nhận '+run.received_observed+'/'+run.sent+' · Nguồn nhận '+run.acked+' ACK'):'Chọn thiết bị đã đăng ký hoặc LOOPBACK, rồi bắt đầu một lượt đo. Dữ liệu payload được tạo theo run_id + sequence để kiểm tra byte đầu cuối.';
  $('confidence').textContent=run?`Nhận tại đích: ${run.received_observed} · ACK: ${run.acked} · CI 95% (giả định độc lập): ${run.pdr_ci95_iid?.map(x=>(100*x).toFixed(1)+'%').join(' – ')??'—'}. ${run.stop_reason?'Phiên không đầy đủ: '+run.stop_reason:'RTT chỉ trên gói có ACK; log thiếu làm tỷ lệ xác nhận là cận dưới.'}`:'Chưa có dữ liệu thực nghiệm.';
  $('footerStatus').textContent=run?`${state.mode.toUpperCase()} · ${run.config.environment.toUpperCase()} · ${run.finished?'Đã kết thúc':'Đang đo'} · ${run.elapsed.toFixed(1)} / ${run.config.duration}s · ${run.config.payload} bytes/gói`:'Sẵn sàng · Mở Relay Lab trên Android để kết nối';
  $('startRun').disabled=!!(run&&!run.finished);
  const pilot=run?.config?.destination_id==='laptop';$('labelD').querySelector('small').textContent=pilot?'LAPTOP SINK':'ANDROID 02';
}

function options(select,items){const previous=select.value;select.replaceChildren();for(const [id,label]of items){const o=document.createElement('option');o.value=id;o.textContent=label;select.append(o);}if(items.some(x=>x[0]===previous))select.value=previous;}
async function poll(){
  try{state.status=await api('status');$('connection').textContent='Máy chủ trực tuyến';$('connection').classList.add('online');$('serverAddress').textContent=`http://${state.status.server_ip}:8765`;
    renderBench($('deviceList'),state.status.devices);
    updateRouteControls(state.status);
    const net=state.status.network;
    if(net){
      const box=$('benchAddress'),addresses=[...new Set([net.server_ip,...net.addresses])];
      if(box.dataset.signature!==addresses.join(',')){options(box,addresses.map(ip=>[ip,ip]));box.value=net.server_ip;box.dataset.signature=addresses.join(',');}
    }
    if(state.mode==='live'){
      const run=state.status.run;renderLive(run);
      if(run&&!run.finished)for(const e of run.events)consumeEvent(e);
    }
  }catch(e){$('connection').textContent='Mất kết nối máy chủ';$('connection').classList.remove('online');}
  setTimeout(poll,600);
}

async function loadHistory(){
  try{const rows=await api('history?scope='+$('historyScope').value);$('historyList').replaceChildren();
    if(!rows.length)$('historyList').textContent='Chưa có lượt đo mới. Mở Đo trên thiết bị để bắt đầu hoặc chọn Phiên minh chứng.';
    for(const r of rows){const item=document.createElement('div');item.className='history-item';
      const title=document.createElement('b');title.textContent=`${r.config.experiment_label||r.config.environment.toUpperCase()} · ${r.config.route} · ${r.id}`;
      const info=document.createElement('small');info.textContent=`${r.sent} gửi · ${r.delivery_confirmed} xác nhận · RTT p95 ${r.rtt_p95_ms?.toFixed(1)??'—'} ms`;
      const b=document.createElement('button');b.textContent='▶ Phát lại';b.onclick=()=>replay(r.id);
      const a=document.createElement('a');a.href=`/results/run_${r.id}/summary.json`;a.textContent='JSON';a.target='_blank';
      item.append(title,info,b,a);$('historyList').append(item);}
  }catch(e){toast(e.message,true);}
}
export async function replay(id){
  try{const data=await api('replay/'+id);state.eventsSeen.clear();state.activeRun=data.summary;latestEvents=[];
    const events=data.events;const origin=events[0]?.server_time||0;
    state.replay={events,index:0,start:performance.now()/1000,origin,summary:data.summary};
    renderLive(data.summary);$('sceneCaption').textContent=`REPLAY · run ${id} · tốc độ ×1`;
  }catch(e){toast(e.message,true);}
}
export function advanceReplay(time){
  const r=state.replay;if(state.mode!=='replay'||!r)return;
  while(r.index<r.events.length&&r.events[r.index].server_time-r.origin<=time-r.start){const e=r.events[r.index++];consumeEvent(e);latestEvents.push(e);}
  if(r.index===r.events.length){state.replay=null;toast('Đã phát hết log của phiên '+r.summary.id);}
  if(Math.floor(time*5)!==historyTimer){historyTimer=Math.floor(time*5);packetChart($('chart'),latestEvents,Math.max(0,...latestEvents.filter(e=>e.type==='send').map(e=>e.seq+1)));}
}

export async function setupUI(camera){
  for(const id of ['route','environment','sourceDevice','relayDevice','destinationDevice']){
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
  document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));$('resetCamera').onclick=()=>camera.reset();
  $('protocol').onchange=e=>selectProtocol(e.target.value);
  $('snr').oninput=e=>{state.snr=+e.target.value;$('snrValue').textContent=state.snr+' dB';renderSimulation();};
  $('position').oninput=e=>{state.relayPosition=+e.target.value/100;$('positionValue').textContent=e.target.value+'%';dirty=true;renderSimulation();};
  for(const id of ['rate','samples','qos','processing','csi'])$(id).onchange=()=>{dirty=true;renderSimulation();};
  $('simulate').onclick=async()=>{
    $('simulate').disabled=true;$('footerStatus').textContent='Đang sinh kênh và đếm sự kiện outage…';
    try{state.simulation=await api('simulation',{samples:+$('samples').value,rate:+$('rate').value,relay_position:state.relayPosition,qos:+$('qos').value,processing_mj:+$('processing').value,csi_mj:+$('csi').value});dirty=false;renderSimulation();toast('Đã hoàn tất Monte Carlo và khoảng tin cậy.');}catch(e){toast(e.message,true);}finally{$('simulate').disabled=false;}
  };
  $('startRun').onclick=async()=>{try{if($('environment').value==='live'&&selectedRoute()==='relay'&&!$('relayDevice').value){$('routeDevices').open=true;throw new Error('Kết nối thiết bị chuyển tiếp trước khi bắt đầu.');}state.eventsSeen.clear();state.pulses=[];const run=await api('run',{environment:$('environment').value,route:selectedRoute(),relay_kind:$('route').value==='android'?'android':$('route').value==='relay'?'esp32':'',source_id:$('sourceDevice').value,experiment_label:$('experimentLabel').value,corrupt_every:+$('corruptEvery').value,drop_every:+$('dropEvery').value,duration:+$('duration').value,rate:+$('pps').value,payload:+$('payload').value,relay_id:$('relayDevice').value,destination_id:$('destinationDevice').value});state.activeRun=run;renderLive(run);toast('Đang đo run '+run.id);}catch(e){toast(e.message,true);}};
  $('pauseRelay').onclick=async()=>{try{const r=await api('pause-relay',{});toast(r.paused?'Đã yêu cầu dừng forwarding.':'Đã yêu cầu bật forwarding.');}catch(e){toast(e.message,true);}};
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
