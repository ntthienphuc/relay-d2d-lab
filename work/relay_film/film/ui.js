import * as T from '/vendor/three.module.js';
import {timeline} from './state.js';
const $=id=>document.getElementById(id);const labels=[['A','Nguồn'],['B','RelayBox'],['C','Đích']];
const tags=labels.map(([key,name])=>{const n=document.createElement('div');n.className='tag';const chip=document.createElement('i');chip.textContent=key;n.append(chip,name);$('tags').append(n);return n;});
for(let i=0;i<timeline.length;i++)$('ticks').append(document.createElement('i'));
let previous=-1;
export function updateHUD(frame,t,cam){
 const {shot,index,progress,cue}=frame;
 if(previous!==index){
  previous=index;$('chapter').textContent=shot.chapter;$('lead').textContent=shot.lead.replace('Wi-Fi','Wi‑Fi');$('detail').textContent=shot.detail;
  $('numbers').style.display=shot.id==='bench'?'flex':'none';$('footword').textContent=shot.id==='bench'?'Đo trên bàn · 409270498 / 409351681':shot.id==='end'?'Relay Lab · Mạng truyền thông cộng tác':'Mô hình ba tầng';
  [...$('ticks').children].forEach((n,i)=>n.className=i<=index?'on':'');
 }
 $('sub').textContent=cue?.text||'';
 const anchors=[[-.32,1.52,1.10],[.58,3.82,1.15],[1.37,6.16,1.04]];
 for(let i=0;i<3;i++){
  const p=new T.Vector3(...anchors[i]).project(cam);const n=tags[i];
  let show=!['bench','af','df'].includes(shot.id)&&(!['house','relay','join'].includes(shot.id)|| (shot.id==='house'?i!==1:shot.id==='relay'?i===1:i===2));
  n.style.display=show&&p.x>-.32&&p.x<.82&&p.y>-.63&&p.y<.78?'block':'none';n.style.left=((p.x+1)*50)+'%';n.style.top=((1-p.y)*50)+'%';
 }
 const theory=shot.id==='af'||shot.id==='df';
 $('oscLabels').style.display=theory?'block':'none';
 if(theory){
  const points=[[-20.02,2.40,.14],[-15.98,2.40,.14]];
  points.forEach((xyz,i)=>{const pos=new T.Vector3(...xyz).project(cam),label=$('oscLabels').children[i];label.style.left=((pos.x+1)*50)+'%';label.style.top=((1-pos.y)*50)+'%';});
  $('scopeOut').textContent=shot.id==='df'&&progress>=.58?'B dừng phát':'Sóng B phát';
 }
 const signal=$('theoryState');signal.textContent=shot.id==='slots'?(((t*.27)%1)<.5?'Khe 1   ·   A → B':'Khe 2   ·   B → C'):shot.id==='af'?(progress<.64?'FG  ·  giữ hệ số G':'VG  ·  điều chỉnh G'):shot.id==='df'?(progress<.58?'Giải mã thành công':'Không giải mã được'):'';
 if(['af','df','slots'].includes(shot.id))$('footword').textContent='Mô hình kênh · Tín hiệu minh họa';
 const head=t-shot.start,tail=shot.end-t;
 const edge=Math.max(0,1-head/(index===0?.55:.23),1-tail/(index===timeline.length-1?.75:.23));$('fade').style.opacity=(Math.min(1,edge)*.97).toFixed(3);
}
