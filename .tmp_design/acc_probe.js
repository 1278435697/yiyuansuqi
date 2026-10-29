// 衣冠皮层实测探针：横向溢出 / 溢出元素 / object-fit 普查 / 卡片与工具条几何
// 用法：node acc_probe.js <url> <宽> <端口>
const { spawn } = require('child_process');
const os = require('os');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const URL_ = process.argv[2];
const WIDTH = Number(process.argv[3] || 1440);
const PORT = Number(process.argv[4] || 9701);

async function main() {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ysacc' + PORT + WIDTH, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify(r.result.exceptionDetails).slice(0, 240);
    return r.result.result.value;
  };
  await send('Page.enable', {});
  await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 900, deviceScaleFactor: 1, mobile: WIDTH < 500 });
  await send('Page.navigate', { url: URL_ });
  await sleep(5000);
  const out = await ev(`(()=>{
    const vw = document.documentElement.clientWidth;
    const wide = [];
    document.querySelectorAll('.acc-scope, .acc-scope *').forEach((e) => {
      const r = e.getBoundingClientRect();
      if (r.width > 0 && (r.right > vw + 1 || r.left < -1)) {
        wide.push([(e.className && String(e.className).slice(0, 34)) || e.tagName, Math.round(r.left), Math.round(r.right)]);
      }
    });
    const fit = {};
    document.querySelectorAll('.acc-scope img').forEach((e) => {
      const f = getComputedStyle(e).objectFit || '(空)';
      fit[f] = (fit[f] || 0) + 1;
    });
    const g = document.querySelector('.acc-grid');
    const tools = document.querySelector('.acc-toolbar-tools');
    const tb = document.querySelector('.acc-toolbar');
    const first = document.querySelector('.acc-card');
    return JSON.stringify({
      视口: vw,
      横向溢出: document.documentElement.scrollWidth - vw,
      溢出元素: wide.slice(0, 12),
      objectFit普查: fit,
      卡片数: document.querySelectorAll('.acc-card').length,
      网格列: g ? getComputedStyle(g).gridTemplateColumns.split(' ').length : null,
      卡宽: first ? Math.round(first.getBoundingClientRect().width) : null,
      工具条: tools ? { 行宽: Math.round(tb.getBoundingClientRect().width), 工具宽: Math.round(tools.getBoundingClientRect().width), 高: Math.round(tools.getBoundingClientRect().height) } : null,
      作用域根: (() => { const s = document.querySelector('.acc-scope'); if (!s) return null; const r = s.getBoundingClientRect(); return { 左: Math.round(r.left), 右: Math.round(r.right), 宽: Math.round(r.width) }; })(),
    }, null, 1);
  })()`);
  console.log(URL_, '@', WIDTH);
  console.log(out);
  ws.close(); child.kill();
}
main().catch((e) => { console.error('FAIL', e); process.exit(1); });
