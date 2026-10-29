// 款式卡布局根因：--thumb-height 是否生效 / 图是否溢出盖住文字 / 键盘激活对照实验
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/round6';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9481;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysroot6' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const key = async (k, code, vk) => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(800);
  };
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 66 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(7000);

  console.log('1 变量与几何    ' + await ev(`(function(){
    var grid=document.querySelector(".picker .grid")||document.querySelector(".grid");
    var c=document.querySelector(".garment-card"),t=c.querySelector(".thumb"),im=c.querySelector(".thumb img"),b=c.querySelector(".card-body");
    var R=function(e){var r=e.getBoundingClientRect();return [Math.round(r.y),Math.round(r.height)]};
    return JSON.stringify({
      grid_style_var:grid?getComputedStyle(grid).getPropertyValue("--thumb-height"):"无grid",
      grid_inline:grid?String(grid.getAttribute("style")):"",
      thumb_height_css:getComputedStyle(t).height,
      卡R:R(c),thumbR:R(t),imgR:R(im),bodyR:R(b),
      img_intrinsic:im.naturalWidth+"x"+im.naturalHeight,
      img_超出卡:Math.round(R(im)[1]-R(c)[1]),
      body样式:getComputedStyle(b).visibility+"/"+getComputedStyle(b).opacity,
      谁在上:im.getBoundingClientRect().top<b.getBoundingClientRect().top?"img覆盖body":"body在上"
    })})()`));

  await ev(`(function(){var c=document.querySelector(".garment-card");c.scrollIntoView({block:"center"});return 1})()`);
  await sleep(900);
  await shot('tryon_garment_card');

  // 2) 键盘激活对照：造一个原生 button 和一个 el-button，看 CDP 的 Enter/Space 能否激活
  console.log('2 键盘激活对照  ' + await ev(`(function(){
    window.__act=[];
    var b=document.createElement("button");b.id="ctrl-btn";b.textContent="ctrl";
    b.addEventListener("click",function(){window.__act.push("native-click")});
    document.body.appendChild(b);b.focus();return document.activeElement.id})()`));
  await key('Enter', 'Enter', 13);
  await key('Space', 'Space', 32);
  console.log('   原生 button  ' + await ev('JSON.stringify(window.__act)') + '  (若为空=我的按键仪器不能激活原生按钮，不能据此判站点)');

  // 3) 用真实键盘走一遍：先 Tab 到款式卡再回车（与上面同仪器，看是否一致）
  await ev(`(function(){var c=document.querySelector(".garment-card");if(c)c.click();return 1})()`); await sleep(900);
  console.log('3 JS click 选中 ' + await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`));

  ws.close(); child.kill();
  console.log('\nDONE ' + outDir);
}
main();
