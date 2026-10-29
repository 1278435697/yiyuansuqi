// /aiqa 引用可点实测：回答下方出现可点引用 chip、点 chip 跳站内详情、推荐卡与 chip 同源、390 视口不溢出
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/aiqa_sources';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9483;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysaiqasrc' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };
  const STATE = `JSON.stringify({
    引用条: [...document.querySelectorAll('.src-row')].map(r=>r.textContent.replace(/\\s+/g,' ').trim()),
    chip链: [...document.querySelectorAll('.src-chip')].map(a=>a.getAttribute('href')),
    纯文本引用: [...document.querySelectorAll('p.chat-ref')].map(e=>e.textContent.trim().slice(0,40)),
    卡标题: [...document.querySelectorAll('.rec-card b')].map(e=>e.textContent.trim()),
    路由: location.pathname,
    灯箱: !!document.querySelector('.ys-lightbox')
  })`;

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base });
  await sleep(3500);
  await ev(`localStorage.removeItem('yisu_aiqa_chat_v1');localStorage.removeItem('yisu_aiqa_webqa_v1');'cleared'`);
  await send('Page.navigate', { url: base });
  await sleep(3000);

  console.log('== 1) 提问「宋代褙子的形制是怎样的？」');
  await clickAt((await box('.chat-input-row .el-input__inner')).x, (await box('.chat-input-row .el-input__inner')).y);
  await send('Input.insertText', { text: '宋代褙子的形制是怎样的？' });
  await sleep(300);
  const btn = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn.x, btn.y, 3000);
  for (let i = 0; i < 40; i++) {
    if (Number(await ev(`document.querySelectorAll('.chat-row.assistant .chat-content').length`)) >= 1) break;
    await sleep(1500);
  }
  await sleep(5000);
  console.log('   ' + await ev(STATE));
  await shot('answered_with_source_chips');

  console.log('== 2) 点第一个引用 chip');
  const chip = await box('.src-chip');
  if (chip.none) { console.log('   没有引用 chip'); }
  else {
    await clickAt(chip.x, chip.y, 2500);
    console.log('   ' + await ev(STATE));
    await shot('after_source_chip_click');
  }

  console.log('== 3) 史料没命中时是否退回纯文本引用（问「今天天气好吗」）');
  await send('Page.navigate', { url: base });
  await sleep(3000);
  await clickAt((await box('.chat-input-row .el-input__inner')).x, (await box('.chat-input-row .el-input__inner')).y);
  await send('Input.insertText', { text: '今天天气好吗' });
  await sleep(300);
  const btn2 = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn2.x, btn2.y, 3000);
  for (let i = 0; i < 40; i++) {
    if (Number(await ev(`document.querySelectorAll('.chat-row.assistant .chat-content').length`)) >= 1) break;
    await sleep(1500);
  }
  await sleep(3000);
  console.log('   ' + await ev(STATE));
  await shot('no_hit_fallback');

  console.log('== 4) 390x844 视口（带着上面对话）');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url: base });
  await sleep(3500);
  console.log('   ' + await ev(`JSON.stringify({横向滚动宽:document.scrollingElement.scrollWidth,视口:innerWidth,chip数:document.querySelectorAll('.src-chip').length,气泡宽:(document.querySelector('.chat-bubble')||{}).getBoundingClientRect?Math.round(document.querySelector('.chat-bubble').getBoundingClientRect().width):0})`));
  await shot('mobile_390_chips');

  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
