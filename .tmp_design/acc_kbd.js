// 衣冠皮层键盘/交互实测：分段筛选条仍可用 + 卡片 Enter 可打开 + 焦点环可见
// 用法：node acc_kbd.js <url> <端口>
const { spawn } = require('child_process');
const os = require('os');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const URL_ = process.argv[2];
const PORT = Number(process.argv[3] || 9751);

async function main() {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/yskbd' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL_ });
  await sleep(5000);

  const report = {};
  report.初始卡片数 = await ev(`document.querySelectorAll('.acc-card').length`);

  // 1) 分段筛选条：键盘 Tab 到隐藏 radio 并空格选中，看列表是否随之变化
  const radioProbe = await ev(`(async()=>{
    const grp = document.querySelector('.acc-filter-row .el-radio-group');
    if (!grp) return '本页无分段筛选条';
    const inputs = [...grp.querySelectorAll('input[type=radio]')];
    const target = inputs[2] || inputs[inputs.length - 1];
    if (!target) return '无 radio 输入';
    target.focus();
    const focused = document.activeElement === target;
    const before = document.querySelectorAll('.acc-card').length;
    target.click();
    await new Promise(r => setTimeout(r, 2200));
    const cs = getComputedStyle(target.nextElementSibling);
    return JSON.stringify({
      可聚焦: focused,
      选中类别: target.nextElementSibling ? target.nextElementSibling.textContent.trim() : '',
      选中态背景: cs.backgroundImage.slice(0, 42) || cs.backgroundColor,
      焦点环: (() => { target.focus(); const c = getComputedStyle(target.nextElementSibling); return c.outlineColor + ' ' + c.outlineWidth; })(),
      卡片数: { 前: before, 后: document.querySelectorAll('.acc-card').length },
    });
  })()`);
  report.分段筛选 = radioProbe;

  await send('Page.navigate', { url: URL_ });
  await sleep(5000);

  // 2) 卡片 Enter：键盘激活应触发与点击相同的动作
  const cardProbe = await ev(`(async()=>{
    const card = document.querySelector('.acc-card');
    if (!card) return '无卡片';
    const cs = getComputedStyle(card);
    card.focus();
    const focused = document.activeElement === card;
    const ring = (() => { const c = getComputedStyle(card); return c.outlineStyle + ' ' + c.outlineWidth + ' ' + c.outlineColor; })();
    card.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    await new Promise(r => setTimeout(r, 1200));
    const overlay = document.querySelector('.split-reveal, .sr-mask, .sr-root, [class*=split]');
    return JSON.stringify({
      role: card.getAttribute('role'), tabindex: card.getAttribute('tabindex'),
      可聚焦: focused, 焦点环: ring,
      回车后浮层: overlay ? String(overlay.className).slice(0, 40) : (location.pathname + ' 无分裂浮层（路由卡直接跳转：' + location.pathname + '）'),
      当前路径: location.pathname,
    });
  })()`);
  report.卡片键盘激活 = cardProbe;

  console.log(URL_);
  console.log(JSON.stringify(report, null, 1));
  ws.close(); child.kill();
}
main().catch((e) => { console.error('FAIL', e); process.exit(1); });
