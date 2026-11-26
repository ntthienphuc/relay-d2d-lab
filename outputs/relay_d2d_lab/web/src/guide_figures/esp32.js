import * as THREE from 'three';

// Product concept for the physical relay; no claim that this enclosure was built.
export function createRelayBox(){
  const root=new THREE.Group();
  const mat=(color,metalness=.15,roughness=.5)=>new THREE.MeshStandardMaterial({color,metalness,roughness});
  const plastic=mat('#e7edef'),edge=mat('#c3d0d5',.5),pcb=mat('#1c2c75'),metal=mat('#a8b9bf',.85,.28),dark=mat('#29414b');
  const box=(w,h,d,m,x,y,z,parent=root)=>{const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;};
  box(1.8,.42,1.3,plastic,0,.3,0);box(1.85,.06,1.35,edge,0,.08,0);
  box(1.5,.025,1.03,pcb,0,.53,0);
  box(.57,.13,.57,metal,-.3,.61,-.12);box(.32,.07,.22,dark,.28,.58,-.15);
  // GPIO headers, antenna trace and USB connector make the board recognisable.
  for(const z of [-.44,.44])for(let i=0;i<12;i++){
    box(.065,.09,.08,dark,-.65+i*.116,.58,z);
    box(.025,.06,.025,metal,-.65+i*.116,.65,z);
  }
  const gold=mat('#c7a758',.7,.35);
  for(let i=0;i<5;i++)box(.15,.012,.022,gold,.36+(i%2)*.07,.55,-.35+i*.08);
  box(.24,.13,.15,metal,-.91,.32,0);box(.16,.07,.155,dark,-.93,.32,0);
  // Raised instrument panel: two double-digit displays and two buttons.
  box(1.4,.46,.2,plastic,0,.87,.38);
  const segments=[[-.045,.065,.06,.012],[.045,.065,.012,.065],[-.045,0,.06,.012],[-.045,-.065,.06,.012],[-.06,-.03,.012,.065],[.045,-.03,.012,.065],[-.06,.035,.012,.065]];
  const led=new THREE.MeshStandardMaterial({color:'#2f47b0',emissive:'#2f47b0',emissiveIntensity:.45});
  for(const center of [-.36,.36]){
    box(.56,.27,.025,dark,center,.9,.49);
    for(const dx of [-.12,.12])for(const [sx,sy,w,h]of segments)box(w,h,.009,led,center+dx+sx,.9+sy,.508);
  }
  for(const x of [-.35,.35]){
    const b=new THREE.Mesh(new THREE.CylinderGeometry(.09,.1,.04,24),mat('#344fc5'));
    b.rotation.x=Math.PI/2;b.position.set(x,.65,.51);root.add(b);
  }
  for(const x of [-.78,.78])for(const z of [-.55,.55]){
    const screw=new THREE.Mesh(new THREE.CylinderGeometry(.035,.035,.02,12),metal);screw.position.set(x,.52,z);root.add(screw);
    box(.04,.005,.008,dark,x,.532,z);
  }
  for(let i=0;i<6;i++)box(.1,.04,.01,dark,-.4+i*.16,.24,.656);
  return root;
}
