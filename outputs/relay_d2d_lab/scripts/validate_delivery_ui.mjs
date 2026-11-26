import {chromium} from 'playwright';
import fs from 'node:fs';
const out='results/validation_v2';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8765',{waitUntil:'networkidle'});
await page.waitForFunction(()=>window.relayLab?.state?.simulation);
await page.click('[data-mode="live"]');
await page.waitForFunction(()=>document.querySelectorAll('#sourceDevice option').length>1);
const source=await page.locator('#sourceDevice option').nth(1).getAttribute('value');
await page.selectOption('#sourceDevice',source);await page.selectOption('#route','direct');
await page.fill('#duration','3');await page.fill('#experimentLabel','v2 browser Android source');
await page.click('#startRun');
await page.waitForFunction(()=>window.relayLab.state.status?.run?.config.experiment_label==='v2 browser Android source'&&window.relayLab.state.status.run.finished,{timeout:20000});
const run=await page.evaluate(()=>window.relayLab.state.status.run);
if(run.sent!==60||run.acked<=0)throw new Error('Android source could not be started by UI');
await page.screenshot({path:out+'/pc_android_source.png',fullPage:true});
const headings={};
for(const [route,name]of [['/guide','ready_guide'],['/research','paper_review']]){
  await page.goto('http://127.0.0.1:8765'+route,{waitUntil:'networkidle'});
  headings[name]=await page.locator('h1').textContent();
  await page.screenshot({path:out+'/'+name+'.png',fullPage:true});
  for(const width of [390,1440]){await page.setViewportSize({width,height:1000});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw new Error(name+' overflows at '+width);}
}
await browser.close();
fs.writeFileSync(out+'/delivery_ui.json',JSON.stringify({errors,headings,android_source_run:{id:run.id,sent:run.sent,confirmed:run.delivery_confirmed},tested_at:new Date().toISOString()},null,2));
console.log(JSON.stringify({errors,headings,run:run.id}));if(errors.length)process.exit(1);
