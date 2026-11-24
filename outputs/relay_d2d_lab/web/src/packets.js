import * as THREE from 'three';

export function createPackets(scene,nodes){
  const group=new THREE.Group();scene.add(group);
  const meshes=new Map();
  const curves={};
  for(const [from,to] of [['S','R'],['R','D'],['S','D']]){
    const geom=new THREE.BufferGeometry().setFromPoints([nodes[from].anchor,nodes[to].anchor]);
    const line=new THREE.Line(geom,new THREE.LineDashedMaterial({color:from==='S'&&to==='D'?'#546e89':'#328f86',dashSize:.15,gapSize:.10,transparent:true,opacity:.5}));
    line.computeLineDistances();scene.add(line);curves[`${from}${to}`]={line,from,to};
  }
  function curve(from,to){
    const a=nodes[from].anchor.clone(),b=nodes[to].anchor.clone();
    const middle=a.clone().lerp(b,.5);middle.y+=from==='D'?2:1.0;
    return new THREE.QuadraticBezierCurve3(a,middle,b);
  }
  return {update(state,time){
    for(const path of Object.values(curves)){
      path.line.geometry.dispose();path.line.geometry=new THREE.BufferGeometry().setFromPoints(curve(path.from,path.to).getPoints(64));path.line.computeLineDistances();
      path.line.material.opacity=path.to==='D'&&path.from==='S'?(state.protocol==='Direct'?.65:.18):.5;
    }
    const alive=new Set();
    state.pulses=state.pulses.filter(p=>time-p.start<p.duration);
    for(const p of state.pulses){
      alive.add(p.id);let m=meshes.get(p.id);
      if(!m){m=new THREE.Mesh(new THREE.SphereGeometry(.065,12,8),new THREE.MeshBasicMaterial({color:p.success?(p.from==='D'?'#eacb72':'#66ffe0'):'#ff6e79'}));group.add(m);meshes.set(p.id,m);}
      const t=Math.max(0,Math.min(1,(time-p.start)/p.duration));
      m.position.copy(curve(p.from,p.to).getPoint(t));
      if(!p.success){m.scale.setScalar(1+t*3);m.material.transparent=true;m.material.opacity=1-t;}
    }
    for(const [id,m]of meshes)if(!alive.has(id)){group.remove(m);m.geometry.dispose();m.material.dispose();meshes.delete(id);}
  }};
}
