import * as THREE from '/vendor/three.module.js';
import {createRelayBox} from './esp32.js';

const material = (color, roughness=.48) => new THREE.MeshStandardMaterial({color,roughness});
const caseDark = material('#303539');
const screen = material('#1c303a',.3);
const edge = material('#a4a49f');
const graphite = material('#5c605c');
const cream = material('#e0dcd1');
const orange = material('#f08555');
const blue = material('#76acb6');
function block(parent,size,position,mat) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size),mat);
  mesh.position.set(...position);
  mesh.castShadow = mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}

function phone() {
  const node = new THREE.Group();
  const housing = new THREE.Group();
  housing.position.y = .1;
  housing.rotation.y = -.26;
  housing.rotation.x = -.10;
  node.add(housing);
  block(housing,[.83,1.59,.14],[0,.94,0],edge);
  block(housing,[.77,1.52,.024],[0,.94,.078],caseDark);
  block(housing,[.68,1.34,.02],[0,.93,.096],screen);
  block(housing,[.22,.025,.025],[0,1.63,.108],edge);
  for (let i=0;i<4;i++) {
    const w=.38+i%2*.09;
    block(housing,[w,.03,.02],[-.23+w/2,1.18-i*.095,.11],blue);
  }
  block(node,[.99,.07,.77],[0,.06,0],graphite);
  return node;
}

function laptop() {
  const node = new THREE.Group();
  node.rotation.y=-.24;
  block(node,[1.68,.11,1.15],[0,.12,.1],edge);
  for (let row=0;row<4;row++)
    for (let col=0;col<11;col++)
      block(node,[.11,.022,.10],[-.7+col*.14,.184,-.33+row*.115],caseDark);
  block(node,[.458,.012,.24],[0,.184,.46],graphite);
  const lid=new THREE.Group();
  lid.position.set(0,.17,-.46);
  lid.rotation.x=-.20;
  node.add(lid);
  block(lid,[1.68,1.14,.075],[0,.58,0],graphite);
  block(lid,[1.52,.99,.024],[0,.58,.05],screen);
  for(let row=0;row<4;row++) block(lid,[.63+row%2*.28,.026,.016],[ -.24,.84-row*.14,.071],row===0?orange:blue);
  return node;
}

function accessPoint() {
  const node = new THREE.Group();
  node.rotation.y=-.24;
  block(node,[1.49,.32,.86],[0,.24,0],cream);
  block(node,[1.38,.13,.76],[0,.11,0],graphite);
  for (const [x,angle] of [[-.54,.19],[.54,-.19]]) {
    const antenna=new THREE.Mesh(new THREE.CylinderGeometry(.037,.045,1,16),graphite);
    antenna.position.set(x,.83,-.26);
    antenna.rotation.z=angle;
    antenna.castShadow=true;
    node.add(antenna);
  }
  for (let i=0;i<5;i++) block(node,[.06,.029,.02],[-.29+i*.14,.26,.437],i===0?orange:blue);
  for (let i=0;i<7;i++) block(node,[.063,.017,.33],[-.42+i*.14,.407,-.04],edge);
  return node;
}

export function makeDevice(spec) {
  if(spec.kind==='pc')return laptop();
  if(spec.kind==='ap')return accessPoint();
  if(spec.kind==='esp')return createRelayBox();
  return phone();
}

