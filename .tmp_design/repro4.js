const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9590);
  const base = process.argv[2] || 'http://47.93.14.11';
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysr4'+port,'about:blank'], { stdio:'ignore' });
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
  console.log(await ev(`(function(){var col=document.querySelector('.img-col');if(!col)return 'no img-col';
    var r=col.getBoundingClientRect();var x=Math.round(r.x+r.width/2),y=Math.round(r.y+r.height/2);
    var top=document.elementFromPoint(x,y);var chain=[];var n=top;
    while(n&&chain.length<7){var cs=getComputedStyle(n);chain.push(n.tagName+'.'+String(n.className).split(' ').slice(0,2).join('.')+' pe='+cs.pointerEvents+' z='+cs.zIndex+' pos='+cs.position);n=n.parentElement;}
    return '点('+x+','+y+') 最上层: '+chain.join('  <=  ')+'   命中img-col='+(col.contains(top)||top===col);})()`));
  console.log(await ev(`(function(){var col=document.querySelector('.img-col').getBoundingClientRect();
    var o=[];document.querySelectorAll('body *').forEach(function(n){var r=n.getBoundingClientRect();
      if(r.width<40||r.height<40)return;
      if(r.top<col.top+col.height&&r.bottom>col.top&&r.left<col.left+col.width&&r.right>col.left){
        var cs=getComputedStyle(n);
        if(cs.position==='fixed'||cs.position==='sticky'||parseInt(cs.zIndex)>0||cs.pointerEvents==='auto'&&n!==col&&col.parentElement&&!col.parentElement.contains(n)&&n!==document.body&&!n.contains(col)&&!col.contains(n))
          o.push(n.tagName+'.'+String(n.className).split(' ').slice(0,2).join('.')+' ['+Math.round(r.left)+','+Math.round(r.top)+' '+Math.round(r.width)+'x'+Math.round(r.height)+'] z='+(cs.zIndex||'-')+' '+cs.position);}});
    return '压在图片上方的元素('+o.length+'): '+o.slice(0,12).join(' | ');})()`));
  ws.close(); child.kill();
})();
