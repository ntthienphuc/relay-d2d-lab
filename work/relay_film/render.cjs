const fs=require('node:fs'),http=require('node:http'),path=require('node:path'),{spawn}=require('node:child_process'),{once}=require('node:events');
const {chromium}=require(process.env.RELAY_PLAYWRIGHT||'playwright');
const stage=path.join(__dirname,'film'), work=__dirname;
const vendor=process.env.RELAY_THREE_VENDOR||path.resolve(work,'../../outputs/relay_d2d_lab/web/vendor');
const web=http.createServer((req,res)=>{
 const uri=new URL(req.url,'http://localhost').pathname;
 let root=uri.startsWith('/vendor/')?vendor:stage;
 const file=path.resolve(root,(uri.startsWith('/vendor/')?uri.slice(8):uri.slice(1))||'index.html');
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);return res.end();}
 const ext=path.extname(file);res.writeHead(200,{'Content-Type':{'.js':'text/javascript; charset=utf-8','.html':'text/html; charset=utf-8','.json':'application/json; charset=utf-8','.css':'text/css; charset=utf-8'}[ext]||'application/octet-stream'});fs.createReadStream(file).pipe(res);
});
(async()=>{
 web.listen(0,'127.0.0.1');await once(web,'listening');const port=web.address().port;
 const browser=await chromium.launch({executablePath:process.env.RELAY_CHROME||'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-unsafe-swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:810},deviceScaleFactor:1});
 page.on('pageerror',console.error);page.setDefaultTimeout(45000);await page.goto('http://127.0.0.1:'+port+'/?capture');await page.waitForFunction(()=>window.film?.duration>0);
 const t=JSON.parse(fs.readFileSync(path.join(stage,'timeline.json'),'utf8'));
 for(const item of t){
 await page.evaluate(t=>window.film.render(t),item.start+(item.end-item.start)*.44);await page.screenshot({path:path.join(work,'film-'+item.id+'.jpg'),type:'jpeg',quality:88});
 }
 if(process.argv.includes('--preview'))return;
 const bin=process.env.RELAY_FFMPEG||'ffmpeg';
 const duration=await page.evaluate(()=>window.film.duration),fps=24,total=Math.ceil(duration*fps),target=path.join(work,'Hanh_trinh_cua_mot_goi_tin.mp4');
 const proc=spawn(bin,['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',String(fps),'-i','pipe:0','-i',path.join(work,'film-narration.wav'),'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-r',String(fps),'-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart','-metadata','title=Hành trình của một gói tin — RelayBox','-metadata','comment=Vietnamese synthetic narration: VieNeu-TTS v3 Turbo, preset voice Thien Minh. Original animation and music: Relay Lab.','-t',String(duration),target],{stdio:['pipe','ignore','inherit']});
 const closed=once(proc,'close');const start=Date.now();
 const cdp=await page.context().newCDPSession(page);
 for(let frame=0;frame<total;frame++){
  await page.evaluate(t=>window.film.render(t),frame/fps);
  const {data}=await cdp.send('Page.captureScreenshot',{format:'jpeg',quality:91,optimizeForSpeed:true,fromSurface:true});
  if(!proc.stdin.write(Buffer.from(data,'base64')))await once(proc.stdin,'drain');
  if(frame%120===0)console.log(frame+'/'+total, Math.round((Date.now()-start)/1000)+' s');
 }
 proc.stdin.end();const [code]=await closed;if(code!==0)throw Error('ffmpeg '+code);console.log(target);
 }finally{await browser.close();web.close();}
})().catch(e=>{console.error(e);web.close();process.exitCode=1;});
