import * as THREE from 'three';

export function createWorld(container){
  const scene=new THREE.Scene();scene.background=new THREE.Color('#f1f4f6');
  scene.fog=new THREE.Fog('#f1f4f6',19,42);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;
  container.appendChild(renderer.domElement);
  scene.add(new THREE.HemisphereLight('#ffffff','#abb9c4',2.4));
  const key=new THREE.DirectionalLight('#d1e8ff',3.0);key.position.set(-3,10,5);key.castShadow=true;
  key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-10,right:10,top:8,bottom:-8,near:.1,far:30});scene.add(key);
  const rim=new THREE.PointLight('#40d9b8',35,18);rim.position.set(3,5,-4);scene.add(rim);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(70,70),new THREE.MeshStandardMaterial({color:'#e9eef1',roughness:.85,metalness:.05}));
  floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);
  const grid=new THREE.GridHelper(30,60,'#c7d4db','#dce4e9');grid.position.y=.006;scene.add(grid);
  const stage=new THREE.Mesh(new THREE.BoxGeometry(13,.18,7.5),new THREE.MeshStandardMaterial({color:'#f7f8fa',metalness:.08,roughness:.7}));
  stage.position.set(0,.1,0);stage.receiveShadow=true;stage.castShadow=true;scene.add(stage);
  // Architectural cutaway: pillars, glass back wall, ceiling rails.
  const structure=new THREE.Group();scene.add(structure);
  const steel=new THREE.MeshStandardMaterial({color:'#b6c5cf',metalness:.4,roughness:.6});
  for(const x of [-6.3,6.3]){
    const pillar=new THREE.Mesh(new THREE.BoxGeometry(.12,3.8,.12),steel);pillar.position.set(x,2,-3.6);structure.add(pillar);
    const foot=new THREE.Mesh(new THREE.BoxGeometry(.42,.1,.42),steel);foot.position.set(x,.24,-3.6);structure.add(foot);
  }
  const rail=new THREE.Mesh(new THREE.BoxGeometry(12.7,.1,.1),steel);rail.position.set(0,3.9,-3.6);structure.add(rail);
  const glass=new THREE.Mesh(new THREE.PlaneGeometry(12.5,3.4),new THREE.MeshStandardMaterial({color:'#4a7397',transparent:true,opacity:.055,side:THREE.DoubleSide,depthWrite:false}));
  glass.position.set(0,2,-3.62);structure.add(glass);
  for(let i=-6;i<=6;i+=2){const divider=new THREE.Mesh(new THREE.BoxGeometry(.025,3.3,.025),steel);divider.position.set(i,2,-3.6);structure.add(divider);}
  return {scene,renderer};
}
