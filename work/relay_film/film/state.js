export const timeline=await fetch('./timeline.json').then(r=>r.json());
export const duration=timeline[timeline.length-1].end;
export function at(t){
 const i=timeline.findIndex(s=>t<s.end),index=i<0?timeline.length-1:i,shot=timeline[index];
 const progress=Math.max(0,Math.min(1,(t-shot.start)/(shot.end-shot.start)));
 const cue=shot.cues.find(c=>t>=c.start-.06&&t<=c.start+c.duration+.27);
 return {shot,index,progress,cue};
}
