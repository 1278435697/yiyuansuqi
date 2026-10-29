const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9352;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp_mainnav',
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
const EXPR = `(() => {
  const links = [...document.querySelectorAll('.app-nav a')];
  return JSON.stringify({
    count: links.length,
    labels: links.map(a => a.textContent.trim()).join(' '),
    acc: (links.find(a => (a.getAttribute('href')||'').includes('accessories')) || {}).textContent,
    accHref: (links.find(a => a.textContent.trim() === '衣冠') || {}).getAttribute && links.find(a => a.textContent.trim()==='衣冠').getAttribute('href'),
    stillPeishi: labels.some ? undefined : undefined,
    hasPeishi: links.some(a => a.textContent.trim() === '配饰'),
    overflow: document.documentElement.scrollWidth - innerWidth,
  });
})()`.replace('labels.some', 'false');
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'http://localhost:5199/' });
  await sleep(9000);
  console.log('MAINNAV', (await send('Runtime.evaluate', { expression: EXPR, returnByValue: true })).result.value);
  ws.close(); child.kill(); process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
