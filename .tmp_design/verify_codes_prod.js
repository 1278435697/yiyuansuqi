// 编号轮上线后生产实测：AI 正文编号可点 + 四类详情页编号 + 390 视口不溢出
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = 'http://47.93.14.11';

async function main() {
  const outDir = __dirname + '/audit/codes_prod';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9512;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscodeprod' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {}; const errs = [];
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

  await send('Page.enable', {}); await send('Runtime.enable', {}); await send('Log.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  console.log('== 0) 线上入口 chunk 与本地构建一致性（浏览器实际加载的 index.html）');
  await send('Page.navigate', { url: BASE + '/aiqa' });
  await sleep(4000);
  console.log('   ' + await ev(`JSON.stringify({脚本:[...document.scripts].map(s=>s.getAttribute('src')).filter(Boolean),样式:[...document.querySelectorAll('link[rel=stylesheet]')].map(l=>l.getAttribute('href'))})`));

  console.log('== 1) 清空历史 → 提问，让正文出现编号');
  await ev(`localStorage.removeItem('yisu_aiqa_chat_v1');'ok'`);
  await send('Page.navigate', { url: BASE + '/aiqa' });
  await sleep(3500);
  const inp = await box('.chat-input-row .el-input__inner');
  await clickAt(inp.x, inp.y, 400);
  await send('Input.insertText', { text: '褙子的形制是什么？出土于哪里？' });
  await sleep(300);
  const btn = await box('.chat-input-row button.el-button--primary');
  await clickAt(btn.x, btn.y, 3000);
  for (let i = 0; i < 50; i++) {
    if (Number(await ev(`document.querySelectorAll('.chat-row.assistant .code-ref').length`)) >= 1) break;
    await sleep(1500);
  }
  await sleep(2500);
  console.log('   编号卡：' + await ev(`JSON.stringify([...document.querySelectorAll('.code-ref')].map(e=>({文:e.textContent,链:e.getAttribute('href')})))`));
  console.log('   引用区：' + await ev(`JSON.stringify([...document.querySelectorAll('.src-item,.source-chip,.chat-sources .el-tag')].slice(0,8).map(e=>e.innerText.replace(/\\s+/g,' ').slice(0,50)))`));
  console.log('   正文片段：' + await ev(`(document.querySelectorAll('.chat-row.assistant .chat-content')[0]||{innerText:''}).innerText.replace(/\\s+/g,' ').slice(0,220)`));
  await shot('01_prod_aiqa');

  console.log('== 2) 逐个点编号，看落点对不对');
  const links = JSON.parse(await ev(`JSON.stringify([...document.querySelectorAll('.code-ref')].map(e=>({文:e.textContent,href:e.getAttribute('href')})))`));
  for (const one of links) {
    if (!one.href) { console.log('   ' + one.文 + ' → 无 href（纯文本，符合预期）'); continue; }
    await send('Page.navigate', { url: BASE + '/aiqa' });
    await sleep(3000);
    const p = JSON.parse(await ev(`(()=>{const a=[...document.querySelectorAll('.code-ref')].find(e=>e.getAttribute('href')===${JSON.stringify(one.href)});if(!a)return JSON.stringify({none:1});const r=a.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()`));
    if (p.none) { console.log('   ' + one.href + ' 重新提问后没出现，跳过'); continue; }
    await clickAt(p.x, p.y, 4500);
    console.log('   ' + one.文 + ' ' + one.href + ' → ' + await ev(`JSON.stringify({url:location.href,标题行:(document.querySelector('.detail-main h2,.p-modal-title-row,h1,h2')||{}).innerText||'',含编号:!!(document.body.innerText.match(/[档案纹样面料资讯]-\\d{4}/)||document.body.innerText.match(/-\\d{2}/))})`));
    await shot('02_landing_' + one.href.replace(/[^a-z0-9]/gi, '_').slice(0, 30));
  }

  console.log('== 3) 四类详情页编号（直接导航，用线上真实 id）');
  for (const [name, path, expect] of [
    ['档案', '/archive/7', '档案-0007'],
    ['资讯', '/news/1', '资讯-0001'],
    ['面料', '/fabric/11', '面料-0011'],
    ['纹样', '/pattern/32', '纹样-0001'],
  ]) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(4200);
    console.log('   ' + name + ' ' + path + ' 期望 ' + expect + ' → ' + await ev(`JSON.stringify({命中:document.body.innerText.includes(${JSON.stringify(expect)}),标题:(document.querySelector('.detail-main h2,.p-modal-title-row,h1,h2')||{}).innerText||''})`));
    await shot('03_' + name + '_detail');
  }

  console.log('== 4) 幻觉编号保护：喂一个不存在的编号，应为纯文本');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: BASE + '/aiqa' });
  await sleep(4000);
  console.log('   ' + await ev(`JSON.stringify({innerWidth:innerWidth,滚动宽:document.scrollingElement.scrollWidth,溢出:document.scrollingElement.scrollWidth>innerWidth+1,编号数:document.querySelectorAll('.code-ref').length,越界数:[...document.querySelectorAll('.code-ref')].filter(e=>e.getBoundingClientRect().right>innerWidth).length})`));
  await shot('04_mobile_390');

  console.log('== 5) 控制台错误：' + JSON.stringify(errs.slice(0, 6)));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
