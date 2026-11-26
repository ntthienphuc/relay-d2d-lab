import * as T from '/vendor/three.module.js';
import {group,soft,box,orb,cyl,part,mat} from './primitives.js';
import {board} from './characters.js';
const points=161,sides=6;
function waveform(parent,color){
 const pos=new Float32Array(points*sides*3),index=[];
 for(let i=0;i<points-1;i++)for(let j=0;j<sides;j++){
   const a=i*sides+j,b=i*sides+(j+1)%sides,c=a+sides,d=b+sides;index.push(a,c,b,b,c,d);
 }
 const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(pos,3));geometry.setIndex(index);
 const mesh=new T.Mesh(geometry,new T.MeshBasicMaterial({color,side:T.DoubleSide}));parent.add(mesh);mesh.frustumCulled=false;
 return (samples,blank)=>{
   mesh.visible=!blank;
   for(let i=0;i<points;i++){
    const slope=(samples[Math.min(points-1,i+1)]-samples[Math.max(0,i-1)])/(3.84/(points-1));
    const ny=.022/Math.sqrt(1+slope*slope),nx=-slope*ny;
    for(let j=0;j<sides;j++){
     const cs=Math.cos(j/sides*2*Math.PI),sn=Math.sin(j/sides*2*Math.PI),k=3*(i*sides+j);
     pos[k]=-1.006+2.012*i/(points-1)+nx*cs;pos[k+1]=samples[i]+ny*cs;pos[k+2]=.143+.022*sn;
    }
   }
   geometry.attributes.position.needsUpdate=true;
 };
}
function scope(parent,x,color){
 const g=group(parent,x,1.41,.14);soft(g,0,0,0,2.47,1.56,.24,.13,'#536e6a');
 soft(g,0,.075,.141,2.25,1.26,.034,.075,'#213f45');
 for(let k=-3;k<=3;k++)box(g,k*.285,.08,.173,.009,1.07,.005,'#406068');
 for(let k=-2;k<=2;k++)box(g,0,.08+k*.20,.173,2.10,.010,.005,k===0?'#608380':'#42666a');
 for(const sign of [-1,1])box(g,sign*.72,-.916,-.019,.11,.35,.31,'#5b716b');
 for(let i=0;i<3;i++)orb(g,-.86+i*.13,-.644,.145,.031,.031,.018,i===0?color:'#abb7a3');
 const axis=group(g,0,.08,.054);return waveform(axis,color);
}
export function createChannels(scene){
 const g=group(scene,-18,0,0);soft(g,0,.17,.08,7.76,.31,2.8,.16,'#c5ae8d');
 const left=scope(g,-2.02,'#efbb79'),right=scope(g,2.02,'#94e3db');
 const b=board(g);b.g.position.set(0,.34,.26);b.g.scale.setScalar(.98);
 const lamp=orb(g,.53,.60,.51,.062,.062,.062,'#71bca4');
 return (id,t,progress)=>{
   g.visible=id==='af'||id==='df';if(!g.visible)return false;
   const input=[],output=[],bits=[1,-1,1,1,-1,-1,1,-1];
   const failed=id==='df'&&progress>=.58;
   for(let i=0;i<points;i++){
    const x=i/(points-1),ph=x*2*Math.PI,clock=t*.95;
    const noise=.048*Math.sin(ph*15.2+clock*2.3)+.029*Math.sin(ph*24.4-clock*4.2)+.018*Math.cos(ph*33.3+clock);
    if(id==='af'){
     const sample=.146*Math.sin(ph*2+clock)+.059*Math.sin(ph*3.7-clock*.55)+noise;
     input.push(sample);output.push(sample*(progress<.64?1.63:1.45+.23*Math.sin(clock)));
    }else{
     const bit=bits[Math.min(7,Math.floor(x*8))];
     input.push(bit*(failed?.055:.192)+noise*(failed?2.8:1.42));output.push(bit*.269);
    }
   }
   lamp.material=mat(failed?'#d26945':'#71bca4');
   left(input,false);right(output,failed);return failed;
 };
}
