const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9600);
  const base = process.argv[2] || 'http://47.93.14.11';
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysr5'+port,'about:blank'], { stdio:'ignore' });
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
  // 记录浏览器真实派发的 click 事件
  await ev(`(function(){window.__clicks=[];document.addEventListener('click',function(e){window.__clicks.push(e.target.tagName+'.'+String(e.target.className).slice(0,16))},true);return 1})()`);
  const b = JSON.parse(await ev(`(function(){var r=document.querySelector('.img-col').getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`));
  console.log('### '+base+'  点击 ('+b.x+','+b.y+')');
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:b.x,y:b.y});
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:b.x,y:b.y,button:'left',buttons:1,clickCount:1});
  await sleep(120);
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:b.x,y:b.y,button:'left',buttons:0,clickCount:1});
  await sleep(2200);
  console.log('  浏览器收到的 click: ' + await ev(`(window.__clicks||[]).join(' | ')||'一个都没有'`));
  console.log('  灯箱: ' + await ev(`(function(){var v=document.querySelector('.el-image-viewer__wrapper');if(!v)return '未打开';
    var pv=v.querySelector('.el-image-viewer__prev'),nx=v.querySelector('.el-image-viewer__next'),ac=v.querySelector('.el-image-viewer__actions');
    var im=v.querySelector('.el-image-viewer__img');
    return '已开 imgs='+v.querySelectorAll('.el-image-viewer__img').length
      +' 左='+(pv?getComputedStyle(pv).display+'/'+getComputedStyle(pv).opacity:'无')
      +' 右='+(nx?getComputedStyle(nx).display+'/'+getComputedStyle(nx).opacity:'无')
      +' 工具条按钮='+(ac?ac.querySelectorAll('button').length:'无')
      +' 当前图宽='+(im?Math.round(im.getBoundingClientRect().width):'-');})()`));
  if (await ev(`!!document.querySelector('.el-image-viewer__wrapper')`)===true) {
    console.log('  点右箭头: ' + await ev(`(function(){var n=document.querySelector('.el-image-viewer__next');if(!n)return '无右箭头';var s=document.querySelector('.el-image-viewer__img');var before=s?s.src:'';n.click();return 'clicked'})()`));
    await sleep(1500);
    console.log('  换图后: ' + await ev(`(function(){var s=document.querySelector('.el-image-viewer__img');var c=document.querySelector('.el-image-viewer__indicator');return (s?s.src.slice(0,44):'无图')+' 指示='+(c?c.textContent.trim():'无')})()`));
  }
  ws.close(); child.kill();
})();
