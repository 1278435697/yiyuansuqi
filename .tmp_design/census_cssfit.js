// 不依赖图片是否加载完：按 computed style 统计还配着 object-fit:cover 的 img
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = process.argv[2] || 'http://localhost:5278';
const PORT = Number(process.argv[3] || 9583);

const PROBE = `(()=>{
  const c={}, n={};
  for (const img of document.querySelectorAll('img')) {
    n.总数=(n.总数||0)+1;
    const f=getComputedStyle(img).objectFit;
    c[f]=(c[f]||0)+1;
    if (f==='cover') (n.cover列表=n.cover列表||[]).push((img.className||'(无class)')+' ← '+(img.parentElement?img.parentElement.className:'')+' | '+(img.currentSrc||img.src).split('/').pop().slice(0,24));
  }
  n.分布=c;
  return JSON.stringify(n);
})()`;

async function main() {
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PORT}`,
      '--user-data-dir=' + os.tmpdir() + '/yscss' + PORT, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || '').slice(0, 140);
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });

  const pages = [
    ['档案列表', '/archive'], ['档案详情', '/archive/7'], ['面料列表', '/fabric'], ['面料详情', '/fabric/11'],
    ['纹样列表', '/pattern'], ['纹样详情', '/pattern/32'], ['衣冠首页', '/accessories/index.html'],
    ['衣冠·头饰-04', '/accessories/index.html#/a/' + encodeURIComponent('头饰-04')],
    ['衣冠·服饰-16', '/accessories/index.html#/a/' + encodeURIComponent('服饰-16')],
    ['衣冠·随身-09', '/accessories/index.html#/a/' + encodeURIComponent('随身-09')],
    ['衣冠·衣制-07', '/accessories/index.html#/a/' + encodeURIComponent('衣制-07')],
  ];
  for (const [name, path] of pages) {
    await send('Page.navigate', { url: BASE + path });
    await sleep(3800);
    await ev(`(()=>{let h=0;return new Promise(r=>{const t=setInterval(()=>{window.scrollBy(0,1400);h+=1400;if(h>document.body.scrollHeight){clearInterval(t);r(1)}},60)})})()`);
    await sleep(1200);
    let info = {};
    try { info = JSON.parse(await ev(PROBE)); } catch (e) { console.log(name + ' 解析失败'); }
    console.log('== ' + name + ' 图 ' + (info.总数 || 0) + ' 分布 ' + JSON.stringify(info.分布 || {}));
    (info.cover列表 || []).slice(0, 8).forEach(x => console.log('     cover→ ' + x));
  }
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
