const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9625);
  const base = process.argv[2] || 'http://localhost:5173';
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ystc'+port,'about:blank'], { stdio:'ignore' });
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
  console.log(await ev(`(function(){window.__log=[];
    var im=document.querySelector('.img-col img');
    if(!im)return 'IMG 不存在';
    var n=im,i=0;
    while(n&&i<9){(function(el,tag){
      el.addEventListener('click',function(e){window.__log.push(tag+' BUBBLE stopP='+e.propagationStopped+' defaultP='+e.defaultPrevented)},false);
      el.addEventListener('click',function(e){window.__log.push(tag+' CAPTURE stopP='+e.propagationStopped)},true);
    })(n, (n.tagName?n.tagName:'window')+'.'+String(n.className||'').split(' ').slice(0,1).join('.'));
    n=n.parentElement||n.defaultView; i++;}
    return '已挂监听: '+window.__log.length+' (应为0)  层级数='+i;})()`));
  const b = JSON.parse(await ev(`(function(){var r=document.querySelector('.img-col img').getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`));
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:b.x,y:b.y});
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:b.x,y:b.y,button:'left',buttons:1,clickCount:1});
  await sleep(100);
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:b.x,y:b.y,button:'left',buttons:0,clickCount:1});
  await sleep(1200);
  console.log('  真实点击 ('+b.x+','+b.y+') 传播日志:');
  console.log('    ' + await ev(`(window.__log||[]).join(' || ')||'一条都没触发'`));
  console.log('  灯箱: ' + await ev(`!!document.querySelector('.el-image-viewer__wrapper')`));
  ws.close(); child.kill();
})();
