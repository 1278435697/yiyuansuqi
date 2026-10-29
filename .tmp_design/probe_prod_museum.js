const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9337;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const TARGET = process.argv[2] || 'http://47.93.14.11/museum?v=20261018';
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp5',
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
  let id = 0; const pend = new Map(); const events = [];
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); }
    else if (m.method) events.push(m);
  });
  const send = (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); });
  return { send, events };
}
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const { send, events } = cdp(ws);
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Log.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  const reqMap = new Map();
  const bad = [];
  const consoleErrs = [];
  for (const e of events) {
    if (e.method === 'Network.requestWillBeSent') reqMap.set(e.params.requestId, e.params.request.url);
    if (e.method === 'Network.responseReceived') {
      const r = e.params.response;
      if (r.status >= 400) bad.push(`${r.status} ${reqMap.get(e.params.requestId) || r.url}`);
    }
    if (e.method === 'Network.loadingFailed') bad.push(`FAILED ${reqMap.get(e.params.requestId) || '?'} :: ${e.params.errorText}`);
    if (e.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(e.params.type)) {
      consoleErrs.push(e.params.args.map((a) => a.value ?? a.description ?? a.type).join(' ').slice(0, 260));
    }
    if (e.method === 'Runtime.exceptionThrown') {
      const d = e.params.exceptionDetails;
      consoleErrs.push('EXCEPTION: ' + (d.exception?.description || d.text || '').slice(0, 300));
    }
  }
  await send('Page.navigate', { url: TARGET });
  const timeline = [];
  for (let i = 0; i < 15; i++) {
    await sleep(2000);
    const s = await send('Runtime.evaluate', {
      expression: `(()=>{const m=document.querySelector('.loading');const t=m?(m.querySelector('.text')||{textContent:''}).textContent.trim():'';return JSON.stringify({ms:Math.round(performance.now()),mask:!!m,text:t})})()`,
      returnByValue: true,
    });
    const v = JSON.parse(s.result.value);
    timeline.push(`${(v.ms / 1000).toFixed(1)}s mask=${v.mask}${v.mask ? ' "' + v.text + '"' : ''}`);
    if (!v.mask) break;
  }
  await sleep(4000);
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  require('fs').writeFileSync('D:/yisu-ai-platform/.tmp_design/prod-museum-live.png', Buffer.from(shot.data, 'base64'));
  const state = await send('Runtime.evaluate', {
    expression: `JSON.stringify({
      url: location.href,
      mask: (()=>{const m=document.querySelector('.loading');return m?{visible:true,text:(m.querySelector('.text')||{}).textContent||m.textContent.trim().slice(0,60)}:{visible:false}})(),
      canvas: (()=>{const c=document.querySelector('canvas');return c?{w:c.width,h:c.height}:null})(),
      hud: !!document.querySelector('.hud'),
      title: document.title
    })`,
    returnByValue: true,
  });
  console.log('URL   :', TARGET);
  console.log('TIMELINE:');
  timeline.forEach((t) => console.log('   ', t));
  console.log('STATE :', state.result.value);
  console.log('NET x ' + bad.length);
  [...new Set(bad)].slice(0, 25).forEach((b) => console.log('   ', b));
  console.log('CONSOLE x ' + consoleErrs.length);
  [...new Set(consoleErrs)].slice(0, 20).forEach((c) => console.log('   ', c));
  ws.close();
  child.kill();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
