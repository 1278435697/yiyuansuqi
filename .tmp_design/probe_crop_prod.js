// 图片裁切取证：逐页列出「被 cover 裁掉」的图，给渲染比例 vs 原图比例
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = 'http://47.93.14.11';

const PROBE = `(()=>{
  const out=[];
  for (const img of document.querySelectorAll('img')) {
    const cs=getComputedStyle(img);
    if (cs.objectFit !== 'cover') continue;
    const r=img.getBoundingClientRect();
    if (r.width<1 || r.height<1 || !img.naturalWidth || !img.naturalHeight) continue;
    const nr=img.naturalWidth/img.naturalHeight, rr=r.width/r.height;
    const keep=Math.min(nr/rr, rr/nr);
    out.push({类:img.className||'(无class)', 父:(img.parentElement||{}).className||'', 盒:Math.round(r.width)+'x'+Math.round(r.height),
      原图:img.naturalWidth+'x'+img.naturalHeight, 保留N:keep, 保留:Math.round(keep*100)+'%', src:(img.currentSrc||img.src).split('/').pop().slice(0,40)});
  }
  out.sort((a,b)=>a.保留N-b.保留N);
  return JSON.stringify(out);
})()`;

async function main() {
  const port = 9520;
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
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 160);
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  const pages = [
    ['档案·列表', BASE + '/archive'],
    ['档案·详情 褙子', BASE + '/archive/7'],
    ['面料·列表', BASE + '/fabric'],
    ['面料·详情 妆花缎', BASE + '/fabric/11'],
    ['纹样·列表', BASE + '/pattern'],
    ['纹样·详情 回纹', BASE + '/pattern/32'],
    ['衣冠·首页', BASE + '/accessories/index.html'],
    ['衣冠·详情 衣制-07', BASE + '/accessories/index.html#/a/%E8%A1%A3%E5%88%B6-07'],
    ['衣冠·详情 头饰-04', BASE + '/accessories/index.html#/a/%E5%A4%B4%E9%A5%B0-04'],
  ];
  const report = {};
  for (const [name, url] of pages) {
    await send('Page.navigate', { url });
    await sleep(name.startsWith('衣冠') ? 4500 : 4200);
    await ev(`window.scrollTo(0, document.body.scrollHeight)`); await sleep(700);
    await ev(`window.scrollTo(0, 0)`); await sleep(500);
    const raw = await ev(PROBE);
    let arr = [];
    try { arr = JSON.parse(raw); } catch (e) { console.log(name + ' 探测失败: ' + String(raw).slice(0, 120)); }
    report[name] = arr;
    console.log('== ' + name + '  被裁图 ' + arr.length + ' 张');
    for (const one of arr.slice(0, 12)) console.log('   ' + JSON.stringify(one));
  }
  fs.writeFileSync(__dirname + '/audit/fit_prod.json', JSON.stringify(report, null, 1));
  console.log('已写 audit/fit_prod.json');
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
