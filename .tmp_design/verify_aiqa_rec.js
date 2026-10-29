// /aiqa 答后推荐检索实测：卡片渲染、点卡跳详情不被全局灯箱抢占、追问 chip 能发送、390 视口不溢出
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/aiqa_rec';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9481;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysaiqa' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const box = async (sel) => JSON.parse(await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return JSON.stringify({none:1});const r=e.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height})})()`));
  const clickAt = async (x, y, w = 1600) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  const shot2 = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };
  const REC = `JSON.stringify({
    卡数: document.querySelectorAll('.rec-card').length,
    类型: [...document.querySelectorAll('.rec-card .rec-type')].map(e=>e.textContent.trim()),
    标题: [...document.querySelectorAll('.rec-card b')].map(e=>e.textContent.trim()),
    图载: [...document.querySelectorAll('.rec-card img')].map(i=>i.naturalWidth>0),
    追问: [...document.querySelectorAll('.ask-chip')].map(e=>e.textContent.trim()),
    灯箱: !!document.querySelector('.ys-lightbox'),
    路由: location.pathname
  })`;

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base });
  await sleep(3500);
  await ev(`localStorage.removeItem('yisu_aiqa_chat_v1');localStorage.removeItem('yisu_aiqa_webqa_v1');'cleared'`);
  await send('Page.navigate', { url: base });
  await sleep(3000);

  console.log('== 1) 提问「明代马面裙用什么面料？」');
  await clickAt((await box('.chat-input-row .el-input__inner')).x, (await box('.chat-input-row .el-input__inner')).y);
  await send('Input.insertText', { text: '明代马面裙用什么面料？' });
  await sleep(300);
  const btn = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn.x, btn.y, 3000);
  for (let i = 0; i < 40; i++) {
    const n = await ev(`document.querySelectorAll('.chat-row.assistant .chat-content').length`);
    if (n >= 1) break;
    await sleep(1500);
  }
  await sleep(4000);
  console.log('   ' + await ev(REC));
  await shot2('answered_desktop');

  console.log('== 2) 点第一张卡的图片（看是否被全局灯箱抢占 / 是否跳详情）');
  const card = await box('.rec-card img');
  await clickAt(card.x, card.y, 2500);
  console.log('   ' + await ev(REC));
  await shot2('after_card_click');

  console.log('== 3) 回问答页点追问 chip');
  await send('Page.navigate', { url: base });
  await sleep(3000);
  const ask = await box('.ask-chip');
  if (!ask.none) {
    await clickAt(ask.x, ask.y, 2500);
    for (let i = 0; i < 40; i++) {
      const n = await ev(`document.querySelectorAll('.chat-row.user .chat-content').length`);
      if (n >= 2) break;
      await sleep(1500);
    }
    await sleep(4000);
  }
  console.log('   ' + await ev(REC));
  await shot2('after_chip_click');

  console.log('== 4) 390x844 视口');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url: base });
  await sleep(3500);
  console.log('   ' + await ev(`JSON.stringify({横向滚动宽:document.scrollingElement.scrollWidth,视口:innerWidth,卡数:document.querySelectorAll('.rec-card').length})`));
  await shot2('mobile_390');

  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
