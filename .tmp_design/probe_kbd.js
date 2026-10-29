const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const port = Number(process.env.PORT || 9440);
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new','--disable-gpu','--no-sandbox',`--remote-debugging-port=${port}`,'--user-data-dir='+require('os').tmpdir()+'/ysk'+port,'about:blank'], { stdio:'ignore' });
  let ws;
  for (let i=0;i<60;i++){ try{ const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const t=l.find(x=>x.type==='page'); if(!t) throw 0; ws=new WebSocket(t.webSocketDebuggerUrl);
    await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej}); break;}catch{await sleep(250);} }
  let id=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m);delete p[m.id];}};
  const send=(method,params)=>new Promise(r=>{const i=++id;p[i]=r;ws.send(JSON.stringify({id:i,method,params}));});
  const ev=async e=>{const r=await send('Runtime.evaluate',{expression:e,returnByValue:true});
    if(r.error) throw new Error(JSON.stringify(r.error).slice(0,200));
    if(r.result.exceptionDetails) return 'EXC: '+(r.result.exceptionDetails.exception||{}).description||JSON.stringify(r.result.exceptionDetails).slice(0,200);
    if(r.result.result.value===undefined) return 'UNDEF '+(r.result.result.type)+' '+(r.result.result.description||'');
    return r.result.result.value;};
  await send('Runtime.enable',{}); await send('Page.enable',{});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:(process.env.BASE||'http://localhost:5173')+'/tryon'}); await sleep(9000);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});

  console.log('--- 上传区可达性 ---');
  console.log(await ev(`(function(){
    var fi=document.querySelector('input[type=file]');
    var out=[];
    if(!fi){out.push('页面上没有 input[type=file]');}
    else{var cs=getComputedStyle(fi);
      out.push('input[type=file] display='+cs.display+' vis='+cs.visibility+' op='+cs.opacity+' pos='+cs.position+' w='+Math.round(fi.getBoundingClientRect().width)+' tabindex='+fi.getAttribute('tabindex'));
      out.push('  可聚焦? '+(!!(fi.offsetWidth||fi.offsetHeight||fi.getClientRects().length)));
    }
    var dz=document.querySelector('.upload-zone,.drop-zone,[class*=upload]');
    if(dz){out.push('dropzone: '+dz.tagName+'.'+dz.className.toString().slice(0,40)+' tabindex='+dz.getAttribute('tabindex')+' role='+dz.getAttribute('role')+' aria-label='+dz.getAttribute('aria-label'));
      out.push('  键盘事件: onclick='+(!!dz.onclick)+' onkeydown='+(!!dz.onkeydown));}
    return out.join('\n');})()`));

  console.log('\n--- 走 40 跳，找 input[type=file] 与生成按钮 ---');
  const seq=[];
  for(let i=0;i<40;i++){
    seq.push(await ev(`(function(){var a=document.activeElement;if(!a)return '-';
      return a.tagName+'['+(a.type||'')+'] '+(a.className||'').toString().split(' ').slice(0,2).join('.')+' "'+(a.getAttribute('aria-label')||a.textContent||'').trim().slice(0,10)+'";})()`));
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    await sleep(120);
  }
  console.log(seq.map((s,i)=>(i+1)+'. '+s).join('\n'));
  console.log('\n是否出现 file input: '+seq.some(s=>/INPUT\[file\]/.test(s)));

  console.log('\n--- 聚焦搜索框时外层 wrapper 的可见焦点 ---');
  console.log(await ev(`(function(){
    var inp=document.querySelector('.app-main .el-input__inner'); if(!inp) return '无 el-input';
    inp.focus();
    var w=inp.closest('.el-input__wrapper'); var cs=getComputedStyle(w);
    var ics=getComputedStyle(inp);
    return 'input outline='+ics.outlineStyle+' '+ics.outlineWidth+
      '\nwrapper box-shadow='+cs.boxShadow.slice(0,90)+'\nwrapper border='+cs.border+' outline='+cs.outlineStyle;})()`));

  console.log('\n--- 聚焦 el-select 时 ---');
  console.log(await ev(`(function(){var s=document.querySelector('.app-main .el-select__wrapper'); if(!s) return '无';
    var i=s.querySelector('input'); if(i)i.focus();
    return 'select wrapper box-shadow='+getComputedStyle(s).boxShadow.slice(0,90);})()`));

  console.log('\n--- 聚焦 el-switch 时 core 是否有焦点环 ---');
  console.log(await ev(`(function(){var sw=document.querySelector('.app-main .el-switch'); if(!sw) return '无';
    var i=sw.querySelector('input'); i.focus();
    var core=sw.querySelector('.el-switch__core'); var cs=getComputedStyle(core);
    return 'switch input rect='+JSON.stringify(i.getBoundingClientRect())+' outline='+getComputedStyle(i).outlineStyle+
      '\ncore box-shadow='+cs.boxShadow.slice(0,90)+' outline='+cs.outlineStyle;})()`));

  console.log('\n--- 聚焦 el-radio-button(快速/高清) 时 label 是否有焦点态 ---');
  console.log(await ev(`(function(){var l=document.querySelector('.app-main .el-radio-button'); if(!l) return '无';
    var i=l.querySelector('input'); i.focus();
    return 'inner label class='+l.querySelector('.el-radio-button__inner').className+
      '\ninner box-shadow='+getComputedStyle(l.querySelector('.el-radio-button__inner')).boxShadow.slice(0,90);})()`));

  console.log('\n--- 上传 dropzone 键盘 Enter/Space 实测 ---');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  console.log(await ev(`(function(){
    var fi=document.querySelector('input[type=file]');
    var opened=false; var orig=fi?fi.click:null;
    if(fi){ fi.click=function(){opened=true;}; }
    var dz=document.querySelector('.upload-zone,.drop-zone,[class*=upload]');
    if(dz){ dz.focus && dz.focus();
      dz.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
      dz.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',bubbles:true})); }
    var r='Enter 触发文件选择? '+opened;
    if(fi) fi.click=orig;
    return r;})()`));
  ws.close(); child.kill();
})();
