// 390 溢出真因定位：忽略处在横向滚动容器里的元素，找出真正把文档撑到 464 的元素
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const port = 9499;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscode5' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 60 }); if (r.result && r.result.data) fs.writeFileSync(__dirname + '/audit/codes_round5/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); };
  fs.mkdirSync(__dirname + '/audit/codes_round5', { recursive: true });

  const CULPRIT = `(()=>{
    const w=innerWidth;
    const clipped=(e)=>{let p=e.parentElement;while(p){const s=getComputedStyle(p);if(/auto|scroll|hidden/.test(s.overflowX))return true;p=p.parentElement;}return false;};
    const out=[...document.querySelectorAll('body *')]
      .filter(e=>e.getBoundingClientRect().right>w+1 && !clipped(e))
      .sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right).slice(0,8)
      .map(e=>({sel:e.tagName+'.'+(e.className&&e.className.toString?e.className.toString().slice(0,40):''),
                右:Math.round(e.getBoundingClientRect().right),宽:Math.round(e.getBoundingClientRect().width),
                父:(e.parentElement.tagName||'')+'.'+(e.parentElement.className&&e.parentElement.className.toString?e.parentElement.className.toString().slice(0,30):''),
                文:(e.innerText||'').replace(/\\s+/g,' ').slice(0,40)}));
    return JSON.stringify({innerWidth:w,滚动宽:document.scrollingElement.scrollWidth,真越界:out})})()`;

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4000);
  console.log('== 空对话 ' + await ev(CULPRIT));
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
  console.log('== 带答案 ' + await ev(CULPRIT));
  console.log('== 分段宽 ' + await ev(`JSON.stringify(['.chat-bubble','.chat-content','.src-row','.src-chip','.rec-card','.chat-input-row'].map(s=>{const e=document.querySelector(s);if(!e)return s+':无';const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return {sel:s,右:Math.round(r.right),宽:Math.round(r.width),scrollW:e.scrollWidth,overflowX:cs.overflowX,whiteSpace:cs.whiteSpace,wordBreak:cs.wordBreak}}))`));
  await shot('culprit_390');
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
