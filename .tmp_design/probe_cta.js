const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  let port = Number(process.env.PORT || 9470);
  for (const [side, base] of [['before', 'http://47.93.14.11'], ['after', 'http://localhost:5173']]) {
    const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/yscta'+port,'about:blank'], { stdio:'ignore' });
    let ws;
    for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
    port++;
    let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id];}};
    const send=(m2,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method:m2,params}));});
    await send('Runtime.enable',{}); await send('Page.enable',{});
    await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
    await send('Page.navigate',{url:base+'/tryon'}); await sleep(9500);
    const ex = `(function(){var o=[];
      document.querySelectorAll('.app-main button').forEach(function(b){var t=(b.textContent||'').trim();
        if(/试穿|生成|开始/.test(t)&&t.length<16) o.push('CTA "'+t+'" disabled='+b.disabled+' aria-disabled='+b.getAttribute('aria-disabled')+' cls='+String(b.className).slice(0,46));});
      var e=document.querySelector('.el-empty, .yisu-empty, .el-empty__description');
      if(e){var cs=getComputedStyle(e.querySelector('.el-empty__description')||e);
        o.push('空态 '+e.className.toString().slice(0,30)+' color='+cs.color+' fontSize='+cs.fontSize+' bg='+getComputedStyle(e).backgroundColor);}
      var seal=document.querySelector('.el-empty::before');
      var em=document.querySelector('.el-empty');
      if(em){var cb=getComputedStyle(em,'::before');o.push('印章 content='+cb.content+' color='+cb.color+' border='+cb.borderStyle+' '+cb.borderColor+' size='+cb.width);}
      return o.join('\n  ');})()`;
    const r = await send('Runtime.evaluate',{expression:ex,returnByValue:true});
    console.log('\n##### '+side+'\n  '+(r.result.result.value||JSON.stringify(r.result.exceptionDetails).slice(0,200)));
    ws.close(); child.kill(); await sleep(500);
  }
})();
