const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9345;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp_first2',
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
const PROBE = `JSON.stringify({pl: !!document.querySelector('.yisu-preloader'), seen: localStorage.getItem('yisu-preloader-seen'), path: location.pathname})`;
let send;
async function go(path, label, expect) {
  await send('Page.navigate', { url: BASE + path });
  await sleep(1400);
  const r = JSON.parse((await send('Runtime.evaluate', { expression: PROBE, returnByValue: true })).result.value);
  const ok = r.pl === expect;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label.padEnd(26)} path=${r.path} preloader=${r.pl} (期望 ${expect}) seen=${r.seen}`);
  return ok;
}
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  let allOk = true;
  allOk &= await go('/', '① 全新访客进首页', true);
  await sleep(8200);
  const gone = JSON.parse((await send('Runtime.evaluate', { expression: `JSON.stringify({pl:!!document.querySelector('.yisu-preloader')})`, returnByValue: true })).result.value).pl;
  console.log(`      +8.2s 后动画自动收尾 preloader=${gone} ${!gone ? 'PASS' : 'FAIL'}`);
  allOk &= await go('/', '② 再次整页进首页', false);
  allOk &= await (async () => { await send('Runtime.evaluate', { expression: `localStorage.clear()` }); return true; })();
  allOk &= await go('/aiqa', '③ 清记录后直链溯源问答', false);
  allOk &= await go('/', '④ 清记录后再进首页', true);
  console.log(allOk ? '\nALL PASS' : '\nSOME FAILED');
  ws.close(); child.kill(); process.exit(allOk ? 0 : 1);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
