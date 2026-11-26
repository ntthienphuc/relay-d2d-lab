#pragma once

// Standalone portal served by the ESP32, including when the upstream AP is unavailable.
static const char PAGE[] PROGMEM = R"HTML(<!doctype html>
<html lang="vi">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RelayBox · Trạm chuyển tiếp</title>
<style>
:root{color-scheme:light;color:#252620;background:#f6f5f0;font:15px/1.5 system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0}main{width:min(670px,calc(100% - 28px));margin:auto;padding:22px 0 32px}
header{display:flex;align-items:center;gap:10px;margin-bottom:18px;font-size:20px;font-weight:670;letter-spacing:-.5px}
header b{display:grid;place-items:center;width:33px;height:33px;border-radius:9px;background:#ed794b;font-size:16px}
header small{margin-left:auto;color:#5b5c52;font:12px monospace}
.status,.readings,details{border:1px solid #d9d7cc;border-radius:14px;background:#fffef9}
.status{padding:16px 18px;background:#2d2f27;color:#fffef9;border-color:#2d2f27}
h1,h2,p{margin:0}h1{font-size:22px;line-height:1.2;letter-spacing:-.5px}h2{font-size:17px}
#link{display:flex;align-items:baseline;gap:8px;margin-top:8px;color:#ebe6d7;font-size:13px}
#link:before{content:"";display:inline-block;flex:none;width:8px;height:8px;border-radius:50%;background:#b4ab97}
#link.online:before{background:#ffad83}.readings{margin-top:12px;overflow:hidden}.readings h2{padding:14px 14px 0}
dl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin:10px 0 0}
dl div{padding:12px 14px;min-width:0;border-top:1px solid #e2dfd2;border-right:1px solid #e2dfd2}
dl div:nth-child(3n){border-right:0}dt{color:#5e5e51;font-size:12px}
dd{margin:4px 0 0;font:650 clamp(19px,4.8vw,27px) monospace;color:#303027;overflow-wrap:anywhere}
dl div:nth-child(2) dd{color:#9c3818}
details{margin-top:11px;padding:0 14px}summary{cursor:pointer;padding:12px 0;font-weight:620;color:#33342a}
label{display:block;margin-top:10px;color:#47483e;font-size:13px}
input,button{display:block;width:100%;min-height:42px;padding:9px 10px;border:1px solid #c8c6b8;border-radius:7px;font:inherit;color:#252620;background:#fcfbf6}
button{cursor:pointer;margin:13px 0 10px;background:#303229;color:white;border-color:#303229;font-weight:600}
details p{font-size:13px;color:#555449;margin-bottom:10px}
pre{max-height:240px;overflow:auto;font-size:12px;padding:10px;border-radius:8px;background:#efede2}
:focus-visible{outline:3px solid #b8572f;outline-offset:3px}
@media(max-width:340px){dl div{padding:8px 7px}dt{font-size:11px}}
</style>
<main>
<header><b aria-hidden="true">R</b>RelayBox<small>ESP32-CAM</small></header>
<section class="status"><h1>Kết nối Wi-Fi gốc</h1><p id="link" role="status">Đang đọc trạng thái…</p></section>
<section class="readings"><h2>Gói qua trạm</h2><dl id="counts"></dl></section>
<details>
  <summary>Chọn router và máy mở phòng</summary>
  <p>Nối thiết bị này vào Wi-Fi RelayBox để lưu cấu hình. C tiếp tục dùng Wi-Fi RelayBox sau khi ESP kết nối router.</p>
  <form action="/save" method="post">
    <label for="ssid">Tên Wi-Fi gốc (2,4 GHz)</label><input id="ssid" name="ssid" maxlength="32" required>
    <label for="pass">Mật khẩu Wi-Fi gốc</label><input id="pass" name="password" type="password" maxlength="64" autocomplete="new-password">
    <label for="server">IP máy mở phòng (bỏ trống nếu chỉ dùng Internet)</label><input id="server" name="server" inputmode="decimal">
    <button>Lưu và kết nối lại</button>
  </form>
</details>
<details id="lesson"><summary>So sánh Direct, DF và AF trên ESP</summary>
  <p>ESP tự mô phỏng kênh Rayleigh. Mỗi phương án nhận cùng 32.768 mẫu. Chọn SNR để xem tỷ lệ khung không đạt 0,5 bit/s/Hz.</p>
  <label for="snr">SNR tham chiếu</label><select id="snr" style="padding:7px;font:inherit"><option>0 dB</option><option selected>8 dB</option><option>16 dB</option></select>
  <p id="modelstate" role="status"></p><table style="width:100%;text-align:left;font-size:14px"><thead><tr><th>Cơ chế</th><th>Khung lỗi</th><th>Outage</th></tr></thead><tbody id="modelrows"></tbody></table>
  <p>DF giải mã ở B. AF-FG và AF-VG khuếch đại mẫu tín hiệu theo gain cố định hoặc biến đổi trong mô hình. Số DATA/ACK ở trên lấy từ UDP thật.</p>
</details>
<details><summary>Thông số kỹ thuật</summary><pre id="status"></pre></details>
</main>
<script>
const fields = [['DATA đã nhận','received'],['DATA đã chuyển','forwarded'],['ACK đã chuyển','acks'],
                ['Gói không hợp lệ','invalid'],['Log đang chờ','pending_events'],['Máy đã nối','ap_clients']];
const counts = document.querySelector('#counts');
const link = document.querySelector('#link');
const status = document.querySelector('#status');
const values = fields.map(([name]) => {
  const cell = document.createElement('div');
  const label = document.createElement('dt');
  const value = document.createElement('dd');
  label.textContent = name;
  value.textContent = '—';
  cell.append(label,value);
  counts.append(cell);
  return value;
});
const lesson=document.querySelector('#lesson'),snr=document.querySelector('#snr');
const modelstate=document.querySelector('#modelstate'),modelrows=document.querySelector('#modelrows');
let model=null,loading=false;
function renderModel(){
  if(!model)return;
  const row=model.rows[snr.selectedIndex];
  const percent=x=>(100*x).toFixed(2).replace('.',',')+'%';
  modelstate.textContent='DF dạng đóng: '+percent(row.df_closed)+' · Vị trí B ở giữa hai đầu.';
  modelrows.replaceChildren();
  Object.entries(row.failures).forEach(([name,n])=>{
    const tr=modelrows.insertRow();
    [name,n,percent(n/model.samples)].forEach(value=>tr.insertCell().textContent=value);
  });
}
async function loadModel(){
  if(loading||model||!lesson.open)return;
  loading=true;
  try{
    const response=await fetch('/compare',{cache:'no-store'});
    if(!response.ok)throw Error();
    const data=await response.json();
    if(data.rows){model=data;renderModel();}
    else {modelstate.textContent='ESP đang tính: '+data.done+' / '+data.samples+' mẫu…';setTimeout(loadModel,550);}
  }catch(e){modelstate.textContent='Chưa đọc được kết quả. Đóng rồi mở lại mục này.';}
  finally{loading=false;}
}
lesson.addEventListener('toggle',loadModel);snr.addEventListener('change',renderModel);
async function poll() {
  try {
    const response = await fetch('/status', {cache:'no-store'});
    if (!response.ok) throw new Error('status');
    const data = await response.json();
    link.classList.toggle('online',Boolean(data.wifi_connected));
    link.textContent = data.wifi_connected
      ? (data.ipv4_forwarding ? 'Đang chia sẻ Internet qua IPv4' : data.internet_mode === 'subnet_overlap' ? 'Trùng dải mạng. Đổi dải IP của router.' : 'Đang chuẩn bị định tuyến') + ' · ' + data.local_ip
      : 'Đang dò mạng đã lưu';
    fields.forEach(([,key],index) => { values[index].textContent = data[key] ?? '—'; });
    status.textContent = JSON.stringify(data,null,2);
  } catch {
    link.classList.remove('online');
    link.textContent = 'Mất phản hồi. Kiểm tra mạng đang kết nối.';
  }
  setTimeout(poll,2000);
}
poll();
</script></html>)HTML";

