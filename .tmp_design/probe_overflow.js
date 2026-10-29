const { spawn } = require('child_process');
const os = require('os'); const sleep = ms => new Promise(r => setTimeout(r, ms));
const URL_ = process.argv[2], PORT = Number(process.argv[3] || 9593);
const EXPR = `(()=>{
  const W=window.innerWidth, bad=[];
  for (const el of document.querySelectorAll('*')) {
    const r=el.getBoundingClientRect();
    if (r.width<1) continue;
    if (r.right>W+2 && r.left>0) {
      const cs=getComputedStyle(el);
      if (cs.position==='fixed') continue;
      bad.push({标签:el.tagName.toLowerCase(), cls:(el.className&&String(el.className).slice(0,40))||'', 左:Math.round(r.left), 右:Math.round(r.right), 宽:Math.round(r.width)});
    }
  }
  bad.sort((a,b)=>b.右-a.右);
  return JSON.stringify({视口:W, 溢出元素:bad.slice(0,10)});
})()`;
(async () => {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${PORT}`,
     '--user-data-dir='+os.tmpdir()+'/ysovf'+PORT,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const j=await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const t=j.find(x=>x.type==='page'); if(t){ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise((r,rj)=>{ws.onopen=r;ws.onerror=rj}); break;} }catch(e){ await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id]}};
  const send=(m,x)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method:m,params:x}))});
  const ev=async x=>{const r=await send('Runtime.evaluate',{expression:x,returnByValue:true,awaitPromise:true}); if(r.result.exceptionDetails) return 'EXC '+JSON.stringify(r.result.exceptionDetails).slice(0,200); return r.result.result.value};
  await send('Page.enable',{}); await send('Runtime.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:URL_});
  await sleep(4500);
  console.log(await ev(EXPR));
  console.log('滚动后', await ev(`(()=>{window.scrollTo(0,1200);return 1})()`), await sleep(800), await ev(EXPR));
  ws.close(); child.kill();
})();
