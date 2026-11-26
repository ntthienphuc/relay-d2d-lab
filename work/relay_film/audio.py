import sys,wave,json,math
from pathlib import Path
here=Path(__file__).absolute().parent;sys.path.insert(0,str(here/'film-tools'))
import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig
model=here/'film-voice/vi_VN-vais1000-medium.onnx'
voice=PiperVoice.load(model)
rate=22050
def render(text):
    text=text.replace('AF','a ép').replace('DF','đê ép').replace('Wi-Fi','oai phai').replace('A ', 'A ').replace('B ', 'bê ').replace(' C',' xê').replace(' A',' a').replace(' B',' bê').replace('Samsung','Sam sung').replace('RelayBox','rì lây bóc').replace('router','bộ phát').replace('laptop','máy tính')
    chunks=[chunk.audio_float_array for chunk in voice.synthesize(text,SynthesisConfig(length_scale=1.04,noise_scale=.5,noise_w_scale=.333))]
    a=np.concatenate(chunks)
    nz=np.flatnonzero(np.abs(a)>.008)
    if len(nz):a=a[max(0,nz[0]-520):nz[-1]+1700]
    a=a/np.maximum(.38,np.max(np.abs(a)))*.77
    return a.astype('float32')
story=json.loads((here/'film/story.json').read_text('utf8'));clock=.0;sounds=[]
for sc in story:
    sc['start']=round(clock,3);clock+=.65;sc['cues']=[]
    for sentence in sc['lines']:
        spoken=render(sentence);sc['cues'].append({'start':round(clock,3),'duration':round(len(spoken)/rate,3),'text':sentence})
        sounds.append((clock,spoken));clock+=len(spoken)/rate+.34
    clock+=.48;sc['end']=round(clock,3)
clock+=.9;story[-1]['end']=round(clock,3)
N=round(clock*rate);audio=np.zeros(N,dtype=np.float32)
for start,signal in sounds:
    i=round(start*rate);audio[i:i+len(signal)]+=signal
def note(at,freq,duration,gain):
    i=round(at*rate);n=min(round(duration*rate),N-i)
    if n<=0:return
    t=np.arange(n)/rate
    bell=(np.sin(2*np.pi*freq*t)+.22*np.sin(2*np.pi*freq*2*t)+.055*np.sin(2*np.pi*freq*3.01*t))
    envelope=(1-np.exp(-22*t))*np.exp(-3*t/duration)*np.minimum(1,np.maximum(0,(duration-t)*12))
    audio[i:i+n]+=gain*envelope*bell
# Original sparse marimba pattern, ducked under speech.
for k,at in enumerate(np.arange(.12,clock,1.28)):
    chords=((55,62,67,71),(52,59,64,67),(48,55,60,64),(50,57,62,66))
    chord=chords[(k//4)%4];pitch=chord[k%4];note(at,440*2**((pitch-69)/12),1.03,.024 if k%4 else .035)
for sc in story:
    note(sc['start']+.04,659.25,.44,.042);note(sc['start']+.21,783.99,.56,.029)
audio[-rate:]*=np.linspace(1,0,rate)
with wave.open(str(here/'film-narration.wav'),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
(here/'film/timeline.json').write_text(json.dumps(story,ensure_ascii=False,indent=2),'utf8')
print('Runtime',clock,'seconds',[(s['id'],round(s['end']-s['start'],1)) for s in story])
