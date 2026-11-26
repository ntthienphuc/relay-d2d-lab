import * as THREE from 'three';
import {state,emitPulse,selectedRow} from './state.js';
import {createWorld} from './world.js';
import {createNodes,updateNodes} from './nodes.js';
import {createCamera} from './cameras.js';
import {createPackets} from './packets.js';
import {setupUI,advanceReplay} from './ui.js';
import {setupLogs} from './logs.js';

const container=document.getElementById('viewport');
let world;
try{world=createWorld(container);}catch(error){
  for(const label of container.querySelectorAll('.node-label, #viewportHelp'))label.hidden=true;
  const note=document.createElement('p');note.className='empty-state';
  note.textContent='Máy chưa mở được hình 3D. Bạn vẫn có thể mô phỏng, đo Wi-Fi và đọc nhật ký.';
  container.append(note);document.getElementById('resetCamera').hidden=true;
}
const camera=world?createCamera(world.renderer,container):null;
if(world){
  const {scene,renderer}=world;
  const nodes=createNodes(scene);

  const packets=createPackets(scene,nodes);
  let previousPulse=0;
  function draw(now){
    const time=now/1000;camera.controls.update();updateNodes(nodes,state,time);
    if(state.running&&state.mode==='simulation'&&time-previousPulse>.75){
      previousPulse=time;
      // One illustrative fading block per animation; numerical evidence is Python Monte Carlo.
      const cfg=state.simulation?.config||{rate:.5,pathloss:2.2};
      const rho=10**(state.snr/10),d=state.relayPosition,tau=2**(2*cfg.rate)-1;
      const exponential=()=>-Math.log(Math.max(Number.EPSILON,Math.random()));
      const meanA=rho*d**(-cfg.pathloss),a=meanA*exponential(),b=rho*(1-d)**(-cfg.pathloss)*exponential();
      const protocol=state.protocol;
      if(protocol==='Direct')emitPulse('S','D',rho*exponential()>=2**cfg.rate-1,'MODEL',1.15);
      else{
        const decoded=protocol!=='DF'||a>=tau;
        emitPulse('S','R',decoded,'MODEL',.7);
        const gamma=protocol==='DF'?b:protocol==='AF-VG'?a*b/(a+b+1):a*b/(b+meanA+1);
        if(decoded)setTimeout(()=>{if(state.mode==='simulation'&&state.protocol===protocol)emitPulse('R','D',gamma>=tau,'MODEL',.7);},700);
      }
    }
    advanceReplay(time);packets.update(state,time);
    const w=container.clientWidth,h=container.clientHeight;
    for(const [id,node]of Object.entries(nodes)){
      const p=node.anchor.clone();p.y=2.9;p.project(camera.camera);
      const label=document.getElementById('label'+id);label.style.left=((p.x*.5+.5)*w)+'px';label.style.top=((-p.y*.5+.5)*h)+'px';label.style.display=p.z>1?'none':'flex';
    }
    renderer.render(scene,camera.camera);requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
}else{
  setInterval(()=>advanceReplay(performance.now()/1000),150);
}
setupUI(camera);
setupLogs();
window.relayLab={version:'2.6.1',state,renderer:world?.renderer,scene:world?.scene};
