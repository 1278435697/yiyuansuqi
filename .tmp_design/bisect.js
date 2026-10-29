const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const src = require('fs').readFileSync('probe_cta.js', 'utf8');
const m = src.match(/const ex = `([\s\S]*?)`;/)[1];
(async () => {
  const port = 9488;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysbi','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Page.navigate',{url:'http://localhost:5173/tryon'}); await sleep(8000);
  const lines = m.split('\n');
  for (let k = 1; k <= lines.length; k++) {
    const body = lines.slice(0, k).join('\n');
    const probe = '(function(){var o=[];' + lines.slice(1, k).join('\n') + '\nreturn 1;})()';
    const r = await send('Runtime.evaluate', { expression: probe, returnByValue: true });
    const ok = !r.result.exceptionDetails;
    console.log(k + ' ' + (ok ? 'OK  ' : 'BAD ') + lines[k-1].trim().slice(0, 60) + (ok ? '' : ' << ' + JSON.stringify(r.result.exceptionDetails).slice(0, 160)));
    if (!ok) break;
  }
  ws.close(); child.kill();
})();
