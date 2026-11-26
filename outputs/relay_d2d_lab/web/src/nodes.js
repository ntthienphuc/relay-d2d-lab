import * as THREE from 'three';
import {createRelayBox} from './esp32.js';

function material(color,metalness=.3,roughness=.45){return new THREE.MeshStandardMaterial({color,metalness,roughness});}
function box(parent,w,h,d,mat,x=0,y=0,z=0){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
function phone(color){
  const g=new THREE.Group(),frame=material('#8293aa',.8,.25),body=material('#111c2c',.6,.25);
  box(g,1.12,2.15,.12,frame,0,1.18,0);box(g,1.07,2.10,.14,body,0,1.18,.01);
  const screen=new THREE.MeshStandardMaterial({color:'#10293b',emissive:color,emissiveIntensity:.16,roughness:.24,metalness:.4});
  box(g,.99,1.81,.015,screen,0,1.19,.092);
  box(g,.28,.025,.02,material('#a5b4c4'),0,2.16,.09);
  const lens=new THREE.Mesh(new THREE.CylinderGeometry(.025,.025,.02,16),material('#3c7dab'));lens.rotation.x=Math.PI/2;lens.position.set(.32,2.16,.095);g.add(lens);
  box(g,.025,.28,.04,frame,.575,1.58,0);box(g,.025,.2,.04,frame,-.575,1.6,0);
  for(let i=0;i<4;i++)box(g,.15,.05+i*.04,.02,material(color),-.31+i*.2,1.62,.11);
  for(let i=0;i<5;i++)box(g,.65-(i%2)*.15,.022,.02,material('#55798e'),0,1.25-i*.13,.11);
  box(g,.38,.16,.022,material(color),0,.55,.11);
  const stand=box(g,.8,.1,.6,material('#30455b'),0,.11,.05);
  g.rotation.x=-.08;return g;
}
function laptop(){
  const g=new THREE.Group(),alloy=material('#667f99',.8,.3);
  box(g,2.15,.12,1.5,alloy,0,.18,.2);
  box(g,.6,.008,.32,material('#3c526b'),0,.248,.66);
  for(let row=0;row<4;row++)for(let col=0;col<12;col++)box(g,.115,.012,.105,material('#1b2c3c'),-.87+col*.157,.253,-.33+row*.14);
  const lid=new THREE.Group();lid.position.set(0,.23,-.54);lid.rotation.x=-.15;g.add(lid);
  box(lid,2.15,1.4,.08,alloy,0,.7,0);box(lid,1.99,1.21,.012,material('#0a1d2c'),0,.72,.048);
  for(let i=0;i<7;i++)box(lid,1.3-(i%3)*.25,.025,.015,material(i%3?'#4f768d':'#405cd9'),-.13,.26+i*.13,.06);
  return g;
}

export function createNodes(scene){
  const nodes={};
  for(const [id,color,x,z] of [['S','#2f4652',-4.4,0],['R','#ef652e',0,-.7],['D','#7464a3',4.4,0]]){
    const g=new THREE.Group();g.position.set(x,.2,z);const device=id==='S'?laptop():phone(color);g.add(device);scene.add(g);
    let alternate=id==='D'?laptop():id==='R'?createRelayBox():phone(color);alternate.visible=false;g.add(alternate);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(1,.018,8,64),new THREE.MeshBasicMaterial({color}));
    ring.rotation.x=Math.PI/2;ring.position.y=.02;g.add(ring);
    const light=new THREE.PointLight(color,3,3);light.position.set(0,.6,.5);g.add(light);
    nodes[id]={group:g,device,alternate,ring,light,color,anchor:new THREE.Vector3(x,1.5,z)};
  }
  return nodes;
}

export function updateNodes(nodes,state,time){
  const relayX=-4.4+8.8*(state.mode==='simulation'?state.relayPosition:.5);
  const config=state.activeRun?.config||state.preview;
  const laptopSink=state.mode!=='simulation'&&config?.destination_id==='laptop';
  nodes.D.device.visible=!laptopSink;nodes.D.alternate.visible=laptopSink;
  const androidSource=state.mode!=='simulation'&&config?.source_id&&config.source_id!=='laptop';
  nodes.S.device.visible=!androidSource;nodes.S.alternate.visible=!!androidSource;
  const relay=state.status?.devices?.find(d=>d.id===state.activeRun?.config?.relay_id);
  const esp=(state.mode==='simulation'||relay?.platform==='esp32'||config?.relay_kind==='esp32'||String(state.activeRun?.config?.relay_id).startsWith('esp32-'));
  nodes.R.device.visible=!esp;nodes.R.alternate.visible=!!esp;
  nodes.R.group.position.x=relayX;nodes.R.anchor.x=relayX;
  for(const node of Object.values(nodes)){
    node.ring.material.opacity=.55+.25*Math.sin(time*2);node.ring.material.transparent=true;
    node.light.intensity=2.3+.5*Math.sin(time*1.8);
  }
}
