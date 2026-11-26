import * as THREE from '/vendor/three.module.js';

export function makeWorld() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#f4f0e7');
  scene.add(new THREE.HemisphereLight('#fff9ed','#9d9583',2.55));
  const key = new THREE.DirectionalLight('#fff8ed',3.0);
  key.position.set(-3,6,4);
  key.castShadow = true;
  key.shadow.mapSize.set(2048,1024);
  Object.assign(key.shadow.camera,{left:-12,right:12,top:7,bottom:-7,near:.2,far:17});
  key.shadow.normalBias = .025;
  scene.add(key);
  const plane = new THREE.Mesh(
    new THREE.PlaneGeometry(32,18),
    new THREE.MeshStandardMaterial({color:'#f4f0e7',roughness:1})
  );
  plane.rotation.x = -Math.PI/2;
  plane.position.y=-.01;
  plane.receiveShadow=true;
  scene.add(plane);
  return scene;
}

