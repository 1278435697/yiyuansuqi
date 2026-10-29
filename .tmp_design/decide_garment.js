// 决定性测试：款式卡上每个命中点落在什么元素上；键盘 Enter 是否真的选中；有无提示
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const port = 9473;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysdec' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 200);
    return r.result.result.value;
  };
  const clickAt = async (x, y, w = 1400) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  const key = async (k, code, vk) => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(900);
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(7000);

  // 卡片所在步骤：可能需要先滚到选款区
  console.log('0 步骤标记      ' + await ev(`JSON.stringify({stepper:[].slice.call(document.querySelectorAll(".pipeline-stepper *, .step, .stepper")).slice(0,3).map(function(e){return (e.innerText||"").replace(/\\s+/g,"").slice(0,12)}),卡数:document.querySelectorAll(".garment-card").length})`));

  // 1) 把第一张卡滚进视野正中，然后扫描命中点
  const scan = await ev(`(function(){
    var c=document.querySelector(".garment-card");if(!c)return "NO";
    c.scrollIntoView({block:"center"});
    return JSON.stringify({y:Math.round(c.getBoundingClientRect().y)})})()`);
  await sleep(1200);
  const grid = await ev(`(function(){
    var c=document.querySelector(".garment-card");var r=c.getBoundingClientRect();
    var hits={};var samples=[];
    for(var fy=0.08;fy<0.98;fy+=0.06){for(var fx=0.08;fx<0.98;fx+=0.06){
      var x=Math.round(r.x+r.width*fx),y=Math.round(r.y+r.height*fy);
      var h=document.elementFromPoint(x,y);
      var tag=h?(h.tagName+"."+(h.className||"").toString().slice(0,14)):"null";
      hits[tag]=(hits[tag]||0)+1;
      if(samples.length<3&&/BUTTON|STRONG|card-body/.test(tag))samples.push([x,y,tag]);}}
    return JSON.stringify({卡:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],命中分布:hits,非图样本:samples})})()`);
  console.log('1 卡命中分布    ' + grid);
  const g = JSON.parse(grid);
  const only = Object.keys(g.命中分布).join(' | ');
  console.log('   可视高度 ' + g.卡[3] + '，缩略图 ' + await ev(`(function(){var i=document.querySelector(".garment-card .thumb img");var r=i.getBoundingClientRect();return Math.round(r.height)})()`));

  // 2) 真鼠标点卡片正中（会命中 IMG）
  await clickAt(g.卡[0] + Math.round(g.卡[2] / 2), g.卡[1] + Math.round(g.卡[3] / 2), 1600);
  console.log('2 点卡片正中    is-active ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`) +
    ' | 全局灯箱 ' + await ev(`!!document.querySelector(".ys-lightbox")`) + ' | 提示 ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".el-message,.el-message__content")).map(function(e){return e.innerText}))`));
  await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700);

  // 3) 键盘 Enter（目标 = BUTTON 本身，不经 img）
  await ev(`(function(){document.querySelector(".garment-card").focus();return 1})()`); await sleep(400);
  await key('Enter', 'Enter', 13);
  console.log('3 键盘 Enter    is-active ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`) +
    ' | 灯箱 ' + await ev(`!!document.querySelector(".ys-lightbox")`) + ' | 提示 ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".el-message,.el-message__content")).map(function(e){return e.innerText}))`));
  await key('Space', 'Space', 32);
  console.log('  键盘 Space    is-active ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`));

  // 4) 直接 JS 点击 button 元素（绕过 img 目标）作机制对照
  console.log('4 JS click 卡   ' + await ev(`(function(){document.querySelector(".garment-card").click();return 1})()`) ? '已触发' : 'err');
  await sleep(1100);
  console.log('   is-active    ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`) + ' | 灯箱 ' + await ev(`!!document.querySelector(".ys-lightbox")`));

  // 5) 断图占位的卡（thumb-fallback）能否点选
  console.log('5 fallback卡数  ' + await ev(`document.querySelectorAll(".thumb-fallback").length`));
  ws.close(); child.kill();
  console.log('\nDONE');
}
main();
