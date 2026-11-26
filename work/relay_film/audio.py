from pathlib import Path
import json,os,hashlib,re
import numpy as np
import soundfile as sf
from vieneu import Vieneu
r=Path(__file__).resolve().parent
scene=r/'film'
story=json.loads((scene/'story.json').read_text('utf8'))
engine=Vieneu(backend='onnx');voice=os.environ.get('RELAY_VOICE','Thiện Minh')
rate=48000;current=.22;pieces=[];clips=r/('speech-'+voice);clips.mkdir(exist_ok=True)
def subtitle_phrases(line, samples):
    phrases = re.split(r'(?<=[.!?])\s+', line)
    if len(phrases) == 1:
        return [(0.0, line)]
    step = int(.02 * rate)
    rms = np.sqrt(np.mean(samples[:len(samples)//step*step].reshape(-1,step)**2, axis=1))
    breaks = [0.0]
    words = [len(phrase.split()) for phrase in phrases]
    for i in range(1,len(phrases)):
        expected = len(rms) * sum(words[:i]) / sum(words)
        window = min(30, int(len(rms)*.18))
        left = max(int(breaks[-1]/.02)+10, int(expected)-window)
        right = min(len(rms)-10, int(expected)+window+1)
        candidates = np.arange(left, right)
        if not len(candidates):
            return [(0.0, line)]
        smooth = np.convolve(rms, np.ones(5)/5, mode='same')
        cost = smooth[candidates] + .008 * abs(candidates-expected)/max(1,window)
        breaks.append(round(candidates[np.argmin(cost)]*.02,3))
    return list(zip(breaks,phrases))

for idx,storyshot in enumerate(story):
    storyshot['start']=0 if idx==0 else round(current,3)
    current+=.24
    storyshot['cues']=[]
    for j,line in enumerate(storyshot['lines']):
        spoken=line.replace('RelayBox','rì lây bóc').replace('AF','a ép').replace('DF','đê ép').replace('“','').replace('”','')
        f=clips/f'{idx:02d}-{j}.wav'
        key=hashlib.sha256((voice+'|'+spoken).encode()).hexdigest()
        marker=f.with_suffix('.sha256')
        if not (f.exists() and marker.exists() and marker.read_text()==key):
            y=engine.infer(spoken,voice=voice,temperature=.72)
            sf.write(f,y,rate)
            marker.write_text(key)
        y,sr=sf.read(f,dtype='float32');assert sr==rate
        active=np.flatnonzero(np.abs(y)>.008);assert len(active)>0
        y=y[max(0,active[0]-int(.09*rate)):min(len(y),active[-1]+int(.15*rate))]
        n=int(.010*rate);y[:n]*=np.linspace(0,1,n);y[-n:]*=np.linspace(1,0,n)
        rms=np.sqrt(np.mean(y[np.abs(y)>.012]**2));y*=min(.165/max(.05,rms),.84/max(.1,max(abs(y))))
        captions=[dict(start=round(current+offset,3),text=words) for offset,words in subtitle_phrases(line,y)]
        storyshot['cues'].append(dict(start=round(current,3),duration=round(len(y)/rate,3),text=line,captions=captions))
        pieces.append((current,y));current+=len(y)/rate+(.28 if j<len(storyshot['lines'])-1 else .23)
        print(idx,j,round(len(y)/rate,2),flush=True)
    current+=.21;storyshot['end']=round(current,3)
current+=.49;story[-1]['end']=round(current,3)
track=np.zeros(round(current*rate),dtype='float32')
for t,y in pieces:
    i=round(t*rate);track[i:i+len(y)]+=y
def pluck(t,pitch,gain):
    i=round(t*rate);n=min(round(rate*1.18),len(track)-i)
    if n<=0:return
    tt=np.arange(n)/rate;f=440*2**((pitch-69)/12);env=(1-np.exp(-tt*30))*np.exp(-tt*3.6)*np.minimum(1,(1.18-tt)*9)
    track[i:i+n]+=gain*env*(np.sin(tt*2*np.pi*f)+.18*np.sin(tt*4*np.pi*f))
for k,t in enumerate(np.arange(.10,current,1.42)):
    chords=((55,62,67,71),(52,59,64,67),(48,55,60,64),(50,57,62,66));pluck(t,chords[(k//4)%4][k%4],.014)
track[-int(.3*rate):]*=np.linspace(1,0,int(.3*rate))
sf.write(r/'film-narration.wav',track,rate)
(scene/'timeline.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n','utf8')
print('Duration',current,flush=True)
