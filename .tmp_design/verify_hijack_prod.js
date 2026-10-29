// 真实鼠标点击验证：img 在 A/BUTTON 内是否被全局灯箱抢占；开场动画键盘能否进入
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const port = 9437;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yshij' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 200);
    return r.result.result.value;
  };
  const key = async (k, code, vk) => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(400);
  };
  const clickAt = async (x, y, w = 1200) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  // 用 JS 找到第一个「img 在指定宿主内」的图，返回其中心坐标
  const pick = (hostSel) => ev(`(function(){
    var hosts=[].slice.call(document.querySelectorAll(${JSON.stringify(hostSel)}));
    var native=0;
    for(var i=0;i<hosts.length;i++){var h=hosts[i];var im=h.querySelector("img");if(!im)continue;
      if(im.closest("[data-lb-native]")){native++;continue;}
      var r=im.getBoundingClientRect();if(r.width<20||r.height<20)continue;
      return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0,alt:(im.alt||"").slice(0,22),host:h.tagName,href:h.getAttribute("href")||""});}
    return "NONE hosts=" + hosts.length + " native=" + native;})()`);

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  const LB = `JSON.stringify({全局灯箱:!!document.querySelector(".ys-lightbox"),灯箱图:((document.querySelector(".ys-lightbox img")||{}).src||"").split("/").pop()})`;

  // A) 首页资讯卡：img 在 <a> 内
  await send('Page.navigate', { url: base + '/' });
  await sleep(6500);
  await ev(`(function(){var a=document.querySelector("a img");if(a)a.scrollIntoView({block:"center"});return 1})()`);
  await sleep(900);
  let q = await pick("a", "img", 1);
  console.log('A 首页·资讯卡图  目标 ' + q);
  if (q[0] === '{') {
    const o = JSON.parse(q); const before = await ev('location.pathname');
    await clickAt(o.x, o.y, 1800);
    console.log('   点图后 路径 ' + before + ' -> ' + await ev('location.pathname') + ' | ' + await ev(LB));
  }

  // B) 首页资讯卡：点同一张卡的文字区（宿主）作对照
  await send('Page.navigate', { url: base + '/' });
  await sleep(6000);
  q = await pick("a", "img", 1);
  if (q[0] === '{') {
    const o = JSON.parse(q);
    const box = await ev(`(function(){var a=document.querySelector("a");var r=a.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width*0.5)|0,y:(r.bottom-8)|0})})()`);
    const b = JSON.parse(box);
    console.log('B 首页·点宿主文字 ' + box);
    await clickAt(b.x, b.y, 1800);
    console.log('   点文字后 路径 ' + await ev('location.pathname') + ' | ' + await ev(LB));
  }

  // C) 试穿：服饰缩略图在 <button> 内
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(6500);
  await ev(`(function(){var b=document.querySelector("button img");if(b)b.scrollIntoView({block:"center"});return 1})()`);
  await sleep(900);
  q = await pick("button", "img", 1);
  console.log('C 试穿·款式按钮图 ' + q);
  if (q[0] === '{') {
    const o = JSON.parse(q);
    const selBefore = await ev(`JSON.stringify([].slice.call(document.querySelectorAll("button")).filter(function(b){return b.className.indexOf("active")>=0||b.getAttribute("aria-pressed")=="true"||String(b.className).indexOf("selected")>=0}).map(function(b){return (b.innerText||"").trim()}).slice(0,4))`);
    await clickAt(o.x, o.y, 1500);
    console.log('   点图 alt=' + o.alt + ' | 灯箱 ' + await ev(LB));
    console.log('   选中态 ' + selBefore + ' -> ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll("button")).filter(function(b){return b.className.indexOf("active")>=0||b.getAttribute("aria-pressed")=="true"||String(b.className).indexOf("selected")>=0}).map(function(b){return (b.innerText||"").trim()}).slice(0,4))`));
    // 对照：点同一 button 的非图区域
    await ev(`(function(){var b=document.querySelector(".ys-lightbox .lb-close");if(b)b.click();return 1})()`);
    await sleep(600);
    const btnBox = await ev(`(function(){var b=document.querySelector("button img");if(!b)return "NO";var h=b.closest("button");var r=h.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.bottom-6)|0,t:(h.innerText||"").trim().slice(0,12)})})()`);
    console.log('D 试穿·点按钮文字 ' + btnBox);
    if (btnBox[0] === '{') { const d = JSON.parse(btnBox); await clickAt(d.x, d.y, 1500); console.log('   结果 ' + await ev(LB)); }
  }

  // E) 配饰九卷：img 在 <a> 内
  await send('Page.navigate', { url: base + '/accessories' });
  await sleep(6500);
  await ev(`(function(){var a=document.querySelector("a img");if(a)a.scrollIntoView({block:"center"});return 1})()`);
  await sleep(900);
  q = await pick("a", "img", 1);
  console.log('E 配饰·卡片图     ' + q);
  if (q[0] === '{') {
    const o = JSON.parse(q); const before = await ev('location.pathname + location.hash');
    await clickAt(o.x, o.y, 1800);
    console.log('   点图后 ' + before + ' -> ' + await ev('location.pathname + location.hash') + ' | ' + await ev(LB));
  }

  // F) 开场动画：键盘能否进入
  await send('Page.navigate', { url: base + '/user' });
  await sleep(2500);
  console.log('  清 localStorage ' + await ev(`(function(){try{Object.keys(localStorage).forEach(function(k){localStorage.removeItem(k)});return "cleared="+localStorage.length}catch(e){return "ERR "+e.message}})()`));
  await send('Page.navigate', { url: base + '/' });
  await sleep(3000);
  console.log('F 开场层存在      ' + await ev(`JSON.stringify({preloader:!!document.querySelector(".pl-ring-wrap"),可见:!!(document.querySelector(".pl-ring-wrap")&&document.querySelector(".pl-ring-wrap").offsetParent)})`));
  console.log('  原生可聚焦元素  ' + await ev(`[].slice.call(document.querySelectorAll("a[href],button,input,[tabindex]:not([tabindex='-1'])")).filter(function(e){return e.offsetParent}).length`));
  for (let i = 0; i < 12; i++) await key('Tab', 'Tab', 9);
  console.log('  12 次 Tab 落点  ' + await ev(`(document.activeElement.tagName+"."+(document.activeElement.className||"")).slice(0,50)`));
  await key('Enter', 'Enter', 13);
  await sleep(1500);
  console.log('  回车后开场层    ' + await ev(`JSON.stringify({仍在:!!document.querySelector(".pl-ring-wrap"),正文字数:document.body.innerText.replace(/\\s+/g,"").length})`));

  ws.close(); child.kill();
  console.log('\nDONE');
}
main();
