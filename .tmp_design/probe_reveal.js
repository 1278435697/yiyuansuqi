// 点开档案/面料列表卡触发 SplitReveal 揭示层，量里面的图还裁不裁
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = process.argv[2] || 'http://localhost:5278';
const PORT = Number(process.argv[3] || 9610);

const MEASURE = `(()=>{
  const out=[];
  for (const img of document.querySelectorAll('.sr-img img')) {
    const b=img.getBoundingClientRect();
    if (!img.naturalWidth) { out.push({原图:'未加载'}); continue; }
    const nr=img.naturalWidth/img.naturalHeight, rr=b.width/b.height;
    out.push({原图:img.naturalWidth+'x'+img.naturalHeight, 盒:Math.round(b.width)+'x'+Math.round(b.height),
      fit:getComputedStyle(img).objectFit, 保留:Math.round(Math.min(nr/rr, rr/nr)*100)});
  }
  return JSON.stringify({层:!!document.querySelector('.sr-mask'), 图:out});
})()`;

async function main() {
  const dir = __dirname + '/audit/fit_reveal';
  fs.mkdirSync(dir, { recursive: true });
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ysrv' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || '').slice(0, 160);
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  for (const [name, path, sel] of [['档案', '/archive', '.costume-card'], ['面料', '/fabric', '.fabric-card']]) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(7000);
    const box = JSON.parse(await ev(`(()=>{const el=document.querySelector(${JSON.stringify(sel)}); if(!el) return 'null'; const r=el.getBoundingClientRect(); return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()`));
    if (!box || box === "null") { console.log(name + " 找不到卡片，页面上卡片类名=" + await ev("JSON.stringify([...document.querySelectorAll('[class*=card]')].slice(0,6).map(e=>e.className))")); continue; }
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: box.x, y: box.y, button: 'left', clickCount: 1, buttons: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: box.x, y: box.y, button: 'left', clickCount: 1 });
    await sleep(2600);
    if (!(await ev(`!!document.querySelector('.sr-mask')`))) {
      // 坐标点击没命中（可能被吸顶导航压住），滚到卡片中缝再点一次，最后退化为 el.click()
      await ev(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({block:'center'})`);
      await sleep(900);
      const b2 = JSON.parse(await ev(`(()=>{const r=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()`));
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: b2.x, y: b2.y, button: 'left', clickCount: 1, buttons: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: b2.x, y: b2.y, button: 'left', clickCount: 1 });
      await sleep(2200);
      if (!(await ev(`!!document.querySelector('.sr-mask')`))) { await ev(`document.querySelector(${JSON.stringify(sel)}).click()`); await sleep(2200); }
    }
    console.log('== ' + name + ' 揭示层 ' + await ev(MEASURE));
    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 70 });
    fs.writeFileSync(dir + '/reveal_' + encodeURIComponent(name) + '.jpg', Buffer.from(shot.result.data, 'base64'));
  }
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
