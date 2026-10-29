// 图片自适应改后实测：同一套页跑「被 cover 裁掉的图」计数 + 版面/溢出检查 + 截图
// 用法：node probe_fit.js <base> <标签>
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROBE = `(()=>{
  const out=[]; let total=0;
  for (const img of document.querySelectorAll('img')) {
    const cs=getComputedStyle(img);
    const r=img.getBoundingClientRect();
    if (r.width<1||r.height<1||!img.naturalWidth||!img.naturalHeight) continue;
    total++;
    if (cs.objectFit!=='cover') continue;
    const nr=img.naturalWidth/img.naturalHeight, rr=r.width/r.height;
    const keep=Math.min(nr/rr, rr/nr);
    if (keep>0.985) continue;
    out.push({类:img.className||'(无class)', 父:(img.parentElement||{}).className||'', 盒:Math.round(r.width)+'x'+Math.round(r.height),
      原图:img.naturalWidth+'x'+img.naturalHeight, keep:Math.round(keep*100), src:(img.currentSrc||img.src).split('/').pop().slice(0,34)});
  }
  out.sort((a,b)=>a.keep-b.keep);
  return JSON.stringify({图数:total, 被裁:out.length, 明细:out});
})()`;

const LAYOUT = `(()=>{
  const de=document.scrollingElement;
  const card=document.querySelector('.costume-card,.fabric-card,.pattern-card,.acc-card');
  const img=card?card.querySelector('img'):null;
  return JSON.stringify({
    innerWidth:innerWidth, 滚动宽:de.scrollWidth, 溢出:de.scrollWidth>innerWidth+1,
    页高:de.scrollHeight,
    卡盒:card?Math.round(card.getBoundingClientRect().width)+'x'+Math.round(card.getBoundingClientRect().height):'—',
    图盒:img?Math.round(img.getBoundingClientRect().width)+'x'+Math.round(img.getBoundingClientRect().height):'—',
    图fit:img?getComputedStyle(img).objectFit:'—'
  });
})()`;

async function main() {
  const BASE = process.argv[2] || 'http://localhost:5277';
  const TAG = process.argv[3] || 'after';
  const outDir = __dirname + '/audit/fit_' + TAG;
  fs.mkdirSync(outDir, { recursive: true });
  const port = Number(process.argv[4] || 9531);
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysfit' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errs.push(m.params.entry.text.slice(0, 130));
  };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 160);
    return r.result.result.value;
  };
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 60 }); if (r.result && r.result.data) fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); };
  await send('Page.enable', {}); await send('Runtime.enable', {}); await send('Log.enable', {});

  const pages = [
    ['档案列表', '/archive'], ['档案详情', '/archive/7'],
    ['面料列表', '/fabric'], ['面料详情', '/fabric/11'],
    ['纹样列表', '/pattern'], ['纹样详情', '/pattern/32'],
    ['衣冠首页', '/accessories/index.html'],
    ['衣冠详情', '/accessories/index.html#/a/%E5%A4%B4%E9%A5%B0-04'],
  ];
  const rep = {};

  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  for (const [name, path] of pages) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(4300);
    await ev(`window.scrollTo(0, 600)`); await sleep(400); await ev(`window.scrollTo(0, 0)`); await sleep(400);
    const d = JSON.parse(await ev(PROBE));
    const l = await ev(LAYOUT);
    rep[name] = { 图数: d.图数, 被裁: d.被裁, 版面: l, 最差: d.明细.slice(0, 4) };
    console.log('== ' + name + ' 图' + d.图数 + ' 被裁' + d.被裁 + ' | ' + l);
    for (const one of d.明细.slice(0, 4)) console.log('     ' + JSON.stringify(one));
    await shot('1440_' + name);
  }

  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: false });
  console.log('-- 390 视口 --');
  for (const [name, path] of [['档案列表', '/archive'], ['纹样列表', '/pattern'], ['衣冠首页', '/accessories/index.html']]) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(4300);
    const l = await ev(LAYOUT);
    rep['390_' + name] = l;
    console.log('== 390 ' + name + ' | ' + l);
    await shot('390_' + name);
  }

  rep.控制台错误 = errs.slice(0, 8);
  fs.writeFileSync(outDir + '/report.json', JSON.stringify(rep, null, 1));
  console.log('截图与报告在 ' + outDir);
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
