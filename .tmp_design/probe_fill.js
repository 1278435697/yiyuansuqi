const { spawn } = require('child_process');
const os = require('os'); const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const PORT = 9584;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${PORT}`,
     '--user-data-dir='+os.tmpdir()+'/ysfill'+PORT,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const j=await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const t=j.find(x=>x.type==='page'); if(t){ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise((r,rj)=>{ws.onopen=r;ws.onerror=rj}); break;} }catch(e){ await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id]}};
  const send=(m,x)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method:m,params:x}))});
  const ev=async x=>{const r=await send('Runtime.evaluate',{expression:x,returnByValue:true,awaitPromise:true}); return r.result.result.value};
  await send('Page.enable',{}); await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:'http://localhost:5278/accessories/index.html#/a/'+encodeURIComponent('头饰-04')});
  await sleep(4200);
  console.log(await ev(`JSON.stringify([...document.querySelectorAll('img')].filter(i=>getComputedStyle(i).objectFit==='fill').map(i=>{const r=i.getBoundingClientRect();return {cls:i.className,父:i.parentElement.className,盒:Math.round(r.width)+'x'+Math.round(r.height),原:i.naturalWidth+'x'+i.naturalHeight,src:(i.currentSrc||i.src).split('/').pop().slice(0,30)}}))`));
  ws.close(); child.kill();
})();
