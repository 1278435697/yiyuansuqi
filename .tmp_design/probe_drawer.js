const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const fs = require('fs');
const port = 9339;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp7',
  '--window-size=420,760', 'about:blank',
], { stdio: 'ignore' });
async function target() {
  for (let i = 0; i < 60; i++) {
    try {
      const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const p = l.find((t) => t.type === 'page');
      if (p) return p;
    } catch {}
    await sleep(250);
  }
  throw new Error('no target');
}
function cdp(ws) {
  let id = 0; const pend = new Map();
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); }
  });
  return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); });
}
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 420, height: 760, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'file:///D:/yisu-ai-platform/frontend/public/accessories/index.html' });
  await sleep(4000);
  const r = await send('Runtime.evaluate', {
    expression: `document.querySelector('.menu-toggle').click(); JSON.stringify({
      open: document.querySelector('.site-header').classList.contains('nav-open'),
      navDisplay: getComputedStyle(document.querySelector('.site-nav')).display,
      firstLink: (()=>{const a=document.querySelector('.site-nav a');const s=getComputedStyle(a);return {fs:s.fontSize,pad:s.padding,radius:s.borderRadius,bg:s.backgroundColor}})()
    })`,
    returnByValue: true,
  });
  console.log(r.result.value);
  await sleep(600);
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/cmp-acc-drawer.png', Buffer.from(shot.data, 'base64'));
  ws.close();
  child.kill();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
