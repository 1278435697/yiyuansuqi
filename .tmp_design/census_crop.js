// 全站「原图被裁」清点：主站四处 + 衣冠子站多条详情，逐张列出还裁在哪
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = process.argv[2] || 'http://47.93.14.11';

const PROBE = `(()=>{
  const out=[];
  for (const img of document.querySelectorAll('img')) {
    const cs=getComputedStyle(img);
    if (cs.objectFit !== 'cover') continue;
    const r=img.getBoundingClientRect();
    if (r.width<1||r.height<1||!img.naturalWidth||!img.naturalHeight) continue;
    const nr=img.naturalWidth/img.naturalHeight, rr=r.width/r.height;
    const keep=Math.min(nr/rr, rr/nr);
    if (keep>0.985) continue;
    out.push({选择器:(img.className||'(无class)')+' ← '+(img.parentElement?img.parentElement.className:''),
      盒:Math.round(r.width)+'x'+Math.round(r.height), 原图:img.naturalWidth+'x'+img.naturalHeight,
      保留:Math.round(keep*100), src:(img.currentSrc||img.src).split('/').pop().slice(0,30)});
  }
  out.sort((a,b)=>a.保留.localeCompare?0:0);
  return JSON.stringify(out);
})()`;

async function main() {
  const outDir = __dirname + '/audit/crop_census';
  fs.mkdirSync(outDir, { recursive: true });
  const port = Number(process.argv[3] || 9581);
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yscensus' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });

  const pages = [
    ['档案列表', '/archive'], ['档案详情·褙子', '/archive/7'], ['档案详情·马面裙', '/archive/1'],
    ['面料列表', '/fabric'], ['面料详情·妆花缎', '/fabric/11'], ['面料详情·丝绢', '/fabric/1'],
    ['纹样列表', '/pattern'], ['纹样详情·回纹', '/pattern/32'], ['纹样详情·团花', '/pattern/1'],
    ['衣冠首页', '/accessories/index.html'],
  ];
  for (const n of ['头饰-04', '衣制-07', '服饰-16', '随身-09', '项饰-06']) {
    pages.push(['衣冠详情·' + n, '/accessories/index.html#/a/' + encodeURIComponent(n)]);
  }

  const tally = {};
  for (const [name, path] of pages) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(4200);
    // 滚到底把所有懒加载图都叫醒
    for (let i = 0; i < 14; i++) { await ev(`window.scrollBy(0, 900)`); await sleep(220); }
    await sleep(900);
    let arr = [];
    try { arr = JSON.parse(await ev(PROBE)); } catch (e) { console.log(name + ' 解析失败'); }
    tally[name] = arr;
    console.log('== ' + name + ' 仍被裁 ' + arr.length + ' 张');
    for (const one of arr) console.log('   ' + JSON.stringify(one));
  }
  const uniq = {};
  Object.values(tally).flat().forEach(x => { uniq[x.选择器] = (uniq[x.选择器] || 0) + 1; });
  console.log('== 归并后需要动手的选择器');
  Object.entries(uniq).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => console.log('   ' + v + ' 次  ' + k));
  fs.writeFileSync(outDir + '/census.json', JSON.stringify(tally, null, 1));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
