export function renderBench(list, nodes) {
  const signature=JSON.stringify(nodes.map(n=>[n.id,n.role,n.model,n.online,n.local_ip,n.bridge_id,n.platform,n.rssi_dbm,n.forwarded,n.queue_lost]));
  if(list.dataset.signature===signature)return;
  list.dataset.signature=signature;
  const rows = nodes.map(node => {
    const row = document.createElement('div');
    row.className = 'bench-node' + (node.online ? '' : ' offline');
    const title = document.createElement('strong');
    const roles = {source:'Nguồn', relay:'Relay', sink:'Đích'};
    title.textContent = (roles[node.role] || node.role) + ' · ' + node.model;
    const status = document.createElement('span');
    status.textContent = node.online ? 'Trực tuyến' : 'Mất liên lạc';
    const detail = document.createElement('small');
    const fields = [node.local_ip];
    if (node.bridge_id) fields.push('qua RelayBox');
    if (node.online && node.rssi_dbm < 0) fields.push(node.rssi_dbm + ' dBm');
    if (node.online && node.forwarded && node.role === 'relay') fields.push(node.forwarded + ' gói đã chuyển');
    if (node.queue_lost) fields.push(node.queue_lost + ' log bị bỏ');
    detail.textContent = fields.join(' · ');
    row.append(title, status, detail);
    if (node.online && node.platform === 'esp32' && /^(?:\d{1,3}\.){3}\d{1,3}$/.test(node.local_ip)) {
      const portal = document.createElement('a');
      portal.href = 'http://' + node.local_ip + '/';
      portal.target = '_blank';
      portal.rel = 'noopener';
      portal.textContent = 'Mở bảng ESP32 ↗';
      row.append(portal);
    }
    return row;
  });
  if (!rows.length) list.textContent = 'Đang chờ thiết bị đăng ký qua Wi-Fi…';
  else list.replaceChildren(...rows);
}
