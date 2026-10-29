const { spawn } = require('child_process'); const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const [URL_, PORT] = [process.argv[2], Number(process.argv[3])];
(async () => {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${PORT}`,
     '--user-data-dir='+os.tmpdir()+'/ysrm'+PORT,'--hide-scrollbars','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const j=await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
    const t=j.find(x=>x.type==='page'); if(t){ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise((r,rj)=>{ws.onopen=r;ws.onerror=rj}); break;}}catch(e){await sleep(250)} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id]}};
  const send=(mm,pp)=>new Promise(res=>{const i=++id;p[i]=res;ws.send(JSON.stringify({id:i,method:mm,params:pp}))});
  const ev=async x=>(await send('Runtime.evaluate',{expression:x,returnByValue:true,awaitPromise:true})).result.result.value;
  await send('Page.enable',{}); await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await send('Page.navigate',{url:URL_}); await sleep(5000);
  console.log(URL_, JSON.stringify(await ev(`(()=>{
    const c=document.querySelector('.acc-card');
    const cs=c?getComputedStyle(c):null;
    return { 减少动效生效: matchMedia('(prefers-reduced-motion: reduce)').matches,
      卡片动画: cs? (cs.animationName+' '+cs.animationDuration) : '无卡片',
      卡片过渡: cs? cs.transitionDuration : '无卡片' };
  })()`)));
  ws.close(); child.kill();
})();
