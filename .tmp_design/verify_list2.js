// 列表卡图点击：整卡跳转；同时回归未改页面的全局放大仍可用
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const STATE = `JSON.stringify({路径:location.pathname,本页灯箱:!!document.querySelector(".el-image-viewer__wrapper"),全局单图:!!document.querySelector(".ys-lightbox")})`;

async function main() {
  const port = 9418;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yslist' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); if (r.result.exceptionDetails) return 'EXC'; return r.result.result.value; };
  const clickAt = async (x, y, w = 1000) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  const tap = async (label, sel) => {
    const ok = await ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(!e)return "NO";e.scrollIntoView({block:"center"});return "ok"})()`);
    if (ok === 'NO') { console.log(label.padEnd(22), '无此元素'); return; }
    await sleep(800);
    const q = JSON.parse(await ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});var r=e.getBoundingClientRect();var x=(r.x+r.width/2)|0,y=(r.y+r.height/2)|0;var h=document.elementFromPoint(x,y);return JSON.stringify({x:x,y:y,hit:h?h.tagName+"."+String(h.className||"").split(" ")[0]:"none"})})()`));
    await clickAt(q.x, q.y);
    console.log(label.padEnd(22), '命中 ' + q.hit, ' ->', await ev(STATE));
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  await send('Page.navigate', { url: process.argv[2] + "/fabric" });
  await sleep(5000);
  console.log('== 面料列表（未改，作对照）==');
  await tap('面料卡·图', '.fabric-card img');
  await ev('history.back()'); await sleep(1200);
  ''
  ws.close(); child.kill();
}
main();
