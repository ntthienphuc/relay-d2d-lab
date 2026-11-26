import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const folder=process.argv[2];
if(!folder)throw Error('Pass the evidence folder');
const base='http://127.0.0.1:8765';
const endpoint=async suffix=>(await fetch(base+'/api/'+suffix)).json();
const initial=await endpoint('status');
if(initial.run&&!initial.run.finished)throw Error('Stop after current measurement');
const board=initial.devices.find(n=>n.platform==='esp32'&&n.online);
const sink=initial.devices.find(n=>n.role==='sink'&&n.bridge_id===board?.id&&n.online);
const source=initial.devices.find(n=>n.role==='source'&&n.online);
if(!board||!sink||!source)throw Error('Expected physical source, relay, SoftAP sink');
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const runs=[];
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
  await page.goto(base);
  await page.waitForFunction(()=>window.relayLab?.state?.simulation);
  await page.click('[data-mode="live"]');
  await page.selectOption('#sourceDevice',source.id);
  await page.selectOption('#relayDevice',board.id);
  await page.selectOption('#destinationDevice',sink.id);
  await page.selectOption('#environment','live');await page.selectOption('#route','relay');
  await page.fill('#pps','10');await page.selectOption('#payload','128');
  for(const kind of ['crc','pause']){
    const label='UI '+kind+' '+Date.now();
    await page.fill('#experimentLabel',label);
    const options=page.locator('details').filter({has:page.locator('#corruptEvery')});
    if(await options.getAttribute('open')===null)await options.locator('summary').click();
    await page.fill('#corruptEvery',kind==='crc'?'5':'0');
    await page.fill('#duration',kind==='crc'?'10':'14');
    await page.click('#startRun');
    await page.waitForFunction(l=>window.relayLab.state.status?.run?.config?.experiment_label===l,label);
    if(kind==='pause'){
      await page.waitForFunction(()=>window.relayLab.state.status.run.acked>=4);
      await page.click('#pauseRelay');
      await page.waitForFunction(()=>window.relayLab.state.status.run.dropped_by_relay>=4);
      await page.click('#pauseRelay');
    }
    await page.waitForFunction(()=>window.relayLab.state.status.run.finished,null,{timeout:40000});
    const id=(await endpoint('status')).run.id;
    const {summary,events}=await endpoint('replay/'+id);
    const byType=type=>new Set(events.filter(e=>e.type===type).map(e=>e.seq));
    const failed=byType(kind==='crc'?'invalid':'drop_paused');
    const sent=byType('send'),forward=byType('forward'),received=byType('receive');
    if(!summary.complete_send||summary.stop_reason||!failed.size||!received.size)throw Error('Control not observed');
    for(const seq of failed){
      if(!sent.has(seq)||forward.has(seq)||received.has(seq))throw Error('Rejected packet passed control');
      if(kind==='crc'&&(seq+1)%5!==0)throw Error('Unexpected invalid sequence');
    }
    if(kind==='pause'&&![...received].some(seq=>seq>Math.max(...failed)))throw Error('No recovery after resume');
    runs.push({kind,id,sent:sent.size,invalid_or_paused:failed.size,forward:forward.size,received:received.size,acked:summary.acked});
    fs.writeFileSync(path.join(folder,'controls.json'),JSON.stringify({runs,errors},null,2));
  }
  if(errors.length)throw Error(errors.join('\n'));
  console.log(JSON.stringify(runs));
}finally{await browser.close();}
