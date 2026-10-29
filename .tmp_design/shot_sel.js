// 指定页面截图：滚动到某个选择器出现的位置再拍，用于目视复核 contain 后的留白
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const [, , URL_, TAG, SEL, W, PORT_] = process.argv;
const WIDTH = Number(W || 1440), PORT = Number(PORT_ || 9585);

async function main() {
  const dir = __dirname + '/audit/fit_' + TAG;
  fs.mkdirSync(dir, { recursive: true });
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ysshot' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => (await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true })).result.result.value;
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 900, deviceScaleFactor: 1, mobile: WIDTH < 500 });
  await send('Page.navigate', { url: URL_ });
  await sleep(4500);
  if (SEL) {
    await ev(`(()=>{const el=document.querySelector(${JSON.stringify(SEL)}); if(el) el.scrollIntoView({block:'center'}); return el?1:0})()`);
    await sleep(1400);
  } else {
    await ev(`(()=>{let h=0;return new Promise(r=>{const t=setInterval(()=>{window.scrollBy(0,1400);h+=1400;if(h>document.body.scrollHeight){clearInterval(t);r(1)}},60)})})()`);
    await sleep(1500);
    await ev('window.scrollTo(0,0)');
    await sleep(600);
  }
  const overflow = await ev(`document.documentElement.scrollWidth - window.innerWidth`);
  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 72 });
  const name = dir + '/' + WIDTH + '_' + (SEL ? SEL.replace(/[^\w-]/g, '_') : 'top') + '.jpg';
  fs.writeFileSync(name, Buffer.from(shot.result.data, 'base64'));
  console.log('saved', name, '横向溢出', overflow, '页高', await ev('document.body.scrollHeight'));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
