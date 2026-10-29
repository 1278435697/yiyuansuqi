// 定位 390 视口下把布局撑到 465 的元素（区分推荐卡与既有区块）
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const port = 9501;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yswide' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true });
    if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify(r.result.exceptionDetails).slice(0, 200);
    return r.result.result.value;
  };
  await send('Page.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url: 'http://localhost:5173/aiqa' });
  await sleep(3500);
  // 直接把上一轮实测过的推荐结果塞进 localStorage（只改内存，不发请求）
  await ev(`localStorage.setItem('yisu_aiqa_chat_v1', JSON.stringify(${process.argv[2]}));localStorage.setItem('yisu_aiqa_webqa_v1', JSON.stringify({keyword:'明代马面裙用什么面料？'}));'ok'`);
  await send('Page.navigate', { url: 'http://localhost:5173/aiqa' });
  await sleep(3500);
  console.log(await ev(`(()=>{
    const wide=[];
    document.querySelectorAll('*').forEach(e=>{
      const r=e.getBoundingClientRect();
      if(r.width>392||e.scrollWidth>392) wide.push([e.className&&String(e.className).slice(0,28)||e.tagName, Math.round(r.width), e.scrollWidth, Math.round(r.left)]);
    });
    return JSON.stringify({innerWidth, 视口外元素: wide.slice(0,22)},null,1);
  })()`));
  await ev(`document.querySelector('.rec-wrap').scrollIntoView({block:'center'});'ok'`);
  await sleep(600);
  const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 66 });
  require('fs').writeFileSync(__dirname + '/audit/aiqa_rec/mobile_390_injected.jpg', Buffer.from(r.result.data, 'base64'));
  console.log('截图 mobile_390_injected');
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
