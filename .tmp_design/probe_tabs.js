const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9430);
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysp'+port,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  for (const [side,base] of [['before','http://47.93.14.11'],['after','http://localhost:5173']]) {
    await send('Page.navigate',{url:base+'/tryon'}); await sleep(9000);
    const expr = `(function(){var out=[];
      document.querySelectorAll('.app-nav a,.tabs a,.el-radio-button,.el-radio-button__original-radio,.el-segmented__item,button,.el-button').forEach(function(n){
        var r=n.getBoundingClientRect(); if(!r.width) return;
        var cs=getComputedStyle(n);
        out.push({sel:n.tagName+'.'+(n.className||'').toString().split(' ').slice(0,2).join('.'),
          txt:(n.textContent||'').trim().slice(0,8),w:Math.round(r.width),h:Math.round(r.height),
          vis:cs.visibility+' op'+cs.opacity+' pos'+cs.position});
      });
      return JSON.stringify(out);})()`;
    const res=await send('Runtime.evaluate',{expression:expr,returnByValue:true});
    const list=JSON.parse(res.result.result.value);
    console.log('\n### '+side+' 390px  (共'+list.length+'个候选)');
    list.filter(x=>x.h<44||x.w<44).slice(0,18).forEach(x=>console.log('  '+x.sel.padEnd(34)+' '+String(x.w+'x'+x.h).padEnd(9)+' "'+x.txt+'" '+x.vis));
  }
  ws.close(); child.kill();
})();
