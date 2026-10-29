// 拖动验收：用真实鼠标/触摸事件（CDP Input.dispatch*Event）驱动悬浮球
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9341;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PROFILE = 'C:/Users/lenovo/AppData/Local/Temp/yisu_drag_' + Date.now();
const child = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=${PROFILE}`,
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
    if (m.method === 'Runtime.exceptionThrown') events.push(m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text);
  });
  return Object.assign((method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }), { events });
}

const BASE = 'http://localhost:5199';
async function rect(send, sel) {
  const r = await send('Runtime.evaluate', {
    expression: `(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return JSON.stringify(null);const b=e.getBoundingClientRect();return JSON.stringify({x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)})})()`,
    returnByValue: true,
  });
  return JSON.parse(r.result.value);
}
// 球带 :hover/.dragging 的 transform，量位置要读未变形的锚点容器
const ballPos = (send) => rect(send, '.ai-float');

async function mouse(send, type, x, y, button = 'none', clickCount = 0) {
  await send('Input.dispatchMouseEvent', { type, x, y, button, clickCount });
}
async function dragTo(send, from, to, steps = 12) {
  await mouse(send, 'mousePressed', from.x, from.y, 'left', 1);
  for (let i = 1; i <= steps; i++) {
    await mouse(send, 'mouseMoved', Math.round(from.x + (to.x - from.x) * i / steps), Math.round(from.y + (to.y - from.y) * i / steps), 'left');
    await sleep(20);
  }
  await mouse(send, 'mouseReleased', to.x, to.y, 'left', 1);
}
async function tap(send, x, y) {
  await mouse(send, 'mousePressed', x, y, 'left', 1);
  await mouse(send, 'mouseReleased', x, y, 'left', 1);
  await sleep(450);
}

// 布局视口要减掉滚动条，断言一律用实时 clientWidth/Height
const layout = (send) => send('Runtime.evaluate', {
  expression: 'JSON.stringify({w:document.documentElement.clientWidth,h:document.documentElement.clientHeight})',
  returnByValue: true,
}).then((r) => JSON.parse(r.result.value));

let pass = 0, fail = 0;
function check(label, ok, detail) {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${detail ? '  ' + detail : ''}`);
  ok ? pass++ : fail++;
}

(async () => {
  const t = await target();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: BASE + '/aiqa' });
  await sleep(3000);

  const b0 = await ballPos(send);
  const L0 = await layout(send);
  check('初始在右下角', b0.x === L0.w - 58 - 24 && b0.y === L0.h - 58 - 24, JSON.stringify(b0) + ' 视口' + JSON.stringify(L0));

  // 1. 拖到左上角 → 吸左边缘，纵向留在手放的高度
  await dragTo(send, { x: b0.x + 29, y: b0.y + 29 }, { x: 60, y: 120 });
  await sleep(400);
  const b1 = await ballPos(send);
  check('吸到左边缘 x=24', b1.x === 24, `x=${b1.x}`);
  check('纵向跟随手指 y≈91', Math.abs(b1.y - (120 - 29)) <= 3, `y=${b1.y}`);
  check('拖完面板没被误点开', (await rect(send, '.af-panel')) === null);

  // 2. 原地单击 → 打开；球在上半屏 → 面板朝下开
  const tipLeft = await send('Runtime.evaluate', { expression: `document.querySelector('.af-ball').classList.contains('tip-right')`, returnByValue: true });
  check('球在左边缘时提示气泡换到右侧', tipLeft.result.value === true);
  await tap(send, b1.x + 29, b1.y + 29);
  const p1 = await rect(send, '.af-panel');
  check('单击打开面板', p1 !== null, JSON.stringify(p1));
  check('球在上半屏→面板朝下开', p1 !== null && p1.y > b1.y, `panel.y=${p1 && p1.y} ball.y=${b1.y}`);
  check('面板不出视口(左侧)', p1 !== null && p1.x >= 0 && p1.x + p1.w <= 1440, `x=${p1 && p1.x} w=${p1 && p1.w}`);
  await tap(send, b1.x + 29, b1.y + 29);
  check('单击收起面板', (await rect(send, '.af-panel')) === null);

  // 3. 拖回右下角 → 面板回到球上方
  const L2 = await layout(send);
  const b2 = await ballPos(send);
  await dragTo(send, { x: b2.x + 29, y: b2.y + 29 }, { x: 1400, y: 830 });
  await sleep(400);
  const b3 = await ballPos(send);
  check('吸到右边缘', b3.x === L2.w - 58 - 24, `x=${b3.x} 期望=${L2.w - 58 - 24}`);
  await tap(send, b3.x + 29, b3.y + 29);
  const p2 = await rect(send, '.af-panel');
  check('球在底部→面板朝上开', p2 !== null && p2.y + p2.h <= b3.y, `panel.bottom=${p2 && p2.y + p2.h} ball.y=${b3.y}`);
  check('面板不出视口(右侧)', p2 !== null && p2.x >= 0 && p2.x + p2.w <= L2.w, `x=${p2 && p2.x} 右=${p2 && p2.x + p2.w} 视口=${L2.w}`);
  await tap(send, b3.x + 29, b3.y + 29);

  // 4. 缩窄视口 → 球被夹回可见区
  await send('Emulation.setDeviceMetricsOverride', { width: 400, height: 700, deviceScaleFactor: 1, mobile: false });
  await sleep(400);
  const b4 = await ballPos(send);
  check('缩窗后球仍在视口内', b4.x >= 0 && b4.x + b4.w <= 400 && b4.y >= 0 && b4.y + b4.h <= 700, JSON.stringify(b4));
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await sleep(300);

  // 5. 触屏拖动：同样吸边，且不滚页
  const b5 = await ballPos(send);
  const scrollBefore = (await send('Runtime.evaluate', { expression: 'window.scrollY', returnByValue: true })).result.value;
  await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: b5.x + 29, y: b5.y + 29 }] });
  for (let i = 1; i <= 10; i++) {
    await send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: Math.round(b5.x + 29 - i * 30), y: Math.round(b5.y + 29 - i * 8) }] });
    await sleep(20);
  }
  await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await sleep(400);
  const b6 = await ballPos(send);
  const scrollAfter = (await send('Runtime.evaluate', { expression: 'window.scrollY', returnByValue: true })).result.value;
  check('触摸拖动同样吸边', b6.x === 24, `x=${b6.x}`);
  check('触摸拖动没滚页', scrollBefore === scrollAfter, `scroll ${scrollBefore}->${scrollAfter}`);

  // 6. 拖出边界被夹住
  await dragTo(send, { x: b6.x + 29, y: b6.y + 29 }, { x: -200, y: -200 });
  await sleep(400);
  const b7 = await ballPos(send);
  check('拖出屏幕被夹住', b7.x >= 12 && b7.y >= 12, JSON.stringify(b7));

  // 7. 松手位置不在球上（没有 click 派发）→ 抑制标记要自己过期，下次单击仍有效
  const b8 = await ballPos(send);
  await dragTo(send, { x: b8.x + 29, y: b8.y + 29 }, { x: 700, y: 450 });
  await sleep(600);
  const b9 = await ballPos(send);
  await tap(send, b9.x + 29, b9.y + 29);
  check('松手在别处后仍能单击开合', (await rect(send, '.af-panel')) !== null, `球 x=${b9.x}`);
  await tap(send, b9.x + 29, b9.y + 29);

  await send('Page.captureScreenshot', { format: 'png' }).then((r) => require('fs').writeFileSync('D:/yisu-ai-platform/.tmp_design/drag-final.png', Buffer.from(r.data, 'base64')));
  if (send.events.length) console.log('\n页面异常: ' + [...new Set(send.events)].join('\n'));
  console.log(`\n${pass} passed, ${fail} failed`);
  ws.close(); child.kill(); process.exit(fail ? 1 : 0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(2); });
