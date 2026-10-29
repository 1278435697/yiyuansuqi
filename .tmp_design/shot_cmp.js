const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const fs = require('fs');

const JOBS = [
  { out: 'cmp-main-header.png', url: 'http://47.93.14.11/', w: 1440, h: 130 },
  { out: 'cmp-acc-header.png', url: 'file:///D:/yisu-ai-platform/frontend/public/accessories/index.html', w: 1440, h: 130 },
];

const port = 9334;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp2',
  '--window-size=1440,1600', 'about:blank',
], { stdio: 'ignore' });

async function target() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
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
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id);
      pending.delete(m.id);
      m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result);
    }
  });
  return (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id;
    pending.set(n, { resolve, reject });
    ws.send(JSON.stringify({ id: n, method, params }));
  });
}

(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  for (const job of JOBS) {
    await send('Emulation.setDeviceMetricsOverride', { width: job.w, height: job.h, deviceScaleFactor: 1, mobile: false });
    await send('Page.navigate', { url: job.url });
    await sleep(7000);
    await send('Runtime.evaluate', { expression: 'window.scrollTo(0,0);"ok"' });
    await sleep(500);
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/' + job.out, Buffer.from(shot.data, 'base64'));
    const m = await send('Runtime.evaluate', { expression: 'JSON.stringify({vw:innerWidth,sw:document.documentElement.scrollWidth})', returnByValue: true });
    console.log(job.out, m.result.value);
  }
  ws.close();
  child.kill();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
