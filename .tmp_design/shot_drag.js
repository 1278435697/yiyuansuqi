// 视觉确认：拖到左中、开面板，截图看方向翻转与气泡
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9342;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_shot_${Date.now()}`,
  '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 60; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find((t) => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); }
(async () => {
  const t = await target(); const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'http://localhost:5199/archive' });
  await sleep(3500);
  const g = async (s) => JSON.parse((await send('Runtime.evaluate', { expression: `(()=>{const e=document.querySelector(${JSON.stringify(s)});const b=e.getBoundingClientRect();return JSON.stringify({x:Math.round(b.x),y:Math.round(b.y)})})()`, returnByValue: true })).result.value);
  const b0 = await g('.ai-float');
  const mv = (type, x, y) => send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseReleased' || type === 'mousePressed' ? 'left' : 'left', clickCount: type === 'mousePressed' ? 1 : 0 });
  await mv('mousePressed', b0.x + 29, b0.y + 29);
  for (let i = 1; i <= 14; i++) { await mv('mouseMoved', Math.round(b0.x + 29 - i * 60), Math.round(b0.y + 29 - i * 18)); await sleep(18); }
  await mv('mouseReleased', 200, 400);
  await sleep(500);
  const b1 = await g('.ai-float');
  await mv('mousePressed', b1.x + 29, b1.y + 29); await mv('mouseReleased', b1.x + 29, b1.y + 29);
  await sleep(700);
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  require('fs').writeFileSync('D:/yisu-ai-platform/.tmp_design/drag-left-open.png', Buffer.from(shot.data, 'base64'));
  console.log('球 =', JSON.stringify(b1), '面板 =', JSON.stringify(await g('.af-panel')));
  ws.close(); child.kill(); process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
