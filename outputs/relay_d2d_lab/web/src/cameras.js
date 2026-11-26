import * as THREE from 'three';
import {OrbitControls} from '/vendor/OrbitControls.js';

export function createCamera(renderer,container){
  const camera=new THREE.PerspectiveCamera(39,1,.1,100);
  camera.position.set(4.6,6.3,13.7);
  const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,.7,0);
  controls.enableDamping=true;controls.dampingFactor=.06;controls.minDistance=6;controls.maxDistance=26;
  controls.maxPolarAngle=Math.PI*.48;controls.update();
  const resize=()=>{const {width,height}=container.getBoundingClientRect();camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height);};
  new ResizeObserver(resize).observe(container);resize();
  return {camera,controls,reset(){camera.position.set(4.6,6.3,13.7);controls.target.set(0,.7,0);controls.update();}};
}
