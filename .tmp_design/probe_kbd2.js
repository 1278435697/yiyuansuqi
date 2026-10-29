const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = 9451;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysk2','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Page.navigate',{url:'http://localhost:5173/tryon'}); await sleep(9000);
  const EXPR = `(function(){
    var fi=document.querySelector('input[type=file]');
    var out=[];
    if(!fi){out.push('NO_FILE_INPUT');}
    else{var cs=getComputedStyle(fi);
      out.push('FI display='+cs.display+' vis='+cs.visibility+' op='+cs.opacity+' pos='+cs.position+' w='+Math.round(fi.getBoundingClientRect().width)+' tabindex='+fi.getAttribute('tabindex'));
      out.push('  focusable='+(!!(fi.offsetWidth||fi.offsetHeight||fi.getClientRects().length)));
    }
    var dz=document.querySelector('.upload-zone,.drop-zone,[class*=upload]');
    if(dz){out.push('DZ '+dz.tagName+'.'+String(dz.className).slice(0,40)+' tabindex='+dz.getAttribute('tabindex')+' role='+dz.getAttribute('role')+' aria='+dz.getAttribute('aria-label'));
      out.push('  keydown='+(!!dz.onkeydown)+' click='+(!!dz.onclick));}
    return out.join(' | ');})()`;
  const r = await send('Runtime.evaluate', { expression: EXPR, returnByValue: true });
  console.log(JSON.stringify(r).slice(0, 1200));
  ws.close(); child.kill();
})();
