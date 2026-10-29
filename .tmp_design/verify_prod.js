// 生产验收：真实浏览器打 http://47.93.14.11/ ，验证本轮上线的三件事
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
import { spawn } from 'child_process';
import fs from 'fs';
const port = 9347;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PROFILE = 'C:/Users/lenovo/AppData/Local/Temp/yisu_prod_' + Date.now();
const BASE = 'http://47.93.14.11';
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

async function evalJs(send, expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text);
  return r.result.value;
}
async function rect(send, sel) {
  const r = await evalJs(send, `(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return JSON.stringify(null);const b=e.getBoundingClientRect();return JSON.stringify({x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)})})()`);
  return JSON.parse(r);
}
const ballPos = (send) => rect(send, '.ai-float');
async function mouse(send, type, x, y, button = 'none', clickCount = 0) {
  await send('Input.dispatchMouseEvent', { type, x, y, button, clickCount });
}
async function dragTo(send, from, to, steps = 12) {
  await mouse(send, 'mousePressed', from.x, from.y, 'left', 1);
  for (let i = 1; i <= steps; i++) {
    await mouse(send, 'mouseMoved', Math.round(from.x + (to.x - from.x) * i / steps), Math.round(from.y + (to.y - from.y) * i / steps), 'left');
    await sleep(25);
  }
  await mouse(send, 'mouseReleased', to.x, to.y, 'left', 1);
  await sleep(350);
}
async function tap(send, x, y) {
  await mouse(send, 'mousePressed', x, y, 'left', 1);
  await mouse(send, 'mouseReleased', x, y, 'left', 1);
  await sleep(500);
}

const results = [];
function check(name, ok, detail = '') {
  results.push({ name, ok, detail });
  console.log((ok ? 'PASS' : 'FAIL') + ' ' + name + (detail ? '  ' + detail : ''));
}

const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));
const send = cdp(ws);
await send('Runtime.enable');
await send('Page.enable');

// ---- 主站 ----
await send('Page.navigate', { url: BASE + '/' });
await sleep(1200);
// 首访会播开场动画，等它结束（动画只在首次进入播放）
for (let i = 0; i < 30; i++) {
  const busy = await evalJs(send, `!!document.querySelector('#yisu-preloader, .preloader, [class*=preload]')`);
  if (!busy) break;
  await sleep(700);
}
await sleep(1500);

const layout = await evalJs(send, `JSON.stringify({w:document.documentElement.clientWidth,h:document.documentElement.clientHeight})`).then((s) => JSON.parse(s));
console.log('视口', JSON.stringify(layout));

const b0 = await ballPos(send);
check('悬浮球已挂载', !!b0, JSON.stringify(b0));
check('默认贴右下角', b0 && Math.abs(b0.x + b0.w - (layout.w - 24)) <= 2 && Math.abs(b0.y + b0.h - (layout.h - 24)) <= 2, JSON.stringify(b0));

// 拖动 → 吸左边缘
await dragTo(send, { x: b0.x + 29, y: b0.y + 29 }, { x: Math.round(layout.w * 0.42), y: Math.round(layout.h * 0.42) });
const b1 = await ballPos(send);
check('拖动后吸到左边缘 x=24', b1 && b1.x === 24, JSON.stringify(b1));
check('纵向跟随手指不放回底部', b1 && b1.y < layout.h - 200, JSON.stringify(b1));
check('拖完面板没被误点开', (await rect(send, '.af-panel')) === null);

// 面板
const ball2 = await ballPos(send);
await tap(send, ball2.x + 29, ball2.y + 29);
const p0 = await rect(send, '.af-panel');
check('单击打开面板', !!p0, JSON.stringify(p0));
if (p0) {
  const ph = await evalJs(send, `Math.round(document.querySelector('.af-panel').getBoundingClientRect().height)`);
  check('面板固定高度 520', ph === 520, 'h=' + ph);
  const dia = await evalJs(send, `(()=>{const cs=getComputedStyle(document.querySelector('.af-panel'),'::after');return JSON.stringify({c:cs.content,w:cs.width,bg:cs.backgroundColor})})()`).then((s) => JSON.parse(s));
  check('指向球的小三角在', dia.c !== 'none' && dia.w === '12px', JSON.stringify(dia));
  check('球在上半屏时面板朝下开', p0.y > ball2.y, JSON.stringify({ ball: ball2.y, panel: p0.y }));
  check('面板不出视口', p0.x >= 0 && p0.x + p0.w <= layout.w + 1 && p0.y + p0.h <= layout.h + 1, JSON.stringify(p0));
}
await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
await sleep(500);
check('Esc 收起面板', (await rect(send, '.af-panel')) === null);

// 导航改名（主站）
const nav = await evalJs(send, `[...document.querySelectorAll('a[href*="accessories"]')].map(a=>a.textContent.trim()).join('|')`);
check('主站导航显示「衣冠」', /衣冠/.test(nav) && !/配饰/.test(nav), nav || '(没找到该链接)');

// 拖回右下角，留个正常收尾状态
const ball3 = await ballPos(send);
await dragTo(send, { x: ball3.x + 29, y: ball3.y + 29 }, { x: layout.w - 40, y: layout.h - 40 });
const b4 = await ballPos(send);
check('能吸回右边缘', b4 && b4.x + b4.w === layout.w - 24, JSON.stringify(b4));

const shot = await send('Page.captureScreenshot', { format: 'png' });
fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/audit/prod-home.png', Buffer.from(shot.data, 'base64'));

// ---- 配饰子页 ----
await send('Page.navigate', { url: BASE + '/accessories/index.html' });
await sleep(3500);
const acc = await evalJs(send, `(()=>{const n=[...document.querySelectorAll('a,nav *,header *')].filter(e=>e.children.length===0).map(e=>e.textContent.trim());return JSON.stringify({title:document.title,hasYG:n.includes('衣冠'),hasPei:n.includes('配饰'),body:document.body.innerText.slice(0,60)})})()`).then((s) => JSON.parse(s));
check('配饰子页导航是「衣冠」', acc.hasYG === true, JSON.stringify(acc));
const accStatus = await evalJs(send, `document.querySelectorAll('img').length`);
check('配饰子页有图渲染', accStatus > 0, 'img=' + accStatus);
const shot2 = await send('Page.captureScreenshot', { format: 'png' });
fs.writeFileSync('D:/yisu-ai-platform/.tmp_design/audit/prod-accessories.png', Buffer.from(shot2.data, 'base64'));

// ---- 3D 博物馆子站仍可用（仓外独有文件，本轮必须没被碰）----
const museum = await evalJs(send, `(async()=>{const r=await fetch('/museum/',{cache:'no-store'});const txt=await r.text();return JSON.stringify({status:r.status,len:txt.length,hit:/<html|<!DOCTYPE/i.test(txt)})})()`).then((s) => JSON.parse(s));
check('/museum/ 仍可访问', museum.status === 200 && museum.hit, JSON.stringify(museum));

// ---- 老入口 chunk 是否还在（别把线上正在用的文件删了）----
const oldChunks = await evalJs(send, `(async()=>{const out=[];for(const u of ['/assets/index-Bb6yjXMn.js','/assets/index-BGkBFnU0.js']){try{out.push(u+'='+(await (await fetch(u,{cache:'no-store'})).status))}catch(e){out.push(u+'=ERR')}}return out.join(' ')})()`);
console.log('新旧入口 chunk 状态:', oldChunks);

const errs = send.events.filter((e) => !/Network Error|ERR_FAILED|AxiosError/i.test(e));
check('页面运行无异常', errs.length === 0, errs.slice(0, 3).join(' | ').slice(0, 300));

console.log('\n汇总: ' + results.filter((r) => r.ok).length + ' passed, ' + results.filter((r) => !r.ok).length + ' failed');
ws.close(); child.kill();
process.exit(results.some((r) => !r.ok) ? 1 : 0);
