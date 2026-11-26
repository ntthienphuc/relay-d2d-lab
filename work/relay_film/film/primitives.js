import * as T from '/vendor/three.module.js';
const mats=new Map();
export function mat(color,metalness=0,roughness=.62){
  const key=[color,metalness,roughness].join('/');
  if(!mats.has(key))mats.set(key,new T.MeshStandardMaterial({color,metalness,roughness}));
  return mats.get(key);
}
export function part(parent,geo,color,x=0,y=0,z=0){
  const mesh=new T.Mesh(geo,color?.isMaterial?color:mat(color));
  mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;
}
export function group(parent,x=0,y=0,z=0){
  const g=new T.Group();g.position.set(x,y,z);parent.add(g);return g;
}
export function box(p,x,y,z,w,h,d,c){return part(p,new T.BoxGeometry(w,h,d),c,x,y,z);}
export function orb(p,x,y,z,rx,ry,rz,c){const m=part(p,new T.SphereGeometry(1,20,16),c,x,y,z);m.scale.set(rx,ry,rz);return m;}
export function cyl(p,x,y,z,rt,rb,h,c,n=32){return part(p,new T.CylinderGeometry(rt,rb,h,n),c,x,y,z);}
export function soft(p,x,y,z,w,h,d,r,c){
  const s=new T.Shape(), hw=w/2-r,hh=h/2-r;
  s.moveTo(-hw,-h/2);s.lineTo(hw,-h/2);s.quadraticCurveTo(w/2,-h/2,w/2,-hh);s.lineTo(w/2,hh);s.quadraticCurveTo(w/2,h/2,hw,h/2);s.lineTo(-hw,h/2);s.quadraticCurveTo(-w/2,h/2,-w/2,hh);s.lineTo(-w/2,-hh);s.quadraticCurveTo(-w/2,-h/2,-hw,-h/2);
  const geo=new T.ExtrudeGeometry(s,{depth:d,bevelEnabled:true,bevelThickness:Math.min(.025,d*.15),bevelSize:Math.min(.025,r*.2),bevelSegments:3,curveSegments:6});
  return part(p,geo,c,x,y,z-d/2);
}
export function line(p,points,color,r=.021){
  const pts=points.map(a=>new T.Vector3(...a));const path=new T.CatmullRomCurve3(pts,false,'centripetal');
  return part(p,new T.TubeGeometry(path,Math.max(10,pts.length*5),r,7,false),color);
}
export function contact(p,x,y,z,rx,rz){
  const n=64,buf=new Uint8Array(n*n*4);
  for(let j=0;j<n;j++)for(let i=0;i<n;i++){
    const u=(i+.5)/n*2-1,v=(j+.5)/n*2-1,k=(j*n+i)*4;
    buf[k]=74;buf[k+1]=50;buf[k+2]=38;buf[k+3]=Math.round(58*Math.max(0,1-u*u-v*v)**2);
  }
  if(!contact.texture){const map=new T.DataTexture(buf,n,n);map.magFilter=T.LinearFilter;map.needsUpdate=true;contact.texture=map;}
  const m=new T.Mesh(new T.PlaneGeometry(rx*2,rz*2),new T.MeshBasicMaterial({map:contact.texture,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1}));m.rotation.x=-Math.PI/2;m.position.set(x,y,z);p.add(m);return m;
}
