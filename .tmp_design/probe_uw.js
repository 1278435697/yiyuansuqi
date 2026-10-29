// 用户作品卡在生产库里没有数据渲染不出来，直接注入同 scoped 属性的元素实测这条 CSS
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const PORT = Number(process.argv[3] || 9605);

const BUILD = (src) => `(()=>{
  const host=document.querySelector('main')||document.querySelector('#app');
  // 把页面上出现过的全部 scoped 属性都挂上去，确保命中视图自己的 data-v
  const vs=new Set();
  for (const el of host.querySelectorAll('*')) for (const a of el.attributes) if (a.name.startsWith('data-v-')) vs.add(a.name);
  const grid=document.createElement('div'); grid.className='uw-grid';
  for (const v of vs) grid.setAttribute(v,'');
  for (const u of ${JSON.stringify(src)}) {
    const card=document.createElement('div'); card.className='uw-card';
    for (const v of vs) card.setAttribute(v,'');
    const img=document.createElement('img'); img.src=u;
    for (const v of vs) img.setAttribute(v,'');
    card.appendChild(img); grid.appendChild(card);
  }
  host.appendChild(grid);
  return new Promise(r=>setTimeout(()=>{
    const out=[];
    for (const img of grid.querySelectorAll('img')) {
      const b=img.getBoundingClientRect();
      const nr=img.naturalWidth/img.naturalHeight, rr=b.width/b.height;
      out.push({原图:img.naturalWidth+'x'+img.naturalHeight, 盒:Math.round(b.width)+'x'+Math.round(b.height),
        fit:getComputedStyle(img).objectFit, 保留:Math.round(Math.min(nr/rr, rr/nr)*100)});
    }
    r(JSON.stringify({挂上作用域:vs.size, 结果:out, 横向溢出:document.documentElement.scrollWidth-window.innerWidth}));
  }, 2500));
})()`;

async function main() {
  const dir = __dirname + '/audit/fit_uw';
  fs.mkdirSync(dir, { recursive: true });
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ysuw' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || '').slice(0, 200);
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  const pages = [['档案', '/archive'], ['面料', '/fabric'], ['纹样', '/pattern']];
  for (const [name, path] of pages) {
    await send('Page.navigate', { url: process.argv[2] + path });
    await sleep(4200);
    const list = JSON.parse(await ev(`JSON.stringify([...document.querySelectorAll('img')].map(i=>i.currentSrc||i.src).filter(s=>/^http/.test(s)).slice(0,4))`));
    if (!list.length) { console.log(name + ' 页面上取不到可用图片 URL，跳过'); continue; }
    console.log(name + ' → ' + await ev(BUILD(list)));
    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 70 });
    fs.writeFileSync(dir + '/uw_' + encodeURIComponent(name) + '.jpg', Buffer.from(shot.result.data, 'base64'));
  }
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
