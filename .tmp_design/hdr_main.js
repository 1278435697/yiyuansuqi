// 只量主站顶栏（含未登录时的「登录」按钮），等 header 真的渲染出来再取 computed style
const { spawn } = require('child_process');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const PORT = Number(process.argv[2] || 9783);
const URL_ = process.argv[3] || 'http://47.93.14.11/';
const PROFILE = `C:\\Users\\lenovo\\AppData\\Local\\Temp\\hdrmain${PORT}`;

const EXPR = `(() => {
  const bg = (s) => (s || '').replace(/\\s+/g, ' ');
  const hdr = document.querySelector('.app-header');
  const hc = getComputedStyle(hdr);
  const seal = hdr.querySelector('.brand-seal');
  const sc = getComputedStyle(seal);
  const h1 = hdr.querySelector('.brand-text h1');
  const p = hdr.querySelector('.brand-text p');
  const nav = hdr.querySelector('.app-nav');
  const link = nav.querySelector('a');
  const btn = hdr.querySelector('.header-right button, .header-right .user-chip');
  const bc = getComputedStyle(btn);
  const box = (el) => { const r = el.getBoundingClientRect(); return Math.round(r.width) + 'x' + Math.round(r.height); };
  return {
    头部: { 尺寸: box(hdr), position: hc.position, 内边距: hc.padding, gap: hc.gap,
      背景图: bg(hc.backgroundImage), 背景色: hc.backgroundColor, backdrop: hc.backdropFilter,
      下边框: hc.borderBottomWidth + ' ' + hc.borderBottomColor, 阴影: bg(hc.boxShadow) },
    品牌: { gap: getComputedStyle(hdr.querySelector('.brand')).gap },
    章: { 尺寸: box(seal), 圆角: sc.borderRadius, 边框: sc.borderTopWidth + ' ' + sc.borderTopColor,
      背景图: bg(sc.backgroundImage), 背景色: sc.backgroundColor, 字色: sc.color, 字号: sc.fontSize,
      字族: sc.fontFamily, 字重: sc.fontWeight, 字距: sc.letterSpacing, 阴影: bg(sc.boxShadow) },
    标题: { 字号: getComputedStyle(h1).fontSize, 字重: getComputedStyle(h1).fontWeight,
      字距: getComputedStyle(h1).letterSpacing, 字色: getComputedStyle(h1).color,
      行高: getComputedStyle(h1).lineHeight, 外边距: getComputedStyle(h1).margin },
    副标: { 字号: getComputedStyle(p).fontSize, 字距: getComputedStyle(p).letterSpacing,
      字色: getComputedStyle(p).color, 行高: getComputedStyle(p).lineHeight, 外边距: getComputedStyle(p).margin },
    导航: { gap: getComputedStyle(nav).gap, flex: getComputedStyle(nav).flexGrow,
      链接: { 尺寸: box(link), 内边距: getComputedStyle(link).padding, 字号: getComputedStyle(link).fontSize,
        字族: getComputedStyle(link).fontFamily, 字距: getComputedStyle(link).letterSpacing,
        字色: getComputedStyle(link).color, 圆角: getComputedStyle(link).borderRadius } },
    右侧: { 文本: btn.textContent.trim().slice(0, 8), 类: btn.className, 尺寸: box(btn),
      内边距: bc.padding, 边框: bc.borderTopWidth + ' ' + bc.borderTopColor, 圆角: bc.borderRadius,
      背景图: bg(bc.backgroundImage), 背景色: bc.backgroundColor, 字色: bc.color, 字号: bc.fontSize,
      字重: bc.fontWeight, 字距: bc.letterSpacing },
  };
})()`;

async function main() {
  const chrome = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const proc = spawn(chrome, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
    '--no-first-run', '--disable-gpu', '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
  await sleep(2500);
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const ws = new WebSocket(list.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r));
  let id = 0;
  const pend = new Map();
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
  });
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const evl = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 400));
    return r.result?.result?.value;
  };
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL_ });
  for (let i = 0; i < 40; i++) {
    await sleep(750);
    const ok = await evl(`!!document.querySelector('.app-header .brand-seal')`);
    if (ok) break;
  }
  await sleep(1500);
  console.log(JSON.stringify(await evl(EXPR), null, 1));
  ws.close();
  proc.kill();
  process.exit(0);
}
main().catch((e) => { console.error(e); process.exit(1); });
