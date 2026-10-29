// 真实键盘 Tab 走查：记录焦点落点顺序与焦点环（:focus-visible 只有真键盘才触发）
// 用法：node acc_tab.js <url> <端口> [最大Tab次数]
const { spawn } = require('child_process');
const os = require('os');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const URL_ = process.argv[2];
const PORT = Number(process.argv[3] || 9771);
const MAX = Number(process.argv[4] || 24);

async function main() {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ystab' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify(r.result.exceptionDetails).slice(0, 200);
    return r.result.result.value;
  };
  const tab = () => send('Input.dispatchKeyEvent', { type: 'keyDown', windowsVirtualKeyCode: 9, code: 'Tab', key: 'Tab', text: '\t' })
    .then(() => send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 9, code: 'Tab', key: 'Tab' }));

  await send('Page.enable', {});
  await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL_ });
  await sleep(5000);

  const seq = [];
  for (let i = 0; i < MAX; i++) {
    await tab();
    await sleep(90);
    const info = await ev(`(()=>{
      const a = document.activeElement;
      if (!a) return null;
      const inScope = !!a.closest('.acc-scope');
      const c = getComputedStyle(a);
      const ring = c.outlineStyle === 'none' ? '无' : c.outlineWidth + ' ' + c.outlineColor;
      return { 标签: a.tagName, 类: String(a.className).slice(0, 30), 文本: (a.textContent || a.value || '').trim().slice(0, 10), 在作用域内: inScope, 焦点环: ring };
    })()`);
    if (info) seq.push(info);
  }
  console.log(URL_);
  console.log(JSON.stringify(seq, null, 1));
  ws.close(); child.kill();
}
main().catch((e) => { console.error('FAIL', e); process.exit(1); });
