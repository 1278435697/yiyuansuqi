// 地基体检：任意 base + 桌面/手机两视口，输出可断言的硬指标。
// 用法: node health.js <baseUrl> <outDir>
import { spawn } from 'child_process';
import fs from 'fs';
const BASE = process.argv[2] || 'http://localhost:5173';
const OUT = process.argv[3] || 'D:/yisu-ai-platform/.tmp_design/audit/h_before';
fs.mkdirSync(OUT, { recursive: true });
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = 9360 + Number(process.argv[4] || 0);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_h_${Date.now()}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });

async function target() {
  for (let i = 0; i < 200; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find((t) => t.type === 'page'); if (p) return p; } catch {}
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
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));
const send = cdp(ws);
await send('Runtime.enable'); await send('Page.enable');

const PROBE = `(() => {
  const de = document.documentElement;
  const VW = de.clientWidth;
  const BLUE = ['rgb(64, 158, 255)','rgb(121, 187, 255)','rgb(160, 207, 255)','rgb(198, 226, 255)','rgb(217, 236, 255)','rgb(236, 245, 255)','rgb(51, 126, 204)'];
  const path = (e) => { const p = []; let c = e; for (let i = 0; i < 4 && c && c.tagName; i++) { p.unshift(c.tagName.toLowerCase() + (c.className && typeof c.className === 'string' ? '.' + c.className.trim().split(/\\s+/).slice(0,2).join('.') : '')); c = c.parentElement; } return p.join('>'); };
  const vis = (e) => { const b = e.getBoundingClientRect(); const cs = getComputedStyle(e); return b.width > 2 && b.height > 2 && cs.visibility !== 'hidden' && cs.opacity !== '0'; };
  let bleed = [], masked = [], blue = [], small = [], touch = [], touchCtrl = [];
  // 溢出分三类：真捅出页面 / 被祖先 overflow-x hidden 藏起来 / 在可横滚容器内（设计如此，不算缺陷）
  const scrollCtx = (e) => {
    let c = e.parentElement;
    while (c && c !== document.body) {
      const ox = getComputedStyle(c).overflowX;
      if (ox === 'auto' || ox === 'scroll') return 'scroller';
      if (ox === 'hidden' || ox === 'clip') return 'masked';
      c = c.parentElement;
    }
    return 'page';
  };
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const cs = getComputedStyle(e);
    const b = e.getBoundingClientRect();
    if (b.right > VW + 3 && b.width < VW * 1.6 && e.getAttribute('aria-hidden') !== 'true' && !/leaflet/.test(e.className.toString())) {
      const ctx = scrollCtx(e);
      if (ctx === 'page') bleed.push({ p: path(e), over: Math.round(b.right - VW) });
      else if (ctx === 'masked') masked.push({ p: path(e), over: Math.round(b.right - VW) });
    }
    for (const prop of ['color','background-color','border-top-color','border-bottom-color','border-left-color','outline-color','fill']) {
      if (BLUE.includes(cs[prop])) { blue.push({ p: path(e), prop, v: cs[prop] }); break; }
    }
    if (!e.children.length && e.textContent.trim()) { const f = parseFloat(cs.fontSize); if (f < 12) small.push({ p: path(e), f, txt: e.textContent.trim().slice(0, 18) }); }
    const vw = window.innerWidth;
    if (vw <= 768 && (e.matches('button, a, .el-button, .el-tabs__item, .el-segmented__item, input, select'))) {
      const undersized = b.height < 44 - 1 || b.width < 44 - 1;
      if (undersized) touch.push({ p: path(e), w: Math.round(b.width), h: Math.round(b.height) });
      // 只算真控件（行内文字链接按 WCAG 2.5.8 豁免），这一列是「必须达标」的口径。
      // 控件内部的 input 不算独立目标：只要它包着的 wrapper 够高，可点区域就是够的。
      const wrap = e.closest('.el-select__wrapper, .el-input__wrapper, .el-textarea');
      const wrappedOk = wrap && wrap.getBoundingClientRect().height >= 44 - 1;
      if (undersized && !wrappedOk && e.matches('button, .el-button, .el-tabs__item, .el-radio-button__inner, .el-pager li, .el-segmented__item, input, select, .app-nav a'))
        touchCtrl.push({ p: path(e), w: Math.round(b.width), h: Math.round(b.height) });
    }
  }
  const bodyOX = getComputedStyle(document.body).overflowX;
  const htmlOX = getComputedStyle(de).overflowX;
  return JSON.stringify({
    vw: VW, pageH: de.scrollHeight,
    hScroll: de.scrollWidth > VW + 2,
    bleed: bleed.length, bleedTop: bleed.sort((a,b)=>b.over-a.over).slice(0,4),
    masked: masked.length, maskedTop: masked.sort((a,b)=>b.over-a.over).slice(0,3),
    blue: blue.length, blueTop: blue.slice(0,4),
    small: small.length, smallTop: small.slice(0,4),
    touch: touch.length, touchTop: touch.slice(0,4),
    touchCtrl: touchCtrl.length, touchCtrlTop: touchCtrl.slice(0,4),
    overflowXGuard: 'body:' + bodyOX + ' html:' + htmlOX,
    emptyKinds: [...new Set([...document.querySelectorAll('[class*=empty]')].map(e=>e.className.toString().split(/\\s+/)[0]))].join(','),
  });
})()`;

const routes = [['home','/'],['archive','/archive'],['timeline','/timeline'],['geomap','/geomap'],['aiqa','/aiqa'],['community','/community'],['heritage','/heritage'],['fabric','/fabric'],['pattern','/pattern'],['user','/user'],['tryon','/tryon'],['accessories','/accessories/index.html']];
const viewports = [['d', 1440, 900], ['m', 390, 844]];
const rows = [];
for (const [vk, w, h] of viewports) {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: vk === 'm' });
  for (const [name, path] of routes) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(1200);
    for (let i = 0; i < 10; i++) {
      const busy = await send('Runtime.evaluate', { expression: `!!document.querySelector('#yisu-preloader, [class*=preload]')`, returnByValue: true });
      if (!busy.result.value) break;
      await sleep(700);
    }
    await sleep(2600);
    const r = JSON.parse((await send('Runtime.evaluate', { expression: PROBE, returnByValue: true })).result.value);
    r.name = name; r.vk = vk;
    rows.push(r);
    console.log(`${vk} ${name.padEnd(12)} 真捅出${String(r.bleed).padStart(3)} 藏起${String(r.masked).padStart(4)} 横滚${r.hScroll ? 'Y' : 'n'} 蓝${String(r.blue).padStart(3)} 小字${String(r.small).padStart(4)} 触控${String(r.touch).padStart(3)} 页高${String(r.pageH).padStart(6)}  ${r.overflowXGuard}${r.emptyKinds ? '  空态[' + r.emptyKinds + ']' : ''}`);
    if (r.bleedTop.length) console.log('     真捅出: ' + r.bleedTop.map((x) => x.p + '(+' + x.over + ')').join('  '));
    if (r.maskedTop.length) console.log('     被藏:   ' + r.maskedTop.map((x) => x.p + '(+' + x.over + ')').join('  '));
    if (r.blueTop.length) console.log('     蓝:   ' + r.blueTop.map((x) => x.p + ' ' + x.prop).join('  '));
  }
}
fs.writeFileSync(`${OUT}/health.json`, JSON.stringify(rows, null, 1));
const sum = (k) => rows.reduce((a, r) => a + r[k], 0);
console.log(`\n== ${BASE} 合计 ==`);
console.log(`真捅出 ${sum('bleed')}  被 overflow 藏起 ${sum('masked')}  整页横滚 ${rows.filter(r=>r.hScroll).length} 页  Element蓝 ${sum('blue')}  字号<12px ${sum('small')}  交互件未达标 ${sum('touch')}  其中真控件 ${sum('touchCtrl')}`);
const tc=rows.filter(r=>r.touchCtrlTop&&r.touchCtrlTop.length);
if(tc.length){console.log('真控件未达标明细:');for(const r of tc)console.log('  '+r.vk+' '+r.name.padEnd(11)+' '+r.touchCtrlTop.map(x=>x.p.split('>').pop()+' '+x.w+'x'+x.h).join('  '));}
ws.close(); child.kill(); process.exit(0);
