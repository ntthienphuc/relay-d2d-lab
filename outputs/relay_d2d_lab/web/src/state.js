export const state = {
  mode: 'simulation', running: true, protocol: 'DF', snr: 4, relayPosition: .5,
  simulation: null, status: null, activeRun: null, replay: null,
  pulses: [], packetId: 0, eventsSeen: new Set(), selectedNode: null,
  palette: {Direct:'#818580',DF:'#242522','AF-FG':'#c14f24','AF-VG':'#75639e'},
};

export function emitPulse(from,to,success=true,label='',duration=1.05){
  state.pulses.push({from,to,success,label,duration,start:performance.now()/1000,id:state.packetId++});
  if(state.pulses.length>160)state.pulses.shift();
}

export function consumeEvent(e){
  const key=e.event_id||`${e.run}/${e.type}/${e.seq}/${e.node}/${e.server_time}`;
  if(state.eventsSeen.has(key))return;
  state.eventsSeen.add(key);
  if(state.eventsSeen.size>10000)state.eventsSeen.clear();
  const route=state.activeRun?.config?.route||'relay';
  if(e.type==='send')emitPulse('S',route==='relay'?'R':'D',true,`#${e.seq}`);
  if(e.type==='forward')emitPulse('R','D',true,`#${e.seq}`);
  if(e.type==='ack_forward')emitPulse('D','R',true,'ACK',.45);
  if(e.type==='ack')emitPulse(route==='relay'?'R':'D','S',true,'ACK',.55);
  if(e.type.startsWith('drop')||e.type==='invalid')emitPulse(e.node,e.node,false,`#${e.seq}`,1.2);
}

export function selectedRow(){
  const rows=state.simulation?.rows||[];
  return rows.reduce((best,r)=>!best||Math.abs(r.snr_db-state.snr)<Math.abs(best.snr_db-state.snr)?r:best,null);
}
