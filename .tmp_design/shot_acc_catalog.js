// 衣冠子站目录卡截图（改前后同一位置）：node shot_acc_catalog.js <base> <tag>
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const BASE = process.argv[2], TAG = process.argv[3] || 'x';
  const outDir = __dirname + '/audit/fit_' + TAG;
  fs.mkdirSync(outDir, { recursive: true });
  const port = Number(process.argv[5] || 9551);
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysacc' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 160);
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  const w = Number(process.argv[4] || 1440);
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: BASE + '/accessories/index.html' });
  await sleep(5000);
  await ev(`document.getElementById('catalog').scrollIntoView();'ok'`);
  await sleep(1200);
  for (let i = 0; i < 6; i++) { await ev(`window.scrollBy(0, 700)`); await sleep(500); }
  await ev(`document.getElementById('catalog').scrollIntoView();'ok'`);
  await sleep(1500);
  console.log(await ev(`(()=>{const a=[...document.querySelectorAll('.acc-card')];
    const c=a.filter(e=>e.getBoundingClientRect().top>0&&e.getBoundingClientRect().top<innerHeight).slice(0,6);
    return JSON.stringify({卡数:a.length, 首排:c.map(e=>{const i=e.querySelector('img'),r=i.getBoundingClientRect(),v=e.querySelector('.card-visual').getBoundingClientRect();
      return i.className+' '+Math.round(r.width)+'x'+Math.round(r.height)+'/'+Math.round(v.width)+'x'+Math.round(v.height)+' fit='+getComputedStyle(i).objectFit+' 原'+i.naturalWidth+'x'+i.naturalHeight;})});})()`));
  const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 });
  fs.writeFileSync(outDir + '/acc_catalog_' + w + '.jpg', Buffer.from(r.result.data, 'base64'));
  console.log('截图 ' + outDir + '/acc_catalog_' + w + '.jpg');
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
