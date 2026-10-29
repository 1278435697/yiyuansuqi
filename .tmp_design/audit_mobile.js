// 全站视觉摸底：逐页真实渲染 + 量化指标 + 整页截图（只读，不改任何东西）
import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = 9352;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = 'D:/yisu-ai-platform/.tmp_design/audit/m';
fs.mkdirSync(OUT, { recursive: true });
const BASE = 'http://47.93.14.11';
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_audit_${Date.now()}`, '--window-size=390,900', 'about:blank'], { stdio: 'ignore' });

async function target() {
  for (let i = 0; i < 60; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find((t) => t.type === 'page'); if (p) return p; } catch {}
    await sleep(250);
  }
  throw new Error('no target');
}
function cdp(ws) {
  let id = 0; const pend = new Map(); const errors = [];
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); }
    if (m.method === 'Runtime.exceptionThrown') errors.push((m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text || '').split('\n')[0]);
  });
  return Object.assign((method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }), { errors });
}
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));
const send = cdp(ws);
await send('Runtime.enable');
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, mobile: true, deviceScaleFactor: 1, deviceScaleFactor: 1, mobile: false });

const PROBE = `(() => {
  const de = document.documentElement, body = document.body;
  const vis = (e) => { const b = e.getBoundingClientRect(); const cs = getComputedStyle(e); return b.width > 2 && b.height > 2 && cs.visibility !== 'hidden' && cs.opacity !== '0'; };
  const txt = (body.innerText || '').replace(/\\s+/g, ' ').trim();
  // 溢出检测：有没有元素横向捅出视口
  let overflow = 0, worst = '';
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const b = e.getBoundingClientRect();
    if (b.right > de.clientWidth + 3 && b.width < de.clientWidth * 1.6) { overflow++; if (!worst) worst = e.tagName + '.' + (e.className || '').toString().slice(0, 40); }
  }
  // 对比度采样：正文里最小的可见字号
  let minFont = 999;
  for (const e of document.querySelectorAll('body *')) {
    if (!e.children.length && e.textContent.trim() && vis(e)) { const f = parseFloat(getComputedStyle(e).fontSize); if (f < minFont) minFont = f; }
  }
  // 主色使用：出现次数最多的非中性色
  const cnt = {};
  for (const e of document.querySelectorAll('body *')) { if (!vis(e)) continue; const c = getComputedStyle(e).color; cnt[c] = (cnt[c] || 0) + 1; }
  const top = Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([c, n]) => c + '×' + n).join(' ');
  return JSON.stringify({
    h: de.scrollHeight, w: de.clientWidth, overflowX: de.scrollWidth > de.clientWidth + 2,
    bleed: overflow, worstBleed: worst,
    chars: txt.length, imgs: document.querySelectorAll('img').length,
    imgsBroken: [...document.querySelectorAll('img')].filter(i => i.complete && i.naturalWidth === 0).length,
    buttons: document.querySelectorAll('button, .el-button, a').length,
    minFont: minFont === 999 ? 0 : minFont, colors: top,
    hasHero: !!document.querySelector('.page-hero, .hero-banner'),
    empties: document.querySelectorAll('.ys-empty, .el-empty').length,
    head: txt.slice(0, 70),
  });
})()`;

const routes = [
  ['home', '/'], ['archive', '/archive'], ['timeline', '/timeline'], ['geomap', '/geomap'],
  ['aiqa', '/aiqa'], ['community', '/community'], ['heritage', '/heritage'], ['fabric', '/fabric'],
  ['pattern', '/pattern'], ['user', '/user'], ['tryon', '/tryon'], ['accessories', '/accessories/index.html'],
  ['museum', '/museum/'],
];
const rows = [];
for (const [name, path] of routes) {
  send.errors.length = 0;
  await send('Page.navigate', { url: BASE + path });
  await sleep(1500);
  for (let i = 0; i < 12; i++) {
    const busy = await send('Runtime.evaluate', { expression: `!!document.querySelector('#yisu-preloader, [class*=preload]')`, returnByValue: true });
    if (!busy.result.value) break;
    await sleep(700);
  }
  await sleep(2500);
  const r = await send('Runtime.evaluate', { expression: PROBE, returnByValue: true });
  const m = JSON.parse(r.result.value);
  m.name = name; m.path = path; m.errs = send.errors.slice(0, 2);
  rows.push(m);
  console.log(`${name.padEnd(12)} 高${String(m.h).padStart(5)} 溢出${m.overflowX ? 'Y' : 'n'}/捅出${String(m.bleed).padStart(3)} 字${String(m.chars).padStart(5)} 图${String(m.imgs).padStart(3)}(坏${m.imgsBroken}) 按钮${String(m.buttons).padStart(3)} 最小字号${m.minFont} 空态${m.empties} hero:${m.hasHero ? 'Y' : 'n'}`);
  if (m.errs.length) console.log('             异常: ' + m.errs.join(' | ').slice(0, 160));
  try {
    const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62, captureBeyondViewport: true });
    fs.writeFileSync(`${OUT}/${name}.jpg`, Buffer.from(s.data, 'base64'));
  } catch (e) { console.log('             截图失败: ' + e.message.slice(0, 80)); }
}
fs.writeFileSync(`${OUT}/metrics.json`, JSON.stringify(rows, null, 1));
console.log('\n指标已存 ' + OUT + '/metrics.json');
ws.close(); child.kill(); process.exit(0);
