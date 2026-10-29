// 量一个顶栏（主站 .app-header 或衣冠 .site-header），输出同一套字段便于逐项对比
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const PORT = Number(process.argv[2]);
const URL_ = process.argv[3];
const OUT = process.argv[4];
const W = Number(process.argv[5] || 1440);
const H = Number(process.argv[6] || 900);

const EXPR = `(() => {
  const bg = (s) => (s || '').replace(/\\s+/g, ' ');
  const hdr = document.querySelector('.app-header, .site-header');
  if (!hdr) return 'NO HEADER';
  const hc = getComputedStyle(hdr);
  const inner = hdr.querySelector('.brand') ? hdr : hdr.querySelector('.header-inner');
  const ic = getComputedStyle(inner);
  const brand = hdr.querySelector('.brand');
  const seal = hdr.querySelector('.brand-seal');
  const sc = getComputedStyle(seal);
  const t = hdr.querySelector('.brand-text h1, .brand-copy strong');
  const p = hdr.querySelector('.brand-text p, .brand-copy small');
  const nav = hdr.querySelector('.app-nav, .site-nav');
  const link = nav.querySelector('a');
  const btn = hdr.querySelector('.header-right button, .header-right .user-chip, .login-link');
  const bc = getComputedStyle(btn);
  const box = (el) => { const r = el.getBoundingClientRect(); return Math.round(r.width) + 'x' + Math.round(r.height) + ' @' + Math.round(r.left) + ',' + Math.round(r.top); };
  return {
    头部: { 尺寸: box(hdr), 内边距: ic.padding, gap: ic.gap, 背景图: bg(hc.backgroundImage),
      背景色: hc.backgroundColor, backdrop: hc.backdropFilter,
      下边框: hc.borderBottomWidth + ' ' + hc.borderBottomColor, 阴影: bg(hc.boxShadow) },
    品牌gap: getComputedStyle(brand).gap,
    章: { 尺寸: box(seal), 圆角: sc.borderRadius, 边框: sc.borderTopWidth + ' ' + sc.borderTopColor,
      背景图: bg(sc.backgroundImage), 字色: sc.color, 字号: sc.fontSize, 字族: sc.fontFamily.slice(0, 40),
      字重: sc.fontWeight, 字距: sc.letterSpacing, 行高: sc.lineHeight, 阴影: bg(sc.boxShadow) },
    标题: { 字号: getComputedStyle(t).fontSize, 字重: getComputedStyle(t).fontWeight,
      字距: getComputedStyle(t).letterSpacing, 字色: getComputedStyle(t).color, 尺寸: box(t) },
    副标: { 字号: getComputedStyle(p).fontSize, 字距: getComputedStyle(p).letterSpacing,
      字色: getComputedStyle(p).color, 尺寸: box(p), 显示: getComputedStyle(p).display },
    导航: { gap: getComputedStyle(nav).gap, flex: getComputedStyle(nav).flexGrow,
      链接: { 尺寸: box(link), 内边距: getComputedStyle(link).padding, 字号: getComputedStyle(link).fontSize,
        字族: getComputedStyle(link).fontFamily.slice(0, 40), 字距: getComputedStyle(link).letterSpacing,
        字色: getComputedStyle(link).color, 圆角: getComputedStyle(link).borderRadius } },
    右侧: { 文本: btn.textContent.trim().slice(0, 6), 尺寸: box(btn), 内边距: bc.padding,
      边框: bc.borderTopWidth + ' ' + bc.borderTopColor, 圆角: bc.borderRadius,
      背景色: bc.backgroundColor, 字色: bc.color, 字号: bc.fontSize, 字重: bc.fontWeight,
      字距: bc.letterSpacing, 字族: bc.fontFamily.slice(0, 40) },
    溢出: document.documentElement.scrollWidth > document.documentElement.clientWidth
      ? '横向溢出 ' + document.documentElement.scrollWidth + '>' + document.documentElement.clientWidth : '无',
  };
})()`;

async function main() {
  const proc = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/yshdrL' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const t = j.find((x) => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  if (!ws) { console.error('no target'); proc.kill(); process.exit(1); }
  let id = 0; const pending = {};
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise((res) => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => (await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true })).result.result.value;
  await send('Page.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: W < 700 });
  await send('Page.navigate', { url: URL_ });
  for (let i = 0; i < 40; i++) {
    await sleep(600);
    if (await ev(`!!document.querySelector('.app-header .brand-seal, .site-header .brand-seal')`)) break;
  }
  await sleep(1800);
  console.log(JSON.stringify(await ev(EXPR), null, 1));
  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80, clip: { x: 0, y: 0, width: W, height: 130, scale: 1 } });
  fs.writeFileSync(OUT, Buffer.from(shot.result.data, 'base64'));
  ws.close(); proc.kill();
  process.exit(0);
}
main().catch((e) => { console.error('FAIL', e); process.exit(1); });
