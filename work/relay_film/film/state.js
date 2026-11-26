export const timeline = await fetch('./timeline.json').then(response => response.json());
export const duration = timeline[timeline.length - 1].end;

export function at(time) {
  const found = timeline.findIndex(shot => time < shot.end);
  const index = found < 0 ? timeline.length - 1 : found;
  const shot = timeline[index];
  const progress = Math.max(0, Math.min(1, (time - shot.start) / (shot.end - shot.start)));
  const cue = shot.cues.find(item => time >= item.start && time < item.start + item.duration + .18);
  const caption = cue?.captions?.filter(part => part.start <= time).at(-1)?.text || cue?.text || '';
  const phaseChanged = shot.id === 'df' && time >= shot.cues[1].start;
  let slot = null;
  if (shot.id === 'slots') {
    const listen = shot.cues[1].start;
    const forward = shot.cues[2].start;
    const explain = shot.cues[3].start;
    if (time >= listen && time < forward) {
      slot = {first:true, fraction:(time-listen)/(forward-listen)};
    } else if (time >= forward && time < explain) {
      slot = {first:false, fraction:(time-forward)/(explain-forward)};
    } else if (time >= explain) {
      const repeat = (time-explain)/(shot.end-explain);
      slot = {first:repeat<.5, fraction:(repeat*2)%1};
    }
  }
  const turn = shot.cues[1].start;
  const reverse = time >= turn;
  const webProgress = reverse ? (time-turn)/(shot.end-turn) : (time-shot.start)/(turn-shot.start);
  return {shot,index,progress,caption,phaseChanged,slot,reverse,webProgress};
}
