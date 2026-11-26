import * as T from '/vendor/three.module.js';
import {part,group,box,soft,orb,line,mat} from './primitives.js';
const v=(x,y,z)=>new T.Vector3(x,y,z);
const A=v(-.85,1.29,1.04),B=v(.02,3.57,.99),C=v(.92,5.94,1.025),R=v(-2.30,.91,.58),G=v(3.66,2.30,1.62);
const colors={data:'#dd663e',ack:'#197e82',wifi:'#53948f',weak:'#c2a68b'};
function path(a,b,depth){
 return new T.CatmullRomCurve3([a.clone(),v(a.x+(b.x-a.x)*.27,a.y+(b.y-a.y)*.19,depth),v(a.x+(b.x-a.x)*.75,a.y+(b.y-a.y)*.77,depth),b.clone()]);
}
function dashes(parent,curve,color,count=15){
 const g=group(parent);for(let k=0;k<count;k++){
   const a=curve.getPointAt((k+.14)/count),b=curve.getPointAt((k+.71)/count);
   const geom=new T.CylinderGeometry(.029,.029,a.distanceTo(b),9);const dash=part(g,geom,color);dash.position.copy(a).add(b).multiplyScalar(.5);dash.quaternion.setFromUnitVectors(v(0,1,0),b.sub(a).normalize());dash.castShadow=false;
 }return g;
}
function envelope(parent,c,ack){
 const g=group(parent);soft(g,0,0,0,.58,.37,.083,.057,c);
 if(ack)line(g,[[-.128,.005,.069],[-.043,-.085,.079],[.157,.11,.067]],'#fff4d6',.026);
 else line(g,[[-.24,.125,.065],[0,-.022,.085],[.24,.125,.065]],'#fff2d3',.022);
 return g;
}
function globe(parent){
 const g=group(parent,G.x,G.y,G.z);orb(g,0,0,0,.49,.49,.49,'#407f83');
 for(const y of [-.22,0,.22]){const ring=part(g,new T.TorusGeometry(Math.sqrt(.492**2-y*y),.012,7,44),'#b8d5ba',0,y,0);ring.rotation.x=Math.PI/2;}
 for(let i=0;i<3;i++){const ring=part(g,new T.TorusGeometry(.496,.012,7,48),'#b8d5ba');ring.rotation.y=i*Math.PI/3;}
 const orbit=part(g,new T.TorusGeometry(.70,.017,8,64),'#d89958');orbit.rotation.set(1.22,0,.6);return g;
}
export function createTraffic(scene){
 const routes={ar:path(A,R,1.36),ab:path(A,B,1.85),bc:path(B,C,1.91),weak:path(R,C,2.08),rb:path(R,B,1.61),rg:path(R,G,2.78)};
 const lines={ab:dashes(scene,routes.ab,colors.data),bc:dashes(scene,routes.bc,colors.data),weak:dashes(scene,routes.weak,colors.weak,26),rb:dashes(scene,routes.rb,colors.wifi),rg:dashes(scene,routes.rg,colors.wifi,22)};
 const deviceRoute=[routes.ar,routes.rb,routes.bc];
 const dataPaths=deviceRoute.map(route=>dashes(scene,route,colors.data));
 const returnPaths=deviceRoute.map(route=>dashes(scene,route,colors.ack));
 const webReply=envelope(scene,colors.wifi,false);
 const data=envelope(scene,colors.data,false),ack=envelope(scene,colors.ack,true);const earth=globe(scene);
 const ripple=group(scene);const rings=[];
 for(let k=0;k<3;k++){
   const m=new T.MeshBasicMaterial({color:'#418b81',transparent:true,opacity:.44,depthWrite:false});rings.push(part(ripple,new T.TorusGeometry(1,.019,8,50),m));
 }
 function showPath(obj,route,f){obj.position.copy(route.getPointAt(T.MathUtils.clamp(f,0,1)));obj.rotation.set(0,.16,.08*Math.sin(f*Math.PI*2));}
 function travel(obj,points,f){
   const position=T.MathUtils.clamp(f,0,.99999)*points.length;
   const [route,back]=points[Math.floor(position)];
   const local=position%1;
   showPath(obj,route,back?1-local:local);
 }
 const outbound=deviceRoute.map(route=>[route,false]);
 const inbound=[[routes.bc,true],[routes.rb,true],[routes.rg,false]];
 const webReturn=[[routes.rg,true],[routes.rb,false],[routes.bc,false]];
 return {update(frame,t){
   const {shot,progress:p,slot,reverse,webProgress}=frame;
   const id=shot.id;
   for(const obj of [...Object.values(lines),...dataPaths,...returnPaths,data,ack,webReply,earth,ripple])obj.visible=false;
   const cycle=(t*.26)%1;
   if(id==='house'){lines.weak.visible=true;data.visible=cycle<.78;const f=Math.min(.68,cycle*.94);showPath(data,routes.weak,f);data.scale.setScalar(cycle<.64?1:Math.max(.08,(.78-cycle)/.14));}
   else if(id==='relay'){lines.rb.visible=p>.26;ripple.visible=p>.48;ripple.position.copy(B);}
   else if(id==='slots'){
     if(slot){
       const link=slot.first?'ab':'bc';lines[link].visible=true;data.visible=true;
       data.scale.setScalar(1);showPath(data,routes[link],slot.fraction);
     }
   }else if(id==='join'){lines.bc.visible=true;ripple.visible=true;ripple.position.copy(C);}
   else if(['data','ack','end'].includes(id)){
     const forward=id!=='ack';
     const obj=forward?data:ack;
     for(const dash of forward?dataPaths:returnPaths)dash.visible=true;
     obj.visible=true;obj.scale.setScalar(1);
     const localCycle=((t-shot.start)/4.2)%1;
     travel(obj,outbound,forward?localCycle:1-localCycle);
   }else if(id==='internet'){
     earth.visible=lines.bc.visible=lines.rb.visible=lines.rg.visible=true;earth.rotation.y=t*.31;
     const obj=reverse?webReply:data;obj.visible=true;obj.scale.setScalar(1);
     travel(obj,reverse?webReturn:inbound,Math.min(1,webProgress*1.16));
   }
   if(ripple.visible)for(let i=0;i<3;i++){const f=(t*.6+i/3)%1;const o=rings[i];o.scale.setScalar(.30+.62*f);o.material.opacity=.45*(1-f);o.rotation.y=.14;}
 }};
}
