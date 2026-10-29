// 390 溢出归因：逐个隐藏候选元素，看谁把文档撑到 464
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const port = 9501;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscode6' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 200);
    return r.result.result.value;
  };
  const box = async (sel) => JSON.parse(await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return JSON.stringify({none:1});const r=e.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()`));
  const clickAt = async (x, y, w = 1600) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4000);
  const inp = await box('.chat-input-row .el-input__inner');
  await clickAt(inp.x, inp.y, 500);
  await send('Input.insertText', { text: '褙子的形制是什么？出土于哪里？' });
  const btn = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn.x, btn.y, 3000);
  for (let i = 0; i < 45; i++) {
    if (Number(await ev(`document.querySelectorAll('.code-ref').length`)) >= 1) break;
    await sleep(1500);
  }
  await sleep(3000);
  console.log('基线 ' + await ev(`JSON.stringify({滚动宽:document.scrollingElement.scrollWidth})`));

  const cands = ['.chat-row.assistant', '.src-row', '.rec-row', '.rec-card', '.chat-input-row', '.chat-head-row', '.follow-chips', '.ask-card .ys-actions', '.question-list'];
  for (const c of cands) {
    const r = await ev(`(()=>{const els=[...document.querySelectorAll(${JSON.stringify(c)})];if(!els.length)return 'NO-SEL';
      els.forEach(e=>e.dataset.abl=e.style.display||'');els.forEach(e=>e.style.display='none');
      const w=document.scrollingElement.scrollWidth;
      els.forEach(e=>e.style.display=e.dataset.abl||'');return JSON.stringify({n:els.length,滚动宽:w})})()`);
    console.log('隐藏 ' + c + ' → ' + r);
  }
  // 逐条气泡内的构成
  console.log('气泡内 ' + await ev(`JSON.stringify([...document.querySelectorAll('.chat-row.assistant')].map(r=>({气泡宽:Math.round(r.querySelector('.chat-bubble').getBoundingClientRect().width),chip行数:r.querySelectorAll('.src-row').length,rec行数:r.querySelectorAll('.rec-row').length})))`));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
