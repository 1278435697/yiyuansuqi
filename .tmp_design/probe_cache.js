// 看清子站到底哪个资源走了缓存：Network 域逐条记录 fromDiskCache
// 用法：node probe_cache.js <port> <tag>
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const port = Number(process.argv[2] || 9561);
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysacc' + port, 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  const seen = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; }
    if (m.method === 'Network.responseReceived') {
      const r = m.params.response;
      if (/accessories\/(index\.html|app\.js|styles\.css|data\.js)/.test(r.url)) {
        seen.push(r.url.replace('http://47.93.14.11', '') + ' 状态' + r.status +
          ' 缓存=' + (r.fromDiskCache ? 'disk' : r.fromMemoryCache ? 'memory' : '回源') +
          ' CC=' + (r.headers['cache-control'] || r.headers['Cache-Control'] || '无') +
          ' LM=' + (r.headers['last-modified'] || r.headers['Last-Modified'] || '无'));
      }
    }
  };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    return r.result.result.value;
  };
  await send('Page.enable', {}); await send('Network.enable', {}); await send('Runtime.enable', {});
  await send('Page.navigate', { url: 'http://47.93.14.11/accessories/index.html' });
  await sleep(6000);
  console.log('实际请求：');
  seen.forEach(s => console.log('  ' + s));
  console.log('页面里 script 标签：' + await ev(`[...document.scripts].map(s=>s.src).filter(s=>s.includes('app.js')).join(',')||'无'`));
  console.log('首张卡 fit=' + await ev(`(()=>{const i=document.querySelector('.card-photo');return i?getComputedStyle(i).objectFit:'无卡'}())`));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
