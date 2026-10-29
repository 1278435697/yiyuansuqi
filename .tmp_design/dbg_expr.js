const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const src = require('fs').readFileSync('repro_pattern.js', 'utf8');
const ms = [...src.matchAll(/ev\(`([\s\S]*?)`\)/g)].map(x => x[1]);
(async () => {
  const port = 9552;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysdbg','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Page.navigate',{url:'about:blank'}); await sleep(1500);
  for (let k=0;k<ms.length;k++){
    const r = await send('Runtime.evaluate',{expression:ms[k],returnByValue:true});
    const ed = r.result.exceptionDetails;
    if (!ed) { console.log(k+' OK -> '+String(r.result.result.value).slice(0,80)); continue; }
    console.log(k+' BAD line='+ed.lineNumber+' col='+ed.columnNumber);
    const lines = ms[k].split('\n');
    console.log('   报错行: '+JSON.stringify(lines[ed.lineNumber]||'(越界)'));
    const L = lines[ed.lineNumber]||'';
    console.log('   col附近: '+JSON.stringify(L.slice(Math.max(0,ed.columnNumber-15), ed.columnNumber+15)));
  }
  ws.close(); child.kill();
})();
