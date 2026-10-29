// 截图：修复后的纹样详情主图 + 打开的多图灯箱（箭头可见）
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const OUT = 'D:/yisu-ai-platform/.tmp_design/audit/pattern/';

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const port = 9415;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysshot' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); return r.result.exceptionDetails ? 'EXC' : r.result.result.value; };
  const shot = async (name) => {
    const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
    fs.writeFileSync(OUT + name, Buffer.from(r.result.data, 'base64'));
    console.log('saved', name);
  };
  const clickAt = async (x, y) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(800);
  };
  const ctr = (sel) => ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`);

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: process.argv[2] });
  await sleep(4500);
  const SEL = process.argv[3] || '.img-col img';
  const TAG = process.argv[4] || 'viewer';
  await ev(`(function(){var e=document.querySelector(${JSON.stringify(SEL)});if(e)e.scrollIntoView({block:"center"});return 1})()`);
  await sleep(1200);
  await shot(TAG + '_before_click.jpg');
  const a = JSON.parse(await ctr(SEL));
  await clickAt(a.x, a.y);
  await shot(TAG + '_open.jpg');
  const n = await ctr('.el-image-viewer__next');
  if (n !== 'NO') { const q = JSON.parse(n); await clickAt(q.x, q.y); await shot(TAG + '_next.jpg'); }
  // 手机视口同样验一次
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await sleep(1500);
  await ev(`(function(){var e=document.querySelector(${JSON.stringify(SEL)});if(e)e.scrollIntoView({block:"center"});return 1})()`);
  await sleep(1200);
  const m = await ctr(SEL);
  if (m !== 'NO') { const q = JSON.parse(m); await clickAt(q.x, q.y); await shot(TAG + '_mobile.jpg'); }
  ws.close(); child.kill();
}
main();
