// 对比主站与衣冠子站的顶部导航条实测样式（同一时刻、同一视口、各自独立 profile 防缓存）
const { spawn } = require('child_process');
const os = require('os');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const PORT = Number(process.argv[2] || 9779);
const TARGETS = [
  ['主站 /archive', 'http://47.93.14.11/archive'],
  ['衣冠 /accessories', 'http://47.93.14.11/accessories/index.html'],
];

const EXPR = `(() => {
  const pick = (el, keys) => {
    if (!el) return null;
    const c = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const o = { 尺寸: Math.round(r.width) + 'x' + Math.round(r.height) };
    for (const k of keys) o[k] = c[k];
    return o;
  };
  const bg = (s) => (s || '').replace(/\\s+/g, ' ').slice(0, 150);
  const hdr = document.querySelector('.site-header, header');
  const hc = hdr ? getComputedStyle(hdr) : null;
  const nav = document.querySelector('.site-nav, nav');
  const link = nav ? nav.querySelector('a') : null;
  const act = nav ? nav.querySelector('a.is-active, a[aria-current], .router-link-active') : null;
  const seal = document.querySelector('.brand-seal, .logo, [class*=logo]');
  const inner = hdr ? hdr.firstElementChild : null;
  const login = document.querySelector('.login-link, header a[href="/"], header button');
  return {
    头部: hdr ? {
      尺寸: Math.round(hdr.getBoundingClientRect().width) + 'x' + Math.round(hdr.getBoundingClientRect().height),
      position: hc.position,
      背景: bg(hc.backgroundImage) + ' | ' + bg(hc.backgroundColor),
      下边框: hc.borderBottomWidth + ' ' + hc.borderBottomColor,
      阴影: bg(hc.boxShadow),
      内边距: hc.padding,
      内容宽: inner ? Math.round(inner.getBoundingClientRect().width) + '@' + Math.round(inner.getBoundingClientRect().left) : '?',
    } : '未找到',
    品牌章: pick(seal, ['borderRadius', 'border', 'backgroundColor', 'fontFamily', 'fontSize', 'color']),
    品牌章背景: seal ? bg(getComputedStyle(seal).backgroundImage) : null,
    导航链接: pick(link, ['fontSize', 'fontFamily', 'letterSpacing', 'color', 'padding']),
    导航间距: nav ? getComputedStyle(nav).gap : null,
    选中项: act ? {
      文本: act.textContent.trim(),
      背景: bg(getComputedStyle(act).backgroundImage) + '|' + bg(getComputedStyle(act).backgroundColor),
      边框: getComputedStyle(act).borderTopWidth + ' ' + getComputedStyle(act).borderTopColor,
      圆角: getComputedStyle(act).borderRadius,
      字色: getComputedStyle(act).color,
    } : '未找到',
    登录: login ? {
      文本: login.textContent.trim().slice(0, 6),
      背景: bg(getComputedStyle(login).backgroundImage) + '|' + bg(getComputedStyle(login).backgroundColor),
      边框: getComputedStyle(login).borderTopWidth + ' ' + getComputedStyle(login).borderTopColor,
      圆角: getComputedStyle(login).borderRadius,
      尺寸: Math.round(login.getBoundingClientRect().width) + 'x' + Math.round(login.getBoundingClientRect().height),
    } : '未找到',
  };
})()`;

async function main() {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/yshdr' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const t = j.find((x) => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  if (!ws) { console.error('no target'); child.kill(); process.exit(1); }
  let id = 0; const pending = {};
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise((res) => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => (await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true })).result.result.value;

  await send('Page.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  const out = {};
  for (const [name, url] of TARGETS) {
    await send('Page.navigate', { url });
    await sleep(5000);
    out[name] = await ev(EXPR);
  }
  console.log(JSON.stringify(out, null, 1));
  ws.close(); child.kill();
}
main().catch((e) => { console.error('FAIL', e); process.exit(1); });
