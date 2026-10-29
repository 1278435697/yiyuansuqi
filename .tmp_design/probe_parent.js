const { spawn } = require('child_process');
const os = require('os'); const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const PORT = 9595;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${PORT}`,
     '--user-data-dir='+os.tmpdir()+'/yspar'+PORT,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const j=await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const t=j.find(x=>x.type==='page'); if(t){ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise((r,rj)=>{ws.onopen=r;ws.onerror=rj}); break;} }catch(e){ await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id]}};
  const send=(m,x)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method:m,params:x}))});
  const ev=async x=>{const r=await send('Runtime.evaluate',{expression:x,returnByValue:true,awaitPromise:true}); if(r.result.exceptionDetails) return 'EXC '+JSON.stringify(r.result.exceptionDetails).slice(0,200); return r.result.result.value};
  await send('Page.enable',{}); await send('Runtime.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:'http://localhost:5278/pattern/32'});
  await sleep(4500);
  console.log(await ev(`(()=>{const el=[...document.querySelectorAll('img')].find(i=>i.getBoundingClientRect().right>window.innerWidth+2); if(!el) return 'none'; let n=el, out=[]; for(let k=0;k<4&&n;k++){ out.push(n.outerHTML ? n.outerHTML.slice(0,220).replace(/\s+/g,' ') : ''); n=n.parentElement; } return JSON.stringify(out,null,1)})()`));
  ws.close(); child.kill();
})();
