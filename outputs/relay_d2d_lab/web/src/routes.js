const $ = id => document.getElementById(id);

function fill(select, entries) {
  const selected = select.value;
  const signature = JSON.stringify(entries);
  if (select.dataset.entries === signature) return;
  select.replaceChildren(...entries.map(([id, label]) => new Option(label, id)));
  select.value = (select.dataset.pinned === '1' && entries.some(([id]) => id === selected)) ? selected : entries[0][0];
  select.dataset.entries = signature;
}

function listed(nodes, role, allow) {
  return nodes
    .filter(node => node.online && node.role === role && allow(node))
    .map(node => [node.id, node.model + ' · ' + node.local_ip]);
}

export function updateRouteControls(status, pending=false) {
  const nodes = status?.devices ?? [];
  const practice = $('environment').value === 'local' || status?.practice === true;
  const choice = $('route').value;
  const direct = choice === 'direct';
  const useLan = node => !node.bridge_id;
  const relays = listed(nodes, 'relay', node => node.platform === 'esp32');
  fill($('relayDevice'), relays.length ? relays : [['', 'Chờ ESP32 kết nối']]);
  const relayId = $('relayDevice').value;
  fill($('sourceDevice'), [...listed(nodes, 'source', node => useLan(node) ||
    (!direct && node.bridge_id === relayId)), ['laptop', 'Laptop làm nguồn']]);
  const sourceOnEsp = nodes.some(node => node.id === $('sourceDevice').value && node.bridge_id);
  fill($('destinationDevice'), [...listed(nodes, 'sink', node => useLan(node) || (!direct && !sourceOnEsp && node.bridge_id === relayId)), ['laptop', 'Laptop làm đích']]);
  const wrongNetwork = direct && nodes.some(d => d.online && d.role === 'sink' && d.bridge_id);
  const hint = $('routeHelp');
  hint.classList.toggle('attention', !practice && (wrongNetwork || (!direct && !relays.length)));
  hint.textContent = practice ? 'Tập trên laptop bằng UDP cục bộ.' :
    wrongNetwork ? 'Điện thoại đích còn ở RelayBox. Hãy về cùng Wi-Fi với laptop rồi chọn Laptop trong ứng dụng.' :
    direct ? 'Cho nguồn và đích dùng chung Wi-Fi với laptop rồi chọn Laptop trong ứng dụng.' :
    'Giữ laptop ở Wi-Fi router. Điện thoại phía RelayBox chọn Gateway ESP, dù làm Nguồn hay Đích.';
  $('routeDevices').classList.toggle('hidden', practice);
  $('relayChoice').classList.toggle('hidden', direct);
  $('routeNetwork').textContent = practice ? 'UDP nội bộ · Không cần điện thoại' : direct ?
    'Nguồn → Wi-Fi gốc → Đích' :
    'Nguồn → ESP32 relay → Đích';
  const form = $('routeDevices');
  form.dataset.route = choice;
  const run=status?.run;
  const active=!!run&&!run.finished;
  const sameRoom=active&&run.config.environment===$('environment').value;
  const bothLaptop=$('sourceDevice').value==='laptop'&&$('destinationDevice').value==='laptop';
  const missingRelay=!practice&&!direct&&!relays.length;
  const pilotAvailable=!practice&&!direct&&bothLaptop&&!missingRelay;
  $('pilotRow').hidden=!pilotAvailable;
  if(!pilotAvailable)$('pilot').checked=false;
  const missingEnd=!practice&&bothLaptop&&!(pilotAvailable&&$('pilot').checked);
  if(active&&!sameRoom)hint.textContent='Một phiên đang chạy trong phòng khác. Đợi phiên kết thúc rồi bắt đầu.';
  else if(missingRelay)hint.textContent='Cấp nguồn ESP32 và kiểm tra IP máy mở phòng trên trang RelayBox.';
  else if(missingEnd)hint.textContent=direct?'Chọn Nguồn hoặc Đích trên điện thoại, nối Wi-Fi router và kết nối trạm.':'Trên điện thoại, nối RelayBox, chọn Nguồn hoặc Đích → Gateway ESP → Kết nối trạm.';
  if(pilotAvailable&&$('pilot').checked)hint.textContent='Kiểm tra relay thật với laptop đảm nhiệm cả nguồn và đích.';
  $('startRun').disabled=!status||pending||active||missingRelay||missingEnd;
  $('startRun').textContent=active&&sameRoom?'Đang gửi gói…':practice?'Bắt đầu tập UDP':'Bắt đầu đo';
  const pause=$('pauseRelay');
  pause.classList.toggle('hidden',sameRoom?run.config.route!=='relay':direct);
  pause.disabled=!sameRoom||run.config.route!=='relay';
  pause.textContent=status?.paused&&sameRoom?'Tiếp tục relay':'Tạm dừng relay';
  $('stopRun').disabled=!sameRoom;
  for(const id of ['route','sourceDevice','destinationDevice','relayDevice','useBenchAddress','payload','duration','pps','dropEvery','corruptEvery','experimentLabel','pilot'])$(id).disabled=active;
  $('pps').max=!practice&&!direct?'50':'200';

}

export function selectedRoute() {
  const choice = $('route').value;
  return choice === 'direct' ? 'direct' : 'relay';
}

