const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  let port = Number(process.env.PORT || 9500);
  for (const [side, base] of [['before', 'http://47.93.14.11'], ['after', 'http://localhost:5173']]) {
    const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/yscd'+port,'about:blank'], { stdio:'ignore' });
    let ws;
    for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
    port++;
    let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
    const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
    await send('Runtime.enable',{}); await send('Page.enable',{});
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:2,mobile:true});
    await send('Page.navigate',{url:base+'/tryon/history'}); await sleep(9500);
    const r = await send('Runtime.evaluate', { expression:
      `(function(){var a=document.querySelector('.app-main article,.record,.el-card');if(!a)return 'none';
        a.scrollIntoView({block:'start'});var r=a.getBoundingClientRect();
        return JSON.stringify({x:Math.max(0,Math.round(r.left+window.scrollX)-4),y:Math.max(0,Math.round(r.top+window.scrollY)-4),w:Math.round(r.width)+8,h:Math.round(r.height)+8});})()`, returnByValue: true });
    const clip = JSON.parse(r.result.result.value);
    if (clip.x === undefined) { console.log(side + ' 没找到卡片'); ws.close(); child.kill(); continue; }
    await sleep(700);
    const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 82, clip: { x: clip.x, y: clip.y, width: clip.w, height: clip.h, scale: 1 }, captureBeyondViewport: true });
    if (!s.result) { console.log('SHOT ERR ' + JSON.stringify(s.error).slice(0,200)); ws.close(); child.kill(); continue; }
    require('fs').writeFileSync('audit/tryon/card-' + side + '.jpg', Buffer.from(s.result.data, 'base64'));
    console.log(side + ' card ' + JSON.stringify(clip));
    ws.close(); child.kill(); await sleep(500);
  }
})();
