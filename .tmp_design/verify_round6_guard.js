// 防幻觉分支实测：喂一个「引用里没有的编号」，确认它只是纯文本、不会变成链接
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/codes_guard';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9503;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysguard' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const clickAt = async (x, y, w = 1500) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3500);
  await ev(`localStorage.clear();'ok'`);
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3000);
  const inp = await box('.chat-input-row .el-input__inner');
  await clickAt(inp.x, inp.y, 400);
  await send('Input.insertText', { text: '随便问一句' });
  const btn = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn.x, btn.y, 4000);
  await sleep(3000);

  console.log('== mock 回答里的编号渲染');
  console.log('   ' + await ev(`JSON.stringify({
    链接编号:[...document.querySelectorAll('.code-ref')].map(e=>({文:e.textContent,链:e.getAttribute('href')})),
    正文纯文本:(document.querySelector('.chat-row.assistant .chat-content')||{}).innerText,
    正文HTML:(document.querySelector('.chat-row.assistant .chat-content')||{}).innerHTML,
    chip数:document.querySelectorAll('.src-chip').length})`));
  await shot('guard_render');
  console.log('== 判定');
  console.log('   ' + await ev(`(()=>{const html=(document.querySelector('.chat-row.assistant .chat-content')||{}).innerHTML||'';
    return JSON.stringify({
      已知编号做成链接: /档案-0007<\\/a>|>〔档案-0007〕<\\//.test(html),
      未知编号是纯文本: !/<a[^>]*>\\s*〔档案-9999〕/.test(html) && html.includes('档案-9999'),
      英文编号未误认: !/<a[^>]*>〔fabric-0001〕/.test(html),
      未知纹样编号纯文本: !/<a[^>]*>〔纹样-0000〕/.test(html) && html.includes('纹样-0000')})})()`));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
