// 真键盘 Tab 到指定序号，读取"可见焦点环"（input 本体 outline + 最近包装层的 outline/box-shadow）
// 用法：node acc_focus.js <url> <端口> <序号> [选择器关键字]
const { spawn } = require('child_process');
const os = require('os');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const URL_ = process.argv[2];
const PORT = Number(process.argv[3] || 9831);
const NTH = Number(process.argv[4] || 14);
const HINT = process.argv[5] || '';

async function main() {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ysfocus' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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

  for (let i = 0; i < NTH; i++) { await tab(); await sleep(80); }

  const res = await ev(`(()=>{
    const a = document.activeElement;
    const pick = (el) => { if (!el) return null; const c = getComputedStyle(el); return {
      sel: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\\s+/).slice(0,2).join('.') : ''),
      outline: c.outlineStyle === 'none' ? 'none' : c.outlineWidth + ' ' + c.outlineColor,
      boxShadow: c.boxShadow === 'none' ? 'none' : c.boxShadow.slice(0, 90),
      border: c.borderTopWidth + ' ' + c.borderTopColor,
    };};
    const chain = [];
    let cur = a;
    for (let i = 0; i < 5 && cur; i++) { chain.push(pick(cur)); cur = cur.parentElement; }
    return { 焦点: chain, matchesHint: ${HINT ? `String(a.className).includes(${JSON.stringify(HINT)})` : 'true'} };
  })()`);
  console.log(URL_ + '  Tab×' + NTH);
  console.log(JSON.stringify(res, null, 1));
  ws.close(); child.kill();
}
main().catch((e) => { console.error('FAIL', e); process.exit(1); });
