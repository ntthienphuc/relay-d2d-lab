import {createChannels} from './channels.js';import {makeWorld} from './world.js';import {aim} from './cameras.js';import {createTraffic} from './packets.js';import {at,duration} from './state.js';import {updateHUD} from './ui.js';
const world=makeWorld(document.querySelector('canvas'));const traffic=createTraffic(world.scene);const channels=createChannels(world.scene);
function render(time){
 const t=Math.min(duration,Math.max(0,time));const f=at(t),id=f.shot.id;
 const theory=id==='af'||id==='df';world.house.visible=id!=='bench'&&!theory;world.bench.visible=id==='bench';
 const [a,b,c]=world.heroes;
 b.g.visible=id!=='house';const base=2.665;
 const enter=id==='relay'?Math.max(0,1-(t-f.shot.start)/1.05):0;
 b.g.position.y=base+enter*enter*1.22;b.g.rotation.z=enter*Math.sin(enter*Math.PI)*.15;
 for(const [index,h] of [...world.heroes,...world.labHeroes].entries()){
   const blink=Math.max(.14,Math.min(1,Math.abs(((t+index*.59)%3.33)-.12)*12));
   for(const eye of h.eyes)eye.scale.y=.082*blink;
 }
 if(id==='join')c.g.rotation.z=.035*Math.sin(t*2.35);else c.g.rotation.z=0;
 channels(id,t,f.phaseChanged);traffic.update(f,t);aim(world.cam,id,f.progress,t);
 if(render.last!==id||enter>0){world.renderer.shadowMap.needsUpdate=true;render.last=id;}
 world.renderer.render(world.scene,world.cam);updateHUD(f,t,world.cam);
}
window.film={render,duration,world};render(0);
if(!location.search.includes('capture')){const start=performance.now();function tick(now){render((now-start)/1000%duration);requestAnimationFrame(tick);}requestAnimationFrame(tick);}
