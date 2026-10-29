const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const fs = require('fs');
const port = 9338;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp6',
  '--window-size=1440,900', 'about:blank',
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
const URL = 'file:///D:/yisu-ai-platform/frontend/public/accessories/index.html';
const EXPR = `(() => {
  const nav = document.querySelector('.site-nav');
  const inner = document.querySelector('.header-inner');
  const login = document.querySelector('.login-link');
  const header = document.querySelector('.site-header');
  const nr = nav.getBoundingClientRect(), lr = login.getBoundingClientRect(), ir = inner.getBoundingClientRect();
  const links = [...nav.querySelectorAll('a')];
  const rows = new Set(links.map(a => Math.round(a.getBoundingClientRect().top))).size;
  return JSON.stringify({
    vw: innerWidth,
    docOverflow: document.documentElement.scrollWidth - innerWidth,
    headerH: Math.round(header.getBoundingClientRect().height),
    navRight: Math.round(nr.right), loginLeft: Math.round(lr.left),
    overlap: Math.round(nr.right - lr.left),
    rows,
    navFits: Math.round(ir.width) - (Math.round(nr.right - ir.left) + 26 + Math.round(lr.width)) >= 0,
    fontSize: getComputedStyle(links[0]).fontSize,
  });
})()`;
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  for (const w of [1121, 1200, 1280, 1366, 1440, 1600, 1920]) {
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: 900, deviceScaleFactor: 1, mobile: false });
    await send('Page.navigate', { url: URL });
    await sleep(2600);
    const r = await send('Runtime.evaluate', { expression: EXPR, returnByValue: true });
    console.log(r.result.value);
  }
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 130, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL });
  await sleep(4000);
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/cmp-acc-header-v2.png', Buffer.from(shot.data, 'base64'));
  await send('Emulation.setDeviceMetricsOverride', { width: 1240, height: 130, deviceScaleFactor: 1, mobile: false });
  await sleep(2500);
  const shot2 = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/cmp-acc-header-1240.png', Buffer.from(shot2.data, 'base64'));
  ws.close();
  child.kill();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
