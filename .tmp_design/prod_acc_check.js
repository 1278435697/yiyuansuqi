const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const fs = require('fs');
const port = 9342;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp9',
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
const URL = 'http://47.93.14.11/accessories/index.html?_ts=20261023';
const EXPR = `(() => {
  const nav = document.querySelector('.site-nav');
  const inner = document.querySelector('.header-inner');
  const login = document.querySelector('.login-link');
  const header = document.querySelector('.site-header');
  const links = [...nav.querySelectorAll('a')];
  const cs = getComputedStyle(links[0]);
  const act = nav.querySelector('.is-active');
  const nr = nav.getBoundingClientRect(), lr = login.getBoundingClientRect();
  return JSON.stringify({
    vw: innerWidth,
    cssHref: document.querySelector('link[rel=stylesheet]').getAttribute('href'),
    docOverflow: document.documentElement.scrollWidth - innerWidth,
    headerH: Math.round(header.getBoundingClientRect().height),
    rows: new Set(links.map(a => Math.round(a.getBoundingClientRect().top))).size,
    overlap: Math.round(nr.right - lr.left),
    navCount: links.length,
    museum: links.find(a=>a.textContent.includes('博物馆')).getAttribute('href'),
    tryon: links.find(a=>a.textContent.includes('试穿')).getAttribute('href'),
    fontSize: cs.fontSize, pad: cs.padding, radius: cs.borderRadius,
    activeBg: act ? getComputedStyle(act).backgroundColor : null,
    activeShadow: act ? getComputedStyle(act).boxShadow : null,
    cards: document.querySelectorAll('.acc-card').length,
  });
})()`;
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable'); await send('Network.enable');
  const errs = []; const fails = [];
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.method === 'Runtime.exceptionThrown') errs.push((m.params.exceptionDetails.exception || {}).description || m.params.exceptionDetails.text);
    if (m.method === 'Network.loadingFailed') fails.push(m.params.errorText);
  });
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL });
  await sleep(9000);
  console.log('PROD', await (await send('Runtime.evaluate', { expression: EXPR, returnByValue: true })).result.value);
  console.log('JS_ERRORS', JSON.stringify(errs.slice(0, 3)));
  console.log('NET_FAILS', JSON.stringify(fails.slice(0, 5)));
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/prod-acc-header.png', Buffer.from(shot.data, 'base64'));
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 130, deviceScaleFactor: 1, mobile: false });
  await sleep(1500);
  const s2 = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/prod-acc-header-crop.png', Buffer.from(s2.data, 'base64'));
  ws.close(); child.kill(); process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
