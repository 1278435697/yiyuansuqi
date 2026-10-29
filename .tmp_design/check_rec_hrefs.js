// 四类卡的 href 是否各自指向站内详情路由（注入到内存，不发请求）
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const port = 9511;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yshref' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => (await send('Runtime.evaluate', { expression: x, returnByValue: true })).result.result.value;
  const cards = [
    { type: "costume", id: 9, title: "马面裙", subtitle: "明 · 下裳", image_url: "", link: "/archive/9", exact: true },
    { type: "pattern", id: 12, title: "联珠团窠纹", subtitle: "隋唐", image_url: "", link: "/pattern/12", exact: true },
    { type: "fabric", id: 3, title: "妆花缎", subtitle: "元—明", image_url: "", link: "/fabric/3", exact: false },
    { type: "news", id: 5, title: "明代马面裙再受关注", subtitle: "宜昌博物馆", image_url: "", link: "/news/5", exact: true },
  ];
  const msgs = [{ role: "user", content: "马面裙" }, {
    role: "assistant", content: "答", ref: "", question: "马面裙",
    rec: { keywords: ["马面裙"], cards, asks: ["马面裙的形制是什么？"] },
  }];
  await send('Page.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'http://localhost:5173/aiqa' });
  await sleep(3000);
  await ev(`localStorage.setItem('yisu_aiqa_chat_v1', JSON.stringify(${JSON.stringify(msgs)}));'ok'`);
  await send('Page.navigate', { url: 'http://localhost:5173/aiqa' });
  await sleep(3000);
  console.log(await ev(`JSON.stringify([...document.querySelectorAll('.rec-card')].map(a=>[a.getAttribute('href'), a.querySelector('.rec-type').textContent.trim()]))`));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
