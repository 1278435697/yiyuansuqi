const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = 9560;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysdbg2','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  const ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  console.log('browser: ' + ver['Browser']);
  await send('Runtime.enable',{}); await sleep(500);
  const tests = [
    ["simple", "(function(){return 'ok';})()"],
    ["chinese", "(function(){var o=[];o.push('高度=1');return o.join('|');})()"],
    ["querysel", "(function(){var o=[];o.push('h='+Math.round(document.querySelector('body').getBoundingClientRect().height));return o.join('|');})()"],
    ["dotcls+chinese", "(function(){var o=[];o.push('.app-main 高度='+1);return o.join('|');})()"],
    ["startdot", "(function(){var o=[];o.push('X .a-b 高度='+Math.round(5));return o.join('|');})()"],
  ];
  for (const [n, e] of tests) {
    const r = await send('Runtime.evaluate', { expression: e, returnByValue: true });
    const ed = r.result.exceptionDetails;
    console.log(n.padEnd(16) + (ed ? 'BAD ' + JSON.stringify(ed).slice(0, 130) : 'OK ' + r.result.result.value));
  }
  ws.close(); child.kill();
})();
