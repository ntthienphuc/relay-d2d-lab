import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const out=process.argv[2];
if(!out)throw Error('Pass the evidence directory');
fs.mkdirSync(out,{recursive:true});
const base='http://127.0.0.1:8765';
const status=await (await fetch(base+'/api/status')).json();
const board=status.devices.find(d=>d.platform==='esp32'&&d.online);
if(!board)throw Error('Register a physical RelayBox first');
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:960}});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
  await page.goto(base);
  await page.waitForFunction(()=>window.relayLab?.state?.simulation);
  await page.click('[data-mode="live"]');
  await page.waitForFunction(()=>document.querySelector('#deviceList a'));
  const dashboard=await page.locator('#deviceList').innerText();
  await page.screenshot({path:path.join(out,'dashboard.png'),fullPage:true});
  await page.goto('http://'+board.local_ip+'/');
  await page.waitForFunction(()=>document.querySelector('#counts dd')?.textContent!=='—' && document.querySelectorAll('#counts dd').length===6);
  const portal=await page.locator('#link').innerText();
  await page.setViewportSize({width:390,height:844});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Portal overflows');
  await page.screenshot({path:path.join(out,'portal.png'),fullPage:true});
  await page.goto(base+'/results/'+path.basename(out)+'/REPORT.html');
  await page.getByRole('heading',{name:'Hai Android và một ESP32-CAM'}).waitFor();
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1||!document.querySelector('img')?.naturalWidth))throw Error('Report overflow or missing graph');
  const raw=await page.locator('td a').evaluateAll(links=>links.map(anchor=>anchor.href));
  for (const url of raw) {
    const response=await page.request.get(url);
    if(!response.ok()||!JSON.parse((await response.text()).split('\n')[0]).event_id)throw Error('Missing raw events at '+url);
  }
  const links=raw.length;
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync(path.join(out,'ui_checks.json'),JSON.stringify({dashboard,portal,raw_log_links:links,errors},null,2));
  console.log('Dashboard, physical portal, mobile report and '+links+' log links');
}finally{await browser.close();}
