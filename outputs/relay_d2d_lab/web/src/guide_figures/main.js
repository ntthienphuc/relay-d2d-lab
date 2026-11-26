import * as THREE from '/vendor/three.module.js';
import {makeWorld} from './world.js';
import {makeDevice} from './devices.js';
import {state} from './state.js';

const viewport = document.querySelector('#fig');
const labels = document.querySelector('#labels');
const width = viewport.clientWidth, height = viewport.clientHeight;
const scene = makeWorld();
const camera = new THREE.OrthographicCamera(-8.5,8.5,8.5*height/width,-8.5*height/width,.1,60);
camera.position.set(0,3.7,11.4);
camera.lookAt(0,.48,0);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(width,height);
renderer.setPixelRatio(devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.1;
viewport.append(renderer.domElement);

const positions = [], n = state.nodes.length, gridWidth = 16;
labels.style.gridTemplateColumns='repeat('+n+',1fr)';
for (const [i,spec] of state.nodes.entries()) {
  const x = -gridWidth/2 + gridWidth * (i+.5)/n;
  const item = makeDevice(spec);
  item.position.set(x,0,0);
  scene.add(item);
  positions.push(x);
  const label = document.createElement('div');
  label.className='label';
  const name = document.createElement('strong'), detail = document.createElement('span');
  name.textContent=spec.label; detail.textContent=spec.detail;
  label.append(name,detail); labels.append(label);
}

const arcs=[];
for (let i=1;i<positions.length;i++) {
  const a=positions[i-1]+.97, b=positions[i]-.97;
  const arc = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(a,.42,.1),new THREE.Vector3((a+b)/2,.64,.1),new THREE.Vector3(b,.42,.1)
  );
  const line = new THREE.Mesh(new THREE.TubeGeometry(arc,24,.022,8,false),new THREE.MeshBasicMaterial({color:'#a04b26'}));
  scene.add(line);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(.085,.24,12),new THREE.MeshBasicMaterial({color:'#a04b26'}));
  tip.position.copy(arc.getPoint(1));
  tip.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),arc.getTangent(1).normalize());
  scene.add(tip);
  const packet=new THREE.Mesh(new THREE.SphereGeometry(.058,12,10),new THREE.MeshBasicMaterial({color:'#e56f34'}));
  scene.add(packet);
  arcs.push({arc,packet});
}
function frame(t) {
  for (const [i,{arc,packet}] of arcs.entries()) packet.position.copy(arc.getPoint((t/1400+i*.25)%1));
  renderer.render(scene,camera);
  if (state.running) requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
window.figureReady = true;

