import * as T from '/vendor/three.module.js';
import {group,soft,box,orb,cyl,line,mat,contact,part} from './primitives.js';
import {phone,router,board,laptop,plant} from './characters.js';
export const levels=[0,2.33,4.66];
function windowFrame(p,x,y,z,w=1.1){
  soft(p,x,y,z,w,1.01,.05,.05,'#faf1ce');soft(p,x,y,z+.047,w-.135,.88,.045,.035,'#99c3c0');
  box(p,x,y,z+.091,.044,.87,.034,'#fff0cb');box(p,x,y,z+.091,w-.12,.043,.034,'#fff0cb');
  box(p,x,y-.512,z+.072,w+.14,.08,.18,'#bb886a');
}
function lamp(p,x,y,z){
  cyl(p,x,y+.05,z,.21,.24,.09,'#94816f');cyl(p,x,y+.62,z,.025,.025,1.11,'#92795f');
  cyl(p,x,y+1.21,z,.14,.31,.38,'#eab266');
}
function sofa(p,x,y,z){
  soft(p,x,y+.25,z,1.33,.29,.54,.09,'#bd6c51');soft(p,x,y+.51,z-.22,1.3,.57,.15,.10,'#d78a68');
  for(const s of [-1,1])soft(p,x+s*.61,y+.385,z,.18,.35,.60,.075,'#ca795a');
  const c=soft(p,x-.24,y+.50,z+.018,.37,.34,.13,.08,'#f3cb86');c.rotation.z=-.18;
}
function shelf(p,x,y,z){
  box(p,x,y+.49,z,1.57,.09,.45,'#ab7858');for(const sign of [-1,1])box(p,x+sign*.60,y+.23,z,.07,.47,.29,'#967555');
  for(let i=0;i<5;i++){const h=.23+.05*(i%3);box(p,x-.48+i*.12,y+.55+h/2,z-.02,.09,h,.22,['#587979','#dda576','#8ea194'][i%3]);}
  plant(p,x+.43,y+.54,z,.50);
}
function tree(p,x,y,z,r){
 const g=group(p,x,y,z);g.scale.setScalar(r);cyl(g,0,.44,0,.10,.13,.88,'#947362');orb(g,0,1.10,0,.47,.66,.43,'#789d92');orb(g,-.26,.93,.05,.28,.34,.30,'#8aab98');
}
export function makeWorld(canvas){
 const renderer=new T.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});renderer.setSize(1440,810,false);renderer.setPixelRatio(1);
 renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.14;
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
 const scene=new T.Scene();scene.background=new T.Color('#eee5d3');scene.fog=new T.FogExp2('#eee5d3',.027);
 const hemi=new T.HemisphereLight('#fff2d8','#b5b8b1',2.36);scene.add(hemi);
 const sun=new T.DirectionalLight('#fff1d4',3.1);sun.position.set(-6,11,9);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-11,right:11,top:12,bottom:-8,near:.1,far:44});sun.shadow.normalBias=.028;sun.shadow.bias=-.00035;scene.add(sun);
 const fill=new T.DirectionalLight('#c8e2ed',1.18);fill.position.set(7,7,-5);scene.add(fill);
 const cam=new T.PerspectiveCamera(31,1440/810,.1,170);
 const ground=box(scene,0,-.32,0,130,.35,130,'#e2d7c0');
 const house=group(scene);box(house,0,-.047,0,6.75,.31,3.40,'#b4b5a2');box(house,0,.069,0,6.68,.145,3.33,'#c7c7af');
 for(let i=0;i<3;i++){
   const h=levels[i];box(house,0,h+.185,0,6.38,.20,3.13,'#b78e6b');box(house,0,h+.294,0,6.39,.057,3.15,'#e2c298');
   box(house,0,h+1.27,-1.45,6.28,2.19,.12,['#e3d7b7','#d0dcce','#e8c9b2'][i]);
   box(house,-3.075,h+1.26,-.37,.12,2.12,2.09,['#d4bd9c','#b7c8b7','#d6b49d'][i]);
   box(house,0,h+.422,-1.345,6.18,.145,.055,'#b6a68e');
   for(let j=0;j<13;j++)box(house,-2.91+j*.477,h+.325,0,.012,.006,3.02,'#c7a985');
   windowFrame(house,1.96,h+1.49,-1.354,1.28);windowFrame(house,-1.82,h+1.50,-1.354,.97);
 }
 box(house,0,7.045,-1.37,6.52,.17,.41,'#bc8d6d');box(house,-3.065,7.04,-.43,.20,.17,2.21,'#bc8d6d');
 sofa(house,1.61,.33,-.69);shelf(house,-1.70,2.66,-.65);lamp(house,2.52,2.66,-.48);sofa(house,-1.51,4.99,-.68);
 plant(house,2.56,.33,.76,1.18);plant(house,-2.55,2.66,.71,.9);plant(house,2.64,4.99,-.52,.9);
 tree(scene,-4.32,-.14,-.92,1.37);tree(scene,-4.99,-.14,-1.74,.78);tree(scene,4.33,-.14,-2.75,1.14);
 for(let i=0;i<10;i++){const x=-21+i*4.1,z=-17-(i%3)*2.74,h=1.8+(i*7%4)*.97;box(scene,x,h/2-.18,z,2.28,h,1.6,'#c9ccba');}
 const a=phone(house,'#f4c885'),b=board(house),c=phone(house,'#93c8bf');
 a.g.position.set(-.85,.335,.76);b.g.position.set(.02,2.665,.70);c.g.position.set(.92,4.995,.74);
 a.g.rotation.y=-.085;b.g.rotation.y=-.10;c.g.rotation.y=-.08;
 const wifi=router(house);wifi.position.set(-2.30,.339,.32);wifi.rotation.y=.10;
 for(const hero of [a,b,c])contact(house,hero.g.position.x,hero.g.position.y+.008,hero.g.position.z,.83,.58);
 const bench=group(scene,17,0,0);const surface=soft(bench,0,.16,0,6.62,.32,3.02,.20,'#d4b58e');
 for(const x of [-2.27,2.27])for(const z of [-.92,.92])box(bench,x,-.03,z,.20,.34,.19,'#9f8265');
 const labpc=laptop(bench);labpc.position.set(-1.79,.353,.08);const labboard=board(bench);labboard.g.position.set(.26,.353,.09);const labphone=phone(bench,'#93c8bf');labphone.g.position.set(2.02,.353,.12);
 for(const x of [-1.79,.26,2.02])contact(bench,x,.355,.15,.83,.46);
 renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
 return {scene,renderer,cam,house,bench,heroes:[a,b,c],labHeroes:[labboard,labphone],wifi};
}
