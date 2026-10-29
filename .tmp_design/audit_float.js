// 现状取证：悬浮球/面板在各状态与视口下的真实渲染
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const fs = require('child_process');
const { spawn } = require('child_process');
const port = 9345;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = 'D:/yisu-ai-platform/.tmp_design/audit/';
require('fs').mkdirSync(OUT, { recursive: true });
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_audit_${Date.now()}`,
  '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 60; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find((t) => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); }
const shot = async (send, name, clip) => {
  const r = await send('Page.captureScreenshot', { format: 'png', ...(clip ? { clip: { ...clip, scale: 2 } } : {}) });
  require('fs').writeFileSync(OUT + name + '.png', Buffer.from(r.data, 'base64'));
  console.log('saved', name);
};
const size = async (send, w, h, mobile = false) => send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile });
const ev = async (send, expression) => (await send('Runtime.evaluate', { expression, returnByValue: true })).result.value;

(async () => {
  const t = await target(); const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');

  // 首页：球静止 + hover 气泡
  await size(send, 1440, 900);
  await send('Page.navigate', { url: 'http://localhost:5199/' });
  await sleep(9000);
  await shot(send, '01-home-ball', { x: 1180, y: 640, width: 260, height: 260 });
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 1377, y: 847 });
  await sleep(400);
  await shot(send, '02-home-ball-hover', { x: 1000, y: 640, width: 440, height: 260 });

  // 面板：空态（快捷问题）
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 1377, y: 847, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 1377, y: 847, button: 'left', clickCount: 1 });
  await sleep(700);
  await shot(send, '03-panel-empty');
  await shot(send, '03-panel-empty-crop', { x: 960, y: 250, width: 480, height: 650 });

  // 发一条消息（后端没起 → 失败态），再补几条本地消息看排版
  await ev(send, `(()=>{const i=document.querySelector('.af-input input');const s=document.querySelector('.af-send');const set=(v)=>{const d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;d.call(i,v);i.dispatchEvent(new Event('input',{bubbles:true}))};return 'ok'})()`);
  await ev(send, `(async()=>{const rows=document.querySelector('.af-msgs');const add=(role,txt,ref)=>{const d=document.createElement('div');d.className='af-row '+role;d.innerHTML='<div class="af-bubble"><p>'+txt+'</p>'+(ref?'<span class="af-ref">引用：'+ref+'</span>':'')+'</div>';rows.appendChild(d)};add('user','曲裾深衣属于哪个朝代？');add('assistant','曲裾深衣主要流行于<b>汉代</b>，以战国楚地为源头。其衣襟层层盘绕、接裾三角衽交叠，是深衣制在汉代的典型演化。', '《马王堆一号汉墓》· 曲裾素纱襌衣');add('user','它和直裾有什么区别？');add('assistant','区别在下摆与衣襟：曲裾的裾边呈斜角、需绕襟数圈方能掩合；直裾则衣襟垂直而下，无需绕襟，穿脱更省事，东汉后逐渐取代曲裾成为常服。','');rows.scrollTop=rows.scrollHeight;return 'done'})()`);
  await sleep(500);
  await shot(send, '04-panel-chat-crop', { x: 960, y: 180, width: 480, height: 720 });

  // 输入框聚焦态
  await ev(send, `document.querySelector('.af-input input').focus()`);
  await sleep(300);
  await shot(send, '05-panel-focus-crop', { x: 960, y: 620, width: 480, height: 280 });

  // 手机视口
  await size(send, 390, 780, true);
  await sleep(600);
  await shot(send, '06-mobile-open');
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 350, y: 720, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 350, y: 720, button: 'left', clickCount: 1 });
  await sleep(600);
  await shot(send, '07-mobile-closed');
  await size(send, 1440, 900); await sleep(400);
  await send('Page.reload'); await sleep(9000);
  await shot(send, '08-home-full');
  ws.close(); child.kill(); process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
