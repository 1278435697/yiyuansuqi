// 全量「原图被裁」复核：主站四处 + 衣冠全部 93 条详情，逐页统计
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = process.argv[2] || 'http://localhost:5278';
const PORT = Number(process.argv[3] || 9582);

const PROBE = `(()=>{
  const out=[]; let imgs=0, loaded=0;
  for (const img of document.querySelectorAll('img')) {
    imgs++;
    const cs=getComputedStyle(img);
    if (img.naturalWidth && img.naturalHeight) loaded++;
    if (cs.objectFit !== 'cover') continue;
    const r=img.getBoundingClientRect();
    if (r.width<1||r.height<1||!img.naturalWidth||!img.naturalHeight) continue;
    const nr=img.naturalWidth/img.naturalHeight, rr=r.width/r.height;
    const keep=Math.min(nr/rr, rr/nr);
    if (keep>0.985) continue;
    out.push({选择器:(img.className||'(无class)')+' ← '+(img.parentElement?img.parentElement.className:''),
      盒:Math.round(r.width)+'x'+Math.round(r.height), 原图:img.naturalWidth+'x'+img.naturalHeight,
      保留:Math.round(keep*100), src:(img.currentSrc||img.src).split('/').pop().slice(0,28)});
  }
  return JSON.stringify({被裁:out, 图数:imgs, 已加载:loaded});
})()`;

async function main() {
  const outDir = __dirname + '/audit/crop_full';
  fs.mkdirSync(outDir, { recursive: true });
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/ysfull' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 160);
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });

  const scan = async () => {
    // 先把懒加载全部叫醒，再一路滚到真正的底，避免未加载图被跳过造成假绿
    await ev(`document.querySelectorAll('img[loading]').forEach(i=>{i.loading='eager'})`);
    let y = -1, guard = 0;
    while (y !== Number(await ev('window.scrollY')) && guard++ < 90) {
      await ev(`window.scrollBy(0, 1200)`);
      await sleep(130);
      y = Number(await ev('window.scrollY'));
    }
    await sleep(1500);
    try { return JSON.parse(await ev(PROBE)); } catch (e) { return { 被裁: [], 图数: -1, 已加载: -1 }; }
  };

  const result = {};
  const pages = [
    ['档案列表', BASE + '/archive'], ['档案详情', BASE + '/archive/7'], ['档案详情2', BASE + '/archive/1'],
    ['面料列表', BASE + '/fabric'], ['面料详情', BASE + '/fabric/11'], ['面料详情2', BASE + '/fabric/1'],
    ['纹样列表', BASE + '/pattern'], ['纹样详情', BASE + '/pattern/32'], ['纹样详情2', BASE + '/pattern/1'],
    ['纹样详情3', BASE + '/pattern/24'],
  ];
  for (const [name, url] of pages) {
    await send('Page.navigate', { url });
    await sleep(4200);
    result[name] = await scan();
    console.log('== ' + name + ' 被裁 ' + result[name].被裁.length + '（图上 ' + result[name].图数 + ' / 已加载 ' + result[name].已加载 + '）');
    result[name].被裁.forEach(x => console.log('   ' + JSON.stringify(x)));
  }

  // 衣冠：一次加载，遍历全部 93 条
  await send('Page.navigate', { url: BASE + '/accessories/index.html' });
  await sleep(4000);
  result['衣冠首页'] = await scan();
  console.log('== 衣冠首页 被裁 ' + result['衣冠首页'].被裁.length + '（图上 ' + result['衣冠首页'].图数 + '）');
  const ids = JSON.parse(await ev(`JSON.stringify((window.ACCESSORIES||[]).map(e=>e.id))`));
  console.log('   衣冠条目 ' + ids.length + ' 条，逐条走查');
  let accTotal = 0, bad = [];
  for (const one of ids) {
    await ev(`location.hash = '#/a/' + encodeURIComponent(${JSON.stringify(one)}); window.scrollTo(0,0)`);
    await sleep(700);
    const arr = await scan();
    accTotal += arr.被裁.length;
    if (arr.被裁.length) { bad.push([one, arr]); console.log('   ' + one + ' 被裁 ' + arr.被裁.length + '：' + JSON.stringify(arr.被裁.slice(0, 3))); }
  }
  console.log('== 衣冠全部详情 被裁合计 ' + accTotal + '（条目 ' + ids.length + '）');
  fs.writeFileSync(outDir + '/census.json', JSON.stringify({ 主站: result, 衣冠被裁条目: bad }, null, 1));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
