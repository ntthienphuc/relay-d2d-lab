export const routes = {
  direct: [
    {kind:'phone', label:'Samsung', detail:'Nguồn'},
    {kind:'ap', label:'AP gốc', detail:'Wi-Fi chung'},
    {kind:'pc', label:'Laptop', detail:'Đích + điều khiển'},
  ],
  esp: [
    {kind:'phone', label:'Samsung', detail:'Nguồn'},
    {kind:'ap', label:'AP gốc', detail:'Wi-Fi chung'},
    {kind:'esp', label:'ESP32-CAM', detail:'STA + SoftAP'},
    {kind:'phone', label:'OPPO', detail:'Đích · Wi-Fi RelayBox'},
  ],
};
const mode = new URLSearchParams(location.search).get('route');
export const state = {nodes: routes[mode] ?? routes.esp, running: true};

