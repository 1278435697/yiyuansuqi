// 设计优化验收：稳定高度 / 无空白带 / tip 不压面板 / Esc / 自动聚焦 / 重试 / 指向三角 / 两列胶囊
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9347;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_des_${Date.now()}`,
  '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 60; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find((t) => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); const errs = []; ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } if (m.method === 'Runtime.exceptionThrown') errs.push(m.params.exceptionDetails?.exception?.description || ''); }); return Object.assign((method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }), { errs }); }
const E = (send, expression) => send('Runtime.evaluate', { expression, returnByValue: true }).then((r) => r.result.value);
let pass = 0, fail = 0;
function check(label, ok, detail) { console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${detail !== undefined ? '  ' + detail : ''}`); ok ? pass++ : fail++; }

(async () => {
  const t = await target(); const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'http://localhost:5199/' });
  await sleep(9000);

  const ball = () => E(send, `(()=>{const b=document.querySelector('.ai-float').getBoundingClientRect();return JSON.stringify({x:Math.round(b.x),y:Math.round(b.y)})})()`).then(JSON.parse);
  const tap = async (x, y) => { await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 }); await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }); await sleep(600); };
  const sendQ = async (q) => { await E(send, `(()=>{const i=document.querySelector('.af-input input');const d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;d.call(i,${JSON.stringify(q)});i.dispatchEvent(new Event('input',{bubbles:true}))})()`); await sleep(120); await E(send, `document.querySelector('.af-send').click()`); await sleep(2200); };

  // A. 空态
  let b = await ball();
  await tap(b.x + 29, b.y + 29);
  const geo = await E(send, `(()=>{const q=(s)=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),h:Math.round(r.height),sh:e.scrollHeight,ov:getComputedStyle(e).overflowY}},P=document.querySelector('.af-panel');return JSON.stringify({panel:q('.af-panel'),head:q('.af-head'),msgs:q('.af-msgs'),input:q('.af-input'),welcome:!!document.querySelector('.af-msgs .af-welcome'),cols:getComputedStyle(document.querySelector('.af-chips')).gridTemplateColumns.split(' ').length,panelOf:getComputedStyle(P).overflow,after:getComputedStyle(P,'::after').content,afterBg:getComputedStyle(P,'::after').backgroundColor})})()`);
  const G = JSON.parse(geo);
  check('面板固定 520 高', G.panel.h === 520, `h=${G.panel.h}`);
  check('引导块在滚动区内（无独立空白带）', G.welcome && G.msgs.h + G.head.h + G.input.h + 2 === G.panel.h, `msgs=${G.msgs.h}+head=${G.head.h}+input=${G.input.h}+边框2=${G.panel.h}`);
  check('空态不产生多余滚动', G.msgs.sh <= G.msgs.h + 1, `sh=${G.msgs.sh} h=${G.msgs.h}`);
  check('快捷问题两列', G.cols === 2, `cols=${G.cols}`);
  check('输入行够高可点', G.input.h >= 52, `input=${G.input.h}`);
  check('指向三角存在且未被裁掉', G.after !== 'none' && G.panelOf === 'visible', `after=${G.after} overflow=${G.panelOf}`);
  check('三角朝球（浅色面板底）', G.afterBg === 'rgb(255, 253, 248)', G.afterBg);

  // B. 开面板时气泡不再压上来
  await E(send, `document.querySelector('.af-ball').dispatchEvent(new MouseEvent('mouseover',{bubbles:true}))`);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: b.x + 29, y: b.y + 29 });
  await sleep(400);
  const tipOp = await E(send, `getComputedStyle(document.querySelector('.af-ball-tip')).opacity`);
  check('面板打开时悬停球不再弹气泡', tipOp === '0', `opacity=${tipOp}`);

  // C. 自动聚焦 + aria
  const focused = await E(send, `document.activeElement.tagName + '.' + document.activeElement.className`);
  check('打开后自动聚焦输入框', focused.startsWith('INPUT'), focused);
  check('打开后面板 aria-expanded=true', (await E(send, `document.querySelector('.af-ball').getAttribute('aria-expanded')`)) === 'true');
  check('role=dialog', (await E(send, `document.querySelector('.af-panel').getAttribute('role')`)) === 'dialog');

  // D. 发一轮：高度必须不变
  await sendQ('曲裾深衣属于哪个朝代？');
  const g2 = JSON.parse(await E(send, `(()=>{const p=document.querySelector('.af-panel');const m=document.querySelector('.af-msgs');const r=p.getBoundingClientRect();return JSON.stringify({h:Math.round(r.height),rows:document.querySelectorAll('.af-row').length,welcome:!!document.querySelector('.af-welcome'),msgsH:m.offsetHeight,msgsSh:m.scrollHeight,retry:!!document.querySelector('.af-retry')})})()`));
  check('对话后面板高度仍是 520（不跳）', g2.h === 520, `h=${g2.h}`);
  check('引导块让位给对话', g2.rows === 2 && !g2.welcome, `rows=${g2.rows}`);
  check('聊天区拿到整块空间', g2.msgsH > 380, `msgs=${g2.msgsH}`);
  check('失败气泡带重试', g2.retry === true);
  await send('Page.captureScreenshot', { format: 'png' }).then((r) => require('fs').writeFileSync('D:/yisu-ai-platform/.tmp_design/audit/d-1440-chat.png', Buffer.from(r.data, 'base64')));

  // E. 重试真的重发
  await E(send, `document.querySelector('.af-retry').click()`);
  await sleep(2400);
  const g3 = JSON.parse(await E(send, `JSON.stringify({rows:document.querySelectorAll('.af-row').length,retry:!!document.querySelector('.af-retry')})`));
  check('点重试＝重发同一条，不重复提问', g3.rows === 2 && g3.retry, `rows=${g3.rows}`);

  // F. Esc 关闭并把焦点还给球
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await sleep(500);
  const closed = await E(send, `JSON.stringify({panel:!!document.querySelector('.af-panel'),act:document.activeElement.className,exp:document.querySelector('.af-ball').getAttribute('aria-expanded')})`);
  const C = JSON.parse(closed);
  check('Esc 关闭面板', C.panel === false && C.exp === 'false', closed);
  check('关闭后焦点回到球', /af-ball/.test(C.act), C.act);

  // G. 球拖到顶部 → 面板朝下开 + 三角翻到顶部（深色头）
  b = await ball();
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: b.x + 29, y: b.y + 29, button: 'left', clickCount: 1 });
  for (let i = 1; i <= 12; i++) { await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: Math.round(b.x + 29 - i * 100), y: Math.round(b.y + 29 - i * 60), button: 'left' }); await sleep(18); }
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 200, y: 100, button: 'left', clickCount: 1 });
  await sleep(500);
  b = await ball();
  await tap(b.x + 29, b.y + 29);
  const g4 = JSON.parse(await E(send, `(()=>{const p=document.querySelector('.af-panel');const m=document.querySelector('.af-msgs');const r=p.getBoundingClientRect();return JSON.stringify({y:Math.round(r.y),h:Math.round(r.height),down:p.classList.contains('is-down'),left:p.classList.contains('is-side-left'),after:getComputedStyle(p,'::after').backgroundColor,scrollable:m.scrollHeight>m.offsetHeight})})()`));
  check('球在上半屏→面板朝下开', g4.down && g4.y > b.y, `panel.y=${g4.y} ball.y=${b.y}`);
  check('朝下时三角贴深红头部', g4.after === 'rgb(126, 36, 24)', g4.after);
  check('吸左后面板左对齐 + 三角换侧', g4.left === true, JSON.stringify(g4));
  check('顶部时高度按剩余空间收缩', g4.h <= 900 - b.y - 58 - 12 + 1, `h=${g4.h}`);
  await send('Page.captureScreenshot', { format: 'png' }).then((r) => require('fs').writeFileSync('D:/yisu-ai-platform/.tmp_design/audit/d-top-open.png', Buffer.from(r.data, 'base64')));

  // H. 手机视口（重载拿回空态）
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 780, deviceScaleFactor: 1, mobile: false });
  await send('Page.reload');
  await sleep(9000);
  b = await ball();
  await tap(b.x + 29, b.y + 29);
  const g5 = JSON.parse(await E(send, `(()=>{const p=document.querySelector('.af-panel');const bb=document.querySelector('.ai-float').getBoundingClientRect();return JSON.stringify({pw:Math.round(p.getBoundingClientRect().width),ph:Math.round(p.getBoundingClientRect().height),cols:getComputedStyle(document.querySelector('.af-chips')).gridTemplateColumns.split(' ').length,ballX:Math.round(bb.x),ballY:Math.round(bb.y)})})()`));
  check('手机上胶囊单列', g5.cols === 1, `cols=${g5.cols}`);
  check('手机上面板不越界', g5.pw <= 380 - 24 && g5.ballX + 58 <= 380 && g5.ph <= Math.round(780 * 0.62), JSON.stringify(g5));
  await send('Page.captureScreenshot', { format: 'png' }).then((r) => require('fs').writeFileSync('D:/yisu-ai-platform/.tmp_design/audit/d-mobile.png', Buffer.from(r.data, 'base64')));

  console.log(`\n${pass} passed, ${fail} failed`);
  if (send.errs.length) console.log('页面异常:\n' + [...new Set(send.errs)].join('\n').slice(0, 400));
  ws.close(); child.kill(); process.exit(fail ? 1 : 0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
