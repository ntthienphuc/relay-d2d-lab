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

export function updateRouteControls(status) {
  const nodes = status?.devices ?? [];
  if (status?.practice) {
    $('environment').value = 'local';
    $('environment').options[0].disabled = true;
  }
  const practice = $('environment').value === 'local' || status?.practice === true;
  const choice = $('route').value;
  const direct = choice === 'direct';
  const phoneRelay = choice === 'android';
  const useLan = node => !node.bridge_id;
  const allDestinations = node => direct || phoneRelay ? useLan(node) : true;
  const relays = listed(nodes, 'relay', node => phoneRelay
    ? node.platform === 'android' && useLan(node)
    : node.platform === 'esp32');
  fill($('relayDevice'), relays.length ? relays : [['', phoneRelay ? 'Chờ Android chọn Relay' : 'Chờ ESP32 kết nối']]);
  const relayId = $('relayDevice').value;
  fill($('sourceDevice'), [...listed(nodes, 'source', node => useLan(node) ||
    (!direct && !phoneRelay && node.bridge_id === relayId)), ['laptop', 'Laptop làm nguồn']]);
  const sourceOnEsp = nodes.some(node => node.id === $('sourceDevice').value && node.bridge_id);
  fill($('destinationDevice'), [...listed(nodes, 'sink', node => allDestinations(node)
    && (direct || phoneRelay || !node.bridge_id || (!sourceOnEsp && node.bridge_id === relayId))), ['laptop', 'Laptop làm đích']]);
  const usingLaptop = $('sourceDevice').value === 'laptop' || $('destinationDevice').value === 'laptop';
  const wrongNetwork = (direct || phoneRelay) && nodes.some(d => d.online && d.role === 'sink' && d.bridge_id);
  const hint = $('routeHelp');
  hint.classList.toggle('attention', !practice && (wrongNetwork || (!direct && !relays.length)));
  hint.textContent = practice ? 'Tập trên laptop bằng UDP cục bộ.' :
    wrongNetwork ? 'Điện thoại đích còn ở RelayBox. Hãy về cùng Wi-Fi với laptop rồi chọn Laptop trong ứng dụng.' :
    phoneRelay ? 'Các máy dùng cùng Wi-Fi. Chọn Relay trên điện thoại ở giữa và nhập IP laptop.' :
    direct ? 'Cho nguồn và đích dùng chung Wi-Fi với laptop rồi chọn Laptop trong ứng dụng.' :
    'Giữ laptop ở Wi-Fi router. Điện thoại phía RelayBox chọn Gateway ESP, dù làm Nguồn hay Đích.';
  if (phoneRelay && usingLaptop && !practice && !wrongNetwork)
    hint.textContent += ' Có thể để laptop đảm nhiệm một đầu.';
  $('routeDevices').classList.toggle('hidden', practice);
  $('relayChoice').classList.toggle('hidden', direct);
  $('routeNetwork').textContent = practice ? 'UDP nội bộ · Không cần điện thoại' : direct ?
    'Nguồn → Wi-Fi gốc → Đích' : phoneRelay ? 'Nguồn → Android relay → Đích · Chung Wi-Fi gốc' :
    'Nguồn → ESP32 relay → Đích';
  const form = $('routeDevices');
  if (phoneRelay && !practice && form.dataset.route !== choice) form.open = true;
  form.dataset.route = choice;
  const pause = $('pauseRelay');
  pause.classList.toggle('hidden', direct);
  const active = status?.run && !status.run.finished;
  pause.disabled = !active || status.run.config.route !== 'relay';
  $('stopRun').disabled = !active;
}

export function selectedRoute() {
  const choice = $('route').value;
  return choice === 'direct' ? 'direct' : 'relay';
}

