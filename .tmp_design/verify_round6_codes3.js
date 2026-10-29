// 编号轮补测 v3：先提问 → 点配饰编号进子站 → 面料/纹样详情编号 → 390 视口（带对话）
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/codes_round3';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9495;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscode3' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  const errs = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; }
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errs.push(m.params.entry.text.slice(0, 140));
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
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };
  const ask = async (q) => {
    const inp = await box('.chat-input-row .el-input__inner');
    await clickAt(inp.x, inp.y, 400);
    await send('Input.insertText', { text: q });
    await sleep(300);
    const btn = await box('.chat-input-row button.el-button--primary');
    await clickAt(btn.x, btn.y, 3000);
    for (let i = 0; i < 45; i++) {
      if (Number(await ev(`document.querySelectorAll('.chat-row.assistant .chat-content .code-ref').length`)) >= 1) break;
      await sleep(1500);
    }
    await sleep(3000);
  };

  await send('Page.enable', {}); await send('Runtime.enable', {}); await send('Log.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  console.log('== 1) 提问，让正文出现编号');
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3500);
  await ev(`localStorage.removeItem('yisu_aiqa_chat_v1');'ok'`);
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3000);
  await ask('褙子的形制是什么？出土于哪里？');
  console.log('   ' + await ev(`JSON.stringify([...document.querySelectorAll('.code-ref')].map(e=>({文:e.textContent,链:e.getAttribute('href')})))`));

  console.log('== 2) 点配饰编号 〔衣制-07〕进子站详情');
  const acc = JSON.parse(await ev(`(()=>{const a=[...document.querySelectorAll('.code-ref')].find(e=>(e.getAttribute('href')||'').startsWith('/accessories'));if(!a)return JSON.stringify({none:1});const r=a.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2,href:a.getAttribute('href')})})()`));
  if (acc.none) console.log('   本轮回答没带配饰编号');
  else {
    await clickAt(acc.x, acc.y, 5000);
    console.log('   目标 ' + acc.href + ' → ' + await ev(`JSON.stringify({url:location.href,含褙子:document.body.innerText.includes('褙子'),正文前100:document.body.innerText.replace(/\\s+/g,' ').slice(0,100)})`));
    await shot('01_accessory_landing');
  }

  console.log('== 3) 面料详情 /fabric/1');
  await send('Page.navigate', { url: base + '/fabric/1' });
  await sleep(4000);
  console.log('   ' + await ev(`JSON.stringify({标题:(document.querySelector('.detail-main h2')||{}).innerText||'无',含编号:document.body.innerText.includes('面料-0001')})`));
  await shot('02_fabric_detail');

  console.log('== 4) 纹样详情 /pattern/1');
  await send('Page.navigate', { url: base + '/pattern/1' });
  await sleep(4000);
  console.log('   ' + await ev(`JSON.stringify({标题行:(document.querySelector('.p-modal-title-row')||{}).innerText.replace(/\\s+/g,' ')||'无',含编号:document.body.innerText.includes('纹样-0088')})`));
  await shot('03_pattern_detail');

  console.log('== 5) 390x844 带对话：编号是否溢出');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4500);
  console.log('   ' + await ev(`JSON.stringify({innerWidth:innerWidth,滚动宽:document.scrollingElement.scrollWidth,溢出:document.scrollingElement.scrollWidth>innerWidth+1,编号数:document.querySelectorAll('.code-ref').length,越界数:[...document.querySelectorAll('.code-ref')].filter(e=>e.getBoundingClientRect().right>innerWidth).length})`));
  await shot('04_mobile_390');

  console.log('== 6) 控制台错误：' + JSON.stringify(errs.slice(0, 6)));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
