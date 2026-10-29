const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9570);
  const base = process.argv[2] || 'http://47.93.14.11';
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysr2'+port,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const mm=JSON.parse(e.data); if(p[mm.id]){p[mm.id](mm);delete p[mm.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  const ev=async label=>{const e=CASES[label];const r=await send('Runtime.evaluate',{expression:e,returnByValue:true});
    const ed=r.result.exceptionDetails;
    if(ed) return 'ERR '+(ed.exception&&ed.exception.description?ed.exception.description.split('\n')[0]:ed.text);
    return r.result.result.value;};
  const CASES = {
    dom: `(function(){var o=[];var m=document.querySelector('.app-main');o.push('app-main='+(m?'h='+Math.round(m.getBoundingClientRect().height):'NULL'));
      var col=document.querySelector('.img-col');o.push('img-col='+(col?'yes':'no'));
      var im=document.querySelector('.img-col img');o.push(im?('img src='+im.src.slice(0,46)+' complete='+im.complete+' naturalW='+im.naturalWidth+' box='+Math.round(im.getBoundingClientRect().width)+'x'+Math.round(im.getBoundingClientRect().height)):'img=no');
      var b=document.querySelector('.count-badge');o.push('badge='+(b?b.textContent:'no'));
      var t=document.querySelector('.p-modal-title-row h2');o.push('title='+(t?t.textContent.trim():'no'));
      return o.join(' | ');})()`,
    pos: `(function(){var e=document.querySelector('.img-col');if(!e)return 'none';var r=e.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});})()`,
    viewer: `(function(){var v=document.querySelector('.el-image-viewer__wrapper');if(!v)return '灯箱未打开';var o=[];
      o.push('imgs='+v.querySelectorAll('.el-image-viewer__img').length);
      var pv=v.querySelector('.el-image-viewer__prev'), nx=v.querySelector('.el-image-viewer__next');
      o.push('左箭头='+(pv?('display='+getComputedStyle(pv).display+' op='+getComputedStyle(pv).opacity+' aria='+pv.getAttribute('aria-label')):'不存在'));
      o.push('右箭头='+(nx?('display='+getComputedStyle(nx).display+' op='+getComputedStyle(nx).opacity+' aria='+nx.getAttribute('aria-label')):'不存在'));
      var ac=v.querySelector('.el-image-viewer__actions');
      o.push('工具条='+(ac?('存在 按钮数='+ac.querySelectorAll('button').length+' 文字='+ac.textContent.trim().slice(0,20)):'不存在'));
      var im=v.querySelector('.el-image-viewer__img');
      o.push('当前图='+(im?(im.src.slice(0,40)+' naturalW='+im.naturalWidth+' box='+Math.round(im.getBoundingClientRect().width)+'x'+Math.round(im.getBoundingClientRect().height)):'无'));
      return o.join(' | ');})()`,
  };
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:base+'/pattern/32'}); await sleep(11000);
  console.log('### '+base+'/pattern/32');
  console.log('  '+await ev('dom'));
  const box=await ev('pos'); console.log('  点击 '+box);
  if(box!=='none'){const c=JSON.parse(box);
    await send('Input.dispatchMouseEvent',{type:'mousePressed',x:c.x,y:c.y,button:'left',clickCount:1});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:c.x,y:c.y,button:'left',clickCount:1});
    await sleep(2500);}
  console.log('  '+await ev('viewer'));
  ws.close(); child.kill();
})();
