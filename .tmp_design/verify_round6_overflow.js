// 390 溢出归因：空对话 vs 带编号对话，宽元素定位，404 资源
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/codes_round4';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9497;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscode4' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {}; const bad = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; }
    if (m.method === 'Network.responseReceived' && m.params.response.status >= 400)
      bad.push(m.params.response.status + ' ' + m.params.response.url.slice(0, 120));
  };
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
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 60 }); if (r.result && r.result.data) fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); };
  const MEASURE = `(()=>{const w=innerWidth;const out=[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>w+1)
    .sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right).slice(0,5)
    .map(e=>({标签:e.tagName+'.'+(e.className&&e.className.toString?e.className.toString().slice(0,30):''),右:Math.round(e.getBoundingClientRect().right),文:(e.innerText||'').replace(/\\s+/g,' ').slice(0,26)}));
    return JSON.stringify({innerWidth:w,滚动宽:document.scrollingElement.scrollWidth,越界:out})})()`;

  await send('Page.enable', {}); await send('Runtime.enable', {}); await send('Network.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });

  console.log('== A) 390 · 空对话（没有编号）');
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3500);
  await ev(`localStorage.clear();'ok'`);
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4000);
  console.log('   ' + await ev(MEASURE));
  await shot('a_empty_390');

  console.log('== B) 同一页生产对照 47.93.14.11/aiqa · 空对话');
  await send('Page.navigate', { url: 'http://47.93.14.11/aiqa' });
  await sleep(6000);
  console.log('   ' + await ev(MEASURE));
  await shot('b_prod_390');

  console.log('== C) 本地 390 · 提问后带编号');
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3500);
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
  console.log('   ' + await ev(MEASURE));
  console.log('   编号 ' + await ev(`JSON.stringify([...document.querySelectorAll('.code-ref')].map(e=>e.textContent))`));
  await shot('c_codes_390');

  console.log('== D) 400+ 资源：' + JSON.stringify([...new Set(bad)].slice(0, 8)));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
