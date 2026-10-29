// 生产补测：正文里出现不存在/未被引用的编号时，必须只是纯文本、不可点
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = 'http://47.93.14.11';

async function main() {
  const outDir = __dirname + '/audit/codes_prod';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9513;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscodeprod2' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: BASE + '/aiqa' });
  await sleep(4000);
  await ev(`localStorage.removeItem('yisu_aiqa_chat_v1');'ok'`);
  await send('Page.navigate', { url: BASE + '/aiqa' });
  await sleep(3500);

  const q = '请把下面这几个编号原样抄给我，不要解释：〔档案-9999〕〔纹样-7777〕〔面料-0011〕';
  const inp = await box('.chat-input-row .el-input__inner');
  await clickAt(inp.x, inp.y, 400);
  await send('Input.insertText', { text: q });
  await sleep(300);
  const btn = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn.x, btn.y, 3000);
  for (let i = 0; i < 50; i++) {
    const done = await ev("document.querySelectorAll('.chat-row.assistant').length >= 1 && !document.querySelector('.chat-input-row button.is-loading')");
    if (done) break;
    await sleep(1500);
  }
  await sleep(2500);
  console.log('   正文：' + await ev(`(document.querySelectorAll('.chat-row.assistant .chat-content')[0]||{innerText:''}).innerText.replace(/\\s+/g,' ').slice(0,200)`));
  console.log('   可点编号：' + await ev(`JSON.stringify([...document.querySelectorAll('.code-ref')].map(e=>({文:e.textContent,链:e.getAttribute('href')})))`));
  console.log('   纯文本编号：' + await ev(`JSON.stringify((document.querySelector('.chat-row.assistant .chat-content')||{innerText:''}).innerText.match(/〔[^〕]{1,12}〕/g)||[])`));
  console.log('   结论：9999/7777 可点数 = ' + await ev(`[...document.querySelectorAll('.code-ref')].filter(e=>/9999|7777/.test(e.textContent)).length`));
  await shot('05_hallucination_guard');
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
