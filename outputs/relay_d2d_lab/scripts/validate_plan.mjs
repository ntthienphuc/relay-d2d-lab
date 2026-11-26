import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dir=path.join(root,'docs/planning');
const target=path.join(dir,'PLAN_HOTSPOT_2026-11-26.html');
const plan=JSON.parse(fs.readFileSync(path.join(dir,'plan.json'),'utf8'));
if(plan.requirements.length!==12||plan.tasks.length!==22||plan.report_outline.reduce((s,x)=>s+x.pages,0)!==38)throw new Error('Plan scope mismatch');
const known=new Map(plan.tasks.map(t=>[t.id,t]));
function visit(id,stack=new Set()){
  if(stack.has(id))throw new Error('Cyclic task dependency: '+id);
  if(!known.has(id))throw new Error('Missing task '+id);
  const next=new Set(stack);next.add(id);known.get(id).depends.forEach(d=>visit(d,next));
}
known.forEach((v,k)=>visit(k));
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const page=await browser.newPage();const errors=[],views=[];
page.on('pageerror',e=>errors.push(e.message));
try{
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:1000});
    await page.goto(pathToFileURL(target).href,{waitUntil:'load'});
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
    if(overflow)throw new Error('Document overflow '+width);
    await page.screenshot({path:path.join(dir,`preview_${width}.png`)});
    views.push({width,overflow,sections:await page.locator('main>section').count()});
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#topology').screenshot({path:path.join(dir,'topology_preview.png')});
  const anchors=await page.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.href));
  let local=0;
  for(const href of anchors){
    const u=new URL(href);
    if(u.protocol!=='file:')continue;
    if(!fs.existsSync(fileURLToPath(u)))throw new Error('Missing local target '+href);
    if(fileURLToPath(u)===target&&u.hash&&!await page.locator(u.hash).count())throw new Error('Missing anchor '+href);
    local++;
  }
  const imageErrors=await page.locator('img').evaluateAll(nodes=>nodes.filter(n=>!n.complete||!n.naturalWidth).map(n=>n.src));
  if(errors.length||imageErrors.length)throw new Error(JSON.stringify({errors,imageErrors}));
  fs.writeFileSync(path.join(dir,'validation.json'),JSON.stringify({requirements:12,tasks:22,acyclic_dependencies:true,views,local_links:local,errors,imageErrors,tested_at:new Date().toISOString()},null,2));
  console.log(JSON.stringify({requirements:12,tasks:22,views,local_links:local,errors}));
}finally{await browser.close();}
