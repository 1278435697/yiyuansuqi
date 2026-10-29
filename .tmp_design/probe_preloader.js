const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9336;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp4',
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
const BASE = 'http://localhost:5199';
const CASES = [
  { path: '/', expect: true, label: '首页直链' },
  { path: '/aiqa', expect: false, label: '溯源问答直链' },
  { path: '/museum', expect: false, label: '博物馆直链' },
  { path: '/archive', expect: false, label: '档案直链' },
];
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const c of CASES) {
    await send('Page.navigate', { url: BASE + c.path });
    await sleep(1200);
    const r = await send('Runtime.evaluate', {
      expression: `JSON.stringify({pl: !!document.querySelector('.yisu-preloader'), path: location.pathname})`,
      returnByValue: true,
    });
    const got = JSON.parse(r.result.value);
    const ok = got.pl === c.expect;
    console.log(`${ok ? 'PASS' : 'FAIL'}  ${c.label.padEnd(14)} path=${got.path} preloader=${got.pl} (期望 ${c.expect})`);
    await sleep(2500);
    const after = await send('Runtime.evaluate', { expression: `JSON.stringify({pl: !!document.querySelector('.yisu-preloader')})`, returnByValue: true });
    console.log(`      +3.7s 后 preloader=${JSON.parse(after.result.value).pl}`);
  }
  ws.close();
  child.kill();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
