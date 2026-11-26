import {group,soft,box,orb,cyl,line,mat,contact} from './primitives.js';
const ink='#213a40';
function feet(g,w){for(const s of [-1,1])orb(g,s*w,.085,.045,.14,.082,.18,'#34464c');}
function face(g,w,y,z){
  const eyes=[];for(const s of [-1,1]){
    eyes.push(orb(g,s*w,y,z,.058,.082,.037,ink));orb(g,s*(w+.1),y-.10,z-.012,.065,.031,.018,'#e8a090');
  }
  line(g,[[-.117,y-.096,z+.012],[0,y-.153,z+.024],[.117,y-.096,z+.012]],ink,.018);
  return eyes;
}
export function phone(parent,color='#efbd76'){
  const g=group(parent);feet(g,.21);
  soft(g,0,.81,0,.84,1.34,.18,.13,mat('#33464d',.19,.48));
  soft(g,0,.81,.107,.72,1.21,.035,.105,color);
  soft(g,0,1.32,.135,.21,.045,.012,.016,ink);
  soft(g,0,.296,.138,.24,.027,.012,.012,'#fff1cc');
  const eyes=face(g,.145,.86,.158);
  for(let i=0;i<3;i++)box(g,-.235+i*.045,1.20+i*.016,.152,.025,.045+i*.032,.01,'#49645e');
  return {g,eyes};
}
export function router(parent){
  const g=group(parent);feet(g,.47);soft(g,0,.29,0,1.43,.33,.71,.12,'#fff2ce');
  for(const sign of [-1,1]){const a=group(g,sign*.48,.43,-.16);a.rotation.z=-sign*.13;cyl(a,0,.36,0,.045,.052,.72,'#334d58');orb(a,0,.73,0,.045,.05,.045,'#334d58');}
  for(let i=0;i<4;i++)orb(g,-.36+.15*i,.29,.368,.03,.03,.012,i===3?'#e88751':'#43988b');
  return g;
}
export function board(parent){
  const g=group(parent);feet(g,.31);
  soft(g,0,.78,0,1.06,1.3,.12,.09,'#24525c');
  for(const s of [-1,1])for(let i=0;i<8;i++){
    box(g,s*.529,.30+i*.132,.025,.11,.055,.12,mat('#dcb66b',.55,.4));
    orb(g,s*.441,.30+i*.132,.076,.026,.026,.011,'#efca80');
  }
  soft(g,.06,.60,.087,.67,.54,.055,.041,mat('#c2c7b8',.46,.42));
  const eyes=face(g,.113,.65,.147);
  soft(g,-.13,1.068,.1,.45,.39,.095,.044,'#253941');
  const ring=cyl(g,-.13,1.07,.181,.14,.14,.075,mat('#acb8b5',.6,.3));ring.rotation.x=Math.PI/2;
  const lens=orb(g,-.13,1.07,.236,.09,.09,.043,mat('#21374c',.5,.2));
  orb(g,-.157,1.10,.266,.019,.019,.012,'#b4e6e0');
  for(let j=0;j<4;j++)box(g,.185+j*.051,1.165-(j%2)*.05,.084,.028,.19,.018,'#e9b965');
  box(g,.266,1.255,.084,.188,.02,.018,'#e9b965');
  for(let i=0;i<4;i++)box(g,-.22+i*.145,.242,.088,.087,.032,.023,'#a5b7a0');
  return {g,eyes,lens};
}
export function laptop(parent){
  const g=group(parent);
  soft(g,0,.126,.18,1.90,.12,1.02,.052,'#b6b9ac');
  for(let i=0;i<5;i++)for(let j=0;j<10;j++)box(g,-.73+j*.162,.203,-.13+i*.073,.121,.011,.043,'#687976');
  box(g,0,.198,.54,.53,.007,.19,'#99a7a2');
  const screen=group(g,0,.21,-.27);screen.rotation.x=-.10;
  soft(screen,0,.57,0,1.82,1.11,.068,.071,'#344950');soft(screen,0,.57,.047,1.67,.98,.014,.028,'#e7e7ce');
  box(screen,0,.932,.069,1.49,.063,.014,'#ce7852');
  for(let i=0;i<7;i++){const h=[.15,.23,.20,.32,.28,.39,.37][i];box(screen,-.61+i*.181,.23+h/2,.067,.095,h,.007,i===6?'#c86843':'#4e8a86');}
  return g;
}
export function plant(parent,x,y,z,s=1){
  const g=group(parent,x,y,z);g.scale.setScalar(s);cyl(g,0,.17,0,.20,.147,.34,'#bf7656');cyl(g,0,.34,0,.207,.203,.065,'#dc9b76');
  for(let i=0;i<7;i++){const a=i*2.40,r=.14,e=orb(g,Math.cos(a)*r,.54+(i%3)*.065,Math.sin(a)*r,.079,.252,.07,i%2?'#548781':'#87a594');e.rotation.z=-Math.cos(a)*.65;e.rotation.x=Math.sin(a)*.65;}
  return g;
}
