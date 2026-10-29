// 编号轮补测：配饰编号点进子站详情 · 面料/纹样详情编号 · 390 视口精确复测
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/codes_round2';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9493;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscode2' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  const events = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; }
    if (m.method === 'Log.entryAdded') events.push(m.params.entry.level + ' ' + m.params.entry.text.slice(0, 120));
    if (m.method === 'Runtime.consoleAPICalled') events.push(m.params.type + ' ' + JSON.stringify(m.params.args).slice(0, 120));
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

  console.log('== 1) 回 /aiqa（对话存 localStorage），点配饰编号 〔衣制-07〕');
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4000);
  const acc = JSON.parse(await ev(`(()=>{const a=[...document.querySelectorAll('.code-ref')].find(e=>(e.getAttribute('href')||'').startsWith('/accessories'));if(!a)return JSON.stringify({none:1});const r=a.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2,href:a.getAttribute('href'),文:a.textContent,target:a.getAttribute('target')})})()`));
  console.log('   配饰编号 ' + JSON.stringify(acc));
  if (!acc.none) {
    await clickAt(acc.x, acc.y, 4500);
    console.log('   落地 ' + await ev(`JSON.stringify({url:location.href,hash:location.hash,含褙子:document.body.innerText.includes('褙子'),正文前80:document.body.innerText.replace(/\\s+/g,' ').slice(0,80)})`));
    await shot('01_accessory_landing');
  }

  console.log('== 2) 面料详情编号 /fabric/{id}');
  await send('Page.navigate', { url: base + '/fabric' });
  await sleep(3500);
  const fabId = await ev(`(async()=>{const r=await fetch('/api/fabrics/list');const j=await r.json();return j.items.length?String(j.items[0].id):'0'})()`);
  console.log('   本地面料 id=' + fabId);
  if (fabId !== '0') {
    await send('Page.navigate', { url: base + '/fabric/' + fabId });
    await sleep(3500);
    console.log('   ' + await ev(`JSON.stringify({标题:(document.querySelector('.detail-main h2')||{}).innerText||'',含编号:document.body.innerText.includes('编号')})`));
    await shot('02_fabric_detail');
  }

  console.log('== 3) 纹样详情编号 /pattern/{id}');
  await send('Page.navigate', { url: base + '/pattern' });
  await sleep(3500);
  const patId = await ev(`(async()=>{const r=await fetch('/api/pattern-library/items');const j=await r.json();return j.items.length?String(j.items[0].id):'0'})()`);
  console.log('   本地纹样 id=' + patId);
  if (patId !== '0') {
    await send('Page.navigate', { url: base + '/pattern/' + patId });
    await sleep(3500);
    console.log('   ' + await ev(`JSON.stringify({标题行:(document.querySelector('.p-modal-title-row')||{}).innerText||'',含编号:document.body.innerText.includes('编号')})`));
    await shot('03_pattern_detail');
  }

  console.log('== 4) 390x844 精确复视口');
  await send('Page.navigate', { url: base + '/aiqa' });
  await sleep(4000);
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
  await sleep(1500);
  console.log('   ' + await ev(`JSON.stringify({innerWidth:innerWidth,滚动宽:document.scrollingElement.scrollWidth,溢出:document.scrollingElement.scrollWidth>innerWidth+1,编号数:document.querySelectorAll('.code-ref').length,编号溢出元素:[...document.querySelectorAll('.code-ref')].filter(e=>e.getBoundingClientRect().right>innerWidth).length})`));
  await shot('04_mobile_390');

  console.log('== 5) 控制台报错/告警：' + JSON.stringify(events.slice(0, 8)));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
