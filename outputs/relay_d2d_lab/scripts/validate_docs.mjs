import {chromium} from 'playwright';
import fs from 'node:fs';
const out='results/validation_v2';
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const page=await browser.newPage();const errors=[],checks=[],links=new Set();
page.on('pageerror',e=>errors.push(e.message));
try {
  const manual=await page.request.get('http://127.0.0.1:8765/guide');
  if (!manual.ok() || !manual.headers()['content-type'].includes('application/pdf')) throw new Error('Guide PDF unavailable');
  for(const route of ['/research','/docs/PROTOCOL.html','/docs/VALIDATION.html']){
    for(const width of [390,1440]){
      await page.setViewportSize({width,height:960});
      await page.goto('http://127.0.0.1:8765'+route,{waitUntil:'networkidle'});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      checks.push({route,width,overflow});if(overflow)throw new Error(`${route} overflow ${width}`);
      const targets=await page.locator('a[href],img[src]').evaluateAll(nodes=>nodes.map(n=>n.href||n.src));
      targets.filter(t=>t.startsWith('http://127.0.0.1:8765/')).forEach(t=>links.add(t));
      if(route==='/docs/VALIDATION.html'||(route==='/research'&&width===390))
        await page.screenshot({path:`${out}/${route.includes('VALIDATION')?'validation':'research'}_${width}.png`});
    }
  }
  const statuses=[];
  for(const url of links){const response=await page.request.get(url);statuses.push({url,status:response.status()});if(!response.ok())throw new Error(`Broken local link ${url}`);}
  if(errors.length)throw new Error(errors.join('\n'));
  fs.writeFileSync(out+'/docs_ui.json',JSON.stringify({checks,statuses,errors,tested_at:new Date().toISOString()},null,2));
  console.log(JSON.stringify({views:checks.length,local_links:statuses.length,errors}));
} finally {await browser.close();}
