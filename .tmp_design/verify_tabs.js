const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = 9520;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ystv','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  await send('Runtime.enable',{}); await send('Page.enable',{});
  const EXPR = `(function(){var o=[];
    document.querySelectorAll('.app-main .tabs a').forEach(function(a){var r=a.getBoundingClientRect();var c=getComputedStyle(a);
      o.push((a.textContent||'').trim()+' '+Math.round(r.width)+'x'+Math.round(r.height)+' '+c.display+'/'+c.alignItems);});
    o.push('docScrollW='+document.documentElement.scrollWidth+' client='+document.documentElement.clientWidth);
    var nav=document.querySelector('.app-main .tabs'); if(nav) o.push('tabs行高='+Math.round(nav.getBoundingClientRect().height)+' 换行='+(nav.getBoundingClientRect().height>60?'是':'否'));
    return o.join(' | ');})()`;
  for (const [vk,W,H] of [['m',390,844],['d',1440,900]]) {
    await send('Emulation.setDeviceMetricsOverride',{width:W,height:H,deviceScaleFactor:1,mobile:W<800});
    await send('Page.navigate',{url:'http://localhost:5173/tryon'}); await sleep(9000);
    const r = await send('Runtime.evaluate',{expression:EXPR,returnByValue:true});
    console.log(vk+' '+(r.result.result?r.result.result.value:JSON.stringify(r.result.exceptionDetails).slice(0,150)));
  }
  ws.close(); child.kill();
})();
