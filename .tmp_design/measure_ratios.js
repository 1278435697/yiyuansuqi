// 三库封面图的原图长宽比分布 → 用数据选定比例容器，而不是拍脑袋
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const P = 'http://47.93.14.11';

async function main() {
  const port = 9540;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysratio' + port, 'about:blank'], { stdio: 'ignore' });
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
  await send('Page.navigate', { url: P + '/' });
  await sleep(3500);

  const sets = {
    档案: `((await (await fetch('/api/archive/costumes?limit=300')).json()).items||[]).map(i=>i.image_url).filter(Boolean)`,
    面料: `((await (await fetch('/api/fabrics/list?limit=300')).json()).items||[]).map(i=>i.image_url).filter(Boolean)`,
    纹样: `((await (await fetch('/api/pattern-library/items?limit=400')).json()).items||[]).map(i=>i.image_url).filter(Boolean)`,
    衣冠: `(await (await fetch('/api/accessories?limit=200')).json()).items.map(i=>i.photo).filter(Boolean)`,
  };
  const all = {};
  for (const [name, expr] of Object.entries(sets)) {
    const raw = await ev(`(async()=>{const urls=${expr};
      const ratio=await Promise.all(urls.map(u=>new Promise(res=>{const im=new Image();
        im.onload=()=>res(im.naturalWidth/im.naturalHeight); im.onerror=()=>res(null); im.src=u;})));
      return JSON.stringify(ratio.filter(Boolean));})()`);
    const arr = JSON.parse(raw).sort((a, b) => a - b);
    const q = p => arr[Math.min(arr.length - 1, Math.floor(arr.length * p))];
    // 对每个候选容器比例，算 contain 后的「空白占比」均值（越小越贴）
    const waste = r => arr.reduce((s, x) => { const cr = Math.min(x / r, r / x); return s + (1 - cr); }, 0) / arr.length;
    const worst = r => Math.max(...arr.map(x => 1 - Math.min(x / r, r / x)));
    const cands = ['1/1', '6/5', '5/4', '4/3', '3/2', '16/10', '8/5', '5/3', '2/1'];
    const scores = cands.map(c => { const [w, h] = c.split('/').map(Number); return c + ' 空' + Math.round(waste(w / h) * 100) + '/最差' + Math.round(worst(w / h) * 100); });
    all[name] = { n: arr.length, 比例: arr.map(x => +x.toFixed(3)), p10: +q(0.1).toFixed(2), 中位: +q(0.5).toFixed(2), p90: +q(0.9).toFixed(2), min: +arr[0].toFixed(2), max: +arr[arr.length - 1].toFixed(2), scores };
    console.log(name + ' ' + JSON.stringify(all[name]));
  }
  fs.writeFileSync(__dirname + '/audit/ratios.json', JSON.stringify(all, null, 1));
  ws.close(); child.kill();
}
main().catch(e => { console.error('FAIL', e); process.exit(1); });
