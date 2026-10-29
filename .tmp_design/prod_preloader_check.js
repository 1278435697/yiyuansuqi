const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9347;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp_prod_first',
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
const BASE = 'http://47.93.14.11';
const PROBE = `JSON.stringify({pl: !!document.querySelector('.yisu-preloader'), seen: localStorage.getItem('yisu-preloader-seen'), path: location.pathname})`;
let send;
async function go(path, label, expect) {
  await send('Page.navigate', { url: BASE + path });
  await sleep(2600);
  const r = JSON.parse((await send('Runtime.evaluate', { expression: PROBE, returnByValue: true })).result.value);
  const ok = r.pl === expect;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label.padEnd(24)} path=${r.path} preloader=${r.pl} (期望 ${expect}) seen=${r.seen}`);
  return ok;
}
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  send = cdp(ws);
  await send('Page.enable'); await send('Network.enable');
  const errs = []; const fails = [];
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.method === 'Runtime.exceptionThrown') errs.push(((m.params.exceptionDetails.exception || {}).description || '').split('\n')[0]);
    if (m.method === 'Network.loadingFailed') fails.push(m.params.errorText);
  });
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  let allOk = true;
  allOk &= await go('/', '① 首次进首页', true);
  await sleep(9000);
  const gone = JSON.parse((await send('Runtime.evaluate', { expression: `JSON.stringify({pl:!!document.querySelector('.yisu-preloader')})`, returnByValue: true })).result.value).pl;
  console.log(`      +9s 动画自行收尾 preloader=${gone} ${!gone ? 'PASS' : 'FAIL'}`);
  allOk &= await go('/', '② 再次整页进首页', false);
  await send('Runtime.evaluate', { expression: `localStorage.clear()` });
  allOk &= await go('/aiqa', '③ 清记录后进溯源问答', false);
  allOk &= await go('/', '④ 清记录后再进首页', true);
  await sleep(9000);
  allOk &= await go('/archive', '⑤ 站内跳档案页', false);
  console.log('JS异常:', errs.length ? errs.slice(0, 3) : '0 条');
  console.log('网络失败:', fails.length ? fails.slice(0, 3) : '0 条');
  console.log(allOk ? '\nALL PASS' : '\nSOME FAILED');
  ws.close(); child.kill(); process.exit(allOk ? 0 : 1);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
