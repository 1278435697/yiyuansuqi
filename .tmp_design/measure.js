const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');

const url = process.argv[2] || 'file:///D:/yisu-ai-platform/frontend/public/accessories/index.html';
const width = Number(process.argv[3] || 420);
const port = 9333;

const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp',
  '--window-size=' + width + ',900', 'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function target() {
  for (let i = 0; i < 40; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/list`);
      const list = await res.json();
      const page = list.find((t) => t.type === 'page');
      if (page) return page;
    } catch {}
    await sleep(250);
  }
  throw new Error('no devtools target');
}

function cdp(ws) {
  let id = 0;
  const pending = new Map();
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    }
  });
  return (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id;
    pending.set(n, { resolve, reject });
    ws.send(JSON.stringify({ id: n, method, params }));
  });
}

const EXPR = `(() => {
  const d = document.documentElement, out = {vw: innerWidth, sw: d.scrollWidth, offenders: []};
  document.querySelectorAll('body *').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.right > innerWidth + 1 && r.width > 0) {
      out.offenders.push({
        sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + '.' + String(el.className).trim().split(/\\s+/).join('.'),
        left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width),
      });
    }
  });
  out.offenders = out.offenders.slice(0, 20);
  return JSON.stringify(out, null, 1);
})()`;

(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: true });
  await send('Page.navigate', { url });
  await sleep(6000);
  const r = await send('Runtime.evaluate', { expression: EXPR, returnByValue: true });
  console.log(r.result.value);
  ws.close();
  child.kill();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
