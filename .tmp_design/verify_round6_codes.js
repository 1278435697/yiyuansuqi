// 编号轮实测：答案正文〔编号〕可点、点进站内详情、配饰编号走站外、详情页显示编号、390 不溢出
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/codes_round';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9491;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscode' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };
  const ask = async (q) => {
    const inp = await box('.chat-input-row .el-input__inner');
    await clickAt(inp.x, inp.y, 400);
    await send('Input.insertText', { text: q });
    await sleep(300);
    const btn = await box('.chat-input-row button.el-button--primary');
    await clickAt(btn.x, btn.y, 3000);
    for (let i = 0; i < 45; i++) {
      if (Number(await ev(`document.querySelectorAll('.chat-row.assistant .chat-content').length`)) >= 1) break;
      await sleep(1500);
    }
    await sleep(4000);
  };
  const STATE = `JSON.stringify({
    正文编号: [...document.querySelectorAll('.chat-row.assistant .chat-content .code-ref')].map(e=>({文:e.textContent,链:e.getAttribute('href')})),
    正文原文: [...document.querySelectorAll('.chat-row.assistant .chat-content')].map(e=>e.innerText.replace(/\\s+/g,' ').slice(0,200)),
    引用chip: [...document.querySelectorAll('.src-chip')].map(e=>({文:e.textContent.trim(),链:e.getAttribute('href')})),
    路由: location.pathname,
    编号文案: [...document.querySelectorAll('h1,h2,.detail-meta')].map(e=>e.innerText.replace(/\\s+/g,' ')).filter(t=>t.includes('编号')).slice(0,3)
  })`;

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  console.log('== 1) /aiqa 提问「褙子的形制是什么？出土于哪里？」');
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3500);
  await ev(`localStorage.removeItem('yisu_aiqa_chat_v1');localStorage.removeItem('yisu_aiqa_webqa_v1');'ok'`);
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(3000);
  await ask('褙子的形制是什么？出土于哪里？');
  console.log('   ' + await ev(STATE));
  await shot('01_answer_codes');

  console.log('== 2) 点正文里第一个站内编号');
  const first = JSON.parse(await ev(`(()=>{const a=[...document.querySelectorAll('.chat-row.assistant .chat-content .code-ref')].find(e=>/^\\/(archive|news|fabric|pattern)/.test(e.getAttribute('href')||''));if(!a)return JSON.stringify({none:1});const r=a.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2,href:a.getAttribute('href'),文:a.textContent})})()`));
  if (first.none) console.log('   没有站内编号可点');
  else {
    console.log('   目标 ' + first.href + ' ' + first.文);
    await clickAt(first.x, first.y, 3000);
    console.log('   ' + await ev(STATE));
    await shot('02_after_code_click');
  }

  console.log('== 3) 配饰编号外链（站外子站，只验 href 与新窗口属性）');
  console.log('   ' + await ev(`JSON.stringify([...document.querySelectorAll('.code-ref')].map(e=>({文:e.textContent,链:e.getAttribute('href'),target:e.getAttribute('target')})))`));

  console.log('== 4) 详情页显示编号：/archive/7 · /news/4 · /fabric');
  for (const p of ['/archive/7', '/news/4', '/fabric']) {
    await send('Page.navigate', { url: base + p });
    await sleep(3000);
    console.log('   ' + p + ' → ' + await ev(`JSON.stringify({含编号:document.body.innerText.includes('编号'),片段:[...document.querySelectorAll('h1,h2,.detail-meta,.dynasty')].map(e=>e.innerText.replace(/\\s+/g,' ')).filter(t=>t.includes('编号')).slice(0,2)})`));
    await shot('03_detail' + p.replace(/\//g, '_'));
  }

  console.log('== 5) 390x844 视口');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4000);
  console.log('   ' + await ev(`JSON.stringify({横向滚动宽:document.scrollingElement.scrollWidth,视口:innerWidth,编号数:document.querySelectorAll('.code-ref').length,气泡宽:Math.round((document.querySelector('.chat-bubble')||{getBoundingClientRect:()=>({width:0})}).getBoundingClientRect().width)})`));
  await shot('04_mobile_390');

  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
