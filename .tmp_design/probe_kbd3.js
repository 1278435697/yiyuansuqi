const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const E = {
  up: `(function(){var fi=document.querySelector('input[type=file]');var o=[];
    if(!fi)o.push('no file input');else{var c=getComputedStyle(fi);o.push('file input display='+c.display+' focusable='+(!!fi.getClientRects().length));}
    var dz=document.querySelector('.drop-zone,.uploader');
    if(!dz)o.push('no dropzone');else o.push('dropzone '+dz.tagName+' tabindex='+dz.getAttribute('tabindex')+' role='+dz.getAttribute('role')+' aria='+dz.getAttribute('aria-label')+' keydown='+(dz.onkeydown?'y':'n'));
    return o.join(' ; ');})()`,
  inp: `(function(){var i=document.querySelector('.app-main .el-input__inner');if(!i)return 'none';i.focus();
    var w=i.closest('.el-input__wrapper');var cs=getComputedStyle(w);var ic=getComputedStyle(i);
    return 'input outline='+ic.outlineStyle+' '+ic.outlineWidth+' | wrapper box-shadow='+cs.boxShadow.slice(0,80)+' border='+cs.borderTopWidth+' '+cs.borderTopColor;})()`,
  sw: `(function(){var s=document.querySelector('.app-main .el-switch');if(!s)return 'none';
    var i=s.querySelector('input');i.focus();var core=s.querySelector('.el-switch__core');
    return 'switchinput rect='+Math.round(i.getBoundingClientRect().width)+'x'+Math.round(i.getBoundingClientRect().height)+' outline='+getComputedStyle(i).outlineStyle+
      ' | core box-shadow='+getComputedStyle(core).boxShadow.slice(0,80);})()`,
  radio: `(function(){var l=document.querySelector('.app-main .el-radio-button');if(!l)return 'none';
    l.querySelector('input').focus();var inner=l.querySelector('.el-radio-button__inner');
    return 'radio inner box-shadow='+getComputedStyle(inner).boxShadow.slice(0,80)+' class='+inner.className;})()`,
  tabs: `(function(){var a=document.querySelector('.app-main .tabs a');if(!a)return 'none';a.focus();var cs=getComputedStyle(a);
    return 'tab a outline='+cs.outlineStyle+' '+cs.outlineWidth+' '+cs.outlineColor+' boxShadow='+cs.boxShadow.slice(0,60)+' h='+Math.round(a.getBoundingClientRect().height);})()`,
  seq: `(function(){var a=document.activeElement;if(!a)return '-';
    var n=(a.getAttribute&&a.getAttribute('aria-label'))||a.textContent||a.value||'';
    return a.tagName+'.'+String(a.className||'').split(' ').slice(0,2).join('.')+' ['+(a.type||'')+'] '+n.trim().slice(0,10);})()`,
};
(async () => {
  let port = Number(process.env.PORT || 9460);
  for (const [side, base] of [['before', 'http://47.93.14.11'], ['after', 'http://localhost:5173']]) {
    const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/yskb'+port,'about:blank'], { stdio:'ignore' });
    let ws;
    for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
    port++;
    let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id];}};
    const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
    const ev=async k=>{const r=await send('Runtime.evaluate',{expression:E[k],returnByValue:true});
      if(r.result.exceptionDetails)return 'EXC '+JSON.stringify(r.result.exceptionDetails).slice(0,150);
      return r.result.result.value;};
    await send('Runtime.enable',{}); await send('Page.enable',{});
    await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
    await send('Page.navigate',{url:base+'/tryon'}); await sleep(9500);
    console.log('\n##### '+side+' '+base);
    for (const k of ['up','inp','sw','radio','tabs']) console.log('  '+k.padEnd(6)+' '+await ev(k));
    const seq=[];
    for(let i=0;i<26;i++){ seq.push(await ev('seq'));
      await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
      await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9}); await sleep(90); }
    console.log('  TAB: '+seq.join(' > '));
    console.log('  file input 在 Tab 序列中: '+/INPUT\.\w* \[file\]|INPUT\S* \[file\]/.test(seq.join(' ')));
    ws.close(); child.kill(); await sleep(600);
  }
})();
