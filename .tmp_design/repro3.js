const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9582);
  const base = process.argv[2] || 'http://47.93.14.11';
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysr3'+port,'about:blank'], { stdio:'ignore' });
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
  const logs=[];
  ws.onmessage2=null;
  await send('Log.enable',{}).catch(()=>{});
  await send('Runtime.evaluate',{expression:'window.__errs=[];window.addEventListener("error",function(e){window.__errs.push(String(e.message))});window.addEventListener("unhandledrejection",function(e){window.__errs.push("rej:"+String(e.reason&&e.reason.message||e.reason))});',returnByValue:true}).catch(()=>{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:base+'/pattern/32'}); await sleep(11000);
  console.log('### '+base);
  console.log(await ev(`(function(){var col=document.querySelector('.img-col');if(!col)return 'no img-col';
    var r=col.getBoundingClientRect();var x=Math.round(r.x+r.width/2),y=Math.round(r.y+r.height/2);
    var top=document.elementFromPoint(x,y);var chain=[];var n=top;
    while(n&&chain.length<8){chain.push(n.tagName+'.'+String(n.className).split(' ').slice(0,2).join('.')+'(pe='+getComputedStyle(n).pointerEvents+',z='+getComputedStyle(n).zIndex+')');n=n.parentElement;}
    return '点击点('+x+','+y+') 最上层链:\n  '+chain.join('\n  ')+'\n  命中 .img-col? '+(col.contains(top)||top===col);})()`));
  const box=JSON.parse(await ev(`(function(){var r=document.querySelector('.img-col').getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`));
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:box.x,y:box.y,button:'left',clickCount:1});
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:box.x,y:box.y,button:'left',clickCount:1});
  await sleep(2000);
  console.log('  点击后 viewer=' + await ev(`!!document.querySelector('.el-image-viewer__wrapper')`));
  console.log('  合成 click 直发 .img-col=' + await ev(`(function(){var c=document.querySelector('.img-col');c.click();return 'dispatched'})()`));
  await sleep(1500);
  console.log('  再查 viewer=' + await ev(`!!document.querySelector('.el-image-viewer__wrapper')`));
  console.log('  页面异常: ' + await ev(`(window.__errs||[]).join(' | ')||'无'`));
  ws.close(); child.kill();
})();
