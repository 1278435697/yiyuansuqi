const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = 9540;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/yspt','about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  const ev=async e=>{const r=await send('Runtime.evaluate',{expression:e,returnByValue:true});
    if(r.result.exceptionDetails) return 'EXC '+JSON.stringify(r.result.exceptionDetails.exception||r.result.exceptionDetails.text).slice(0,160);
    return r.result.result.value;};
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  const base = process.argv[2] || 'http://47.93.14.11';
  await send('Page.navigate',{url:base+'/pattern/32'}); await sleep(10000);
  console.log('URL '+base+'/pattern/32');
  console.log('  详情页 DOM: ' + await ev(`(function(){var o=[];
    o.push('.img-col 存在='+!!document.querySelector('.img-col'));
    var im=document.querySelector('.img-col img');
    o.push(im? 'img src='+im.src.slice(0,60)+' complete='+im.complete+' naturalW='+im.naturalWidth+' 显示='+(im.getBoundingClientRect().width>0) : 'img 不存在');
    o.push('count-badge='+(document.querySelector('.count-badge')||{}).textContent);
    o.push('.p-modal-title-row h2='+((document.querySelector('.p-modal-title-row h2')||{}).textContent||'?'));
    o.push('.app-main 高度='+Math.round(document.querySelector('.app-main').getBoundingClientRect().height));
    return o.join('\n    ');})()`));
  const box = await ev(`(function(){var e=document.querySelector('.img-col');if(!e)return 'none';var r=e.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});})()`);
  console.log('  点击坐标 '+box);
  if (box !== 'none') {
    const c = JSON.parse(box);
    await send('Input.dispatchMouseEvent',{type:'mousePressed',x:c.x,y:c.y,button:'left',clickCount:1});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:c.x,y:c.y,button:'left',clickCount:1});
    await sleep(2500);
  }
  console.log('  灯箱: ' + await ev(`(function(){var v=document.querySelector('.el-image-viewer__wrapper');
    if(!v)return '未打开（点击后没有 .el-image-viewer__wrapper）';
    var o=[];
    o.push('已打开 imgs='+v.querySelectorAll('.el-image-viewer__img').length);
    o.push('左箭头 .arrow-left 存在='+!!v.querySelector('.el-image-viewer__prev')+' 可见='+(v.querySelector('.el-image-viewer__prev')?getComputedStyle(v.querySelector('.el-image-viewer__prev')).display:'-'));
    o.push('右箭头 .arrow-right 存在='+!!v.querySelector('.el-image-viewer__next')+' 可见='+(v.querySelector('.el-image-viewer__next')?getComputedStyle(v.querySelector('.el-image-viewer__next')).display:'-'));
    o.push('工具条 .el-image-viewer__actions 存在='+!!v.querySelector('.el-image-viewer__actions')+' 内容='+((v.querySelector('.el-image-viewer__actions')||{}).textContent||'').trim().slice(0,30));
    var im=v.querySelector('.el-image-viewer__img');
    o.push('当前图 '+(im?('src='+im.src.slice(0,50)+' naturalW='+im.naturalWidth+' w='+Math.round(im.getBoundingClientRect().width)):'无'));
    return o.join('\n    ');})()`));
  ws.close(); child.kill();
})();
