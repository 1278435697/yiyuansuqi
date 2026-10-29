const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const fs = require('fs');
const port = 9335;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  '--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_cdp3',
  '--window-size=1440,1200', 'about:blank',
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
const HOME = 'file:///D:/yisu-ai-platform/frontend/public/accessories/index.html';
const WIDTHS = [1201, 1280, 1360, 1440];
(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  for (const w of WIDTHS) {
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: 1000, deviceScaleFactor: 1, mobile: false });
    await send('Page.navigate', { url: HOME });
    await sleep(3500);
    const r = await send('Runtime.evaluate', {
      expression: `JSON.stringify({vw:innerWidth, sw:document.documentElement.scrollWidth,
        navVisible: getComputedStyle(document.querySelector('.site-nav')).display,
        navOverflow: (()=>{const n=document.querySelector('.site-nav');return n.scrollWidth-n.clientWidth})(),
        burgerVisible: getComputedStyle(document.querySelector('.menu-toggle')).display})`,
      returnByValue: true,
    });
    console.log(r.result.value);
  }
  await send('Emulation.setDeviceMetricsOverride', { width: 420, height: 1400, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: HOME + '#/a/%E5%A4%B4%E9%A5%B0-04' });
  await sleep(6000);
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/acc-v4-detail-mobile.png', Buffer.from(shot.data, 'base64'));
  const m = await send('Runtime.evaluate', {
    expression: 'JSON.stringify({vw:innerWidth,sw:document.documentElement.scrollWidth,off:[...document.querySelectorAll("body *")].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&e.getBoundingClientRect().width>0).slice(0,10).map(e=>e.tagName.toLowerCase()+"."+String(e.className).trim().split(/\\s+/).join(".")+"@"+Math.round(e.getBoundingClientRect().right))})',
    returnByValue: true,
  });
  console.log('detail-mobile', m.result.value);
  ws.close();
  child.kill();
  process.exit(0);
})();
