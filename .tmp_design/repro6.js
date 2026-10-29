const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9612);
  const base = process.argv[2] || 'http://47.93.14.11';
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysr6'+port,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  const ev=async e=>{const r=await send('Runtime.evaluate',{expression:e,returnByValue:true});
    const ed=r.result.exceptionDetails; if(ed)return 'ERR '+(ed.exception&&ed.exception.description?ed.exception.description.split('\n')[0]:ed.text);
    return r.result.result.value;};
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:base+'/pattern/32'}); await sleep(11000);
  console.log('### '+base);
  console.log('  A. .img-col 上是否挂了 Vue 监听: ' + await ev(`(function(){var c=document.querySelector('.img-col');
    var vei=c._vei||c.__vueParentComponent; var keys=c._vei?Object.keys(c._vei):[];
    return 'el._vei keys='+JSON.stringify(keys)+' | 有onclick属性='+(typeof c.onclick)+' | getEventListeners不可用';})()`));
  console.log('  B. 冒泡路径探针: ' + await ev(`(function(){window.__path=[];
    ['.img-col','.img-row','.detail-main','.pattern-page','.app-main'].forEach(function(s){var n=document.querySelector(s);
      if(n)n.addEventListener('click',function(){window.__path.push(s)},false);});
    document.addEventListener('click',function(){window.__path.push('document')},false);
    var im=document.querySelector('.img-col img');
    im.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
    return '从 IMG 派发 bubbles:true 走到的层: '+window.__path.join(' > ');})()`));
  await sleep(1500);
  console.log('  C. 灯箱: ' + await ev(`!!document.querySelector('.el-image-viewer__wrapper')`));
  console.log('  D. detail 数据里 images 长度: ' + await ev(`(function(){var b=document.querySelector('.count-badge');return b?b.textContent:'无徽标'})()`));
  ws.close(); child.kill();
})();
