// 手机视口干净复测：新开页面 → 真鼠标点主图 → 只应出现多图灯箱
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const DUMP = `
(function(){
  var v=document.querySelector(".el-image-viewer__wrapper");
  var i=document.querySelector(".el-image-viewer__canvas img");
  return JSON.stringify({多图灯箱:!!v, 全局单图:!!document.querySelector(".ys-lightbox"),
    右箭头:!!document.querySelector(".el-image-viewer__next"),
    左箭头:!!document.querySelector(".el-image-viewer__prev"),
    放大条:!!document.querySelector(".el-image-viewer__actions"),
    当前:i?i.src.slice(-12):""});
})()
`;

async function main() {
  const port = 9416;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysmob' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); return r.result.exceptionDetails ? 'EXC' : r.result.result.value; };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await send('Page.navigate', { url: process.argv[2] });
  await sleep(5000);
  console.log('手机初始  ', await ev(DUMP));
  const c = await ev(`(function(){var e=document.querySelector(".img-col img");if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0,top:(r.top+scrollY)|0,hit:(document.elementFromPoint((r.x+r.width/2)|0,(r.y+r.height/2)|0)||{}).className})})()`);
  console.log('主图位置  ', c);
  if (c === 'NO') { ws.close(); child.kill(); return; }
  const p = JSON.parse(c);
  if (p.top < 0 || p.top > 844) { await ev(`scrollTo(0, ${p.top - 200})`); await sleep(600); }
  const q = await ev(`(function(){var e=document.querySelector(".img-col img");var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0,hit:(document.elementFromPoint((r.x+r.width/2)|0,(r.y+r.height/2)|0)||{}).tagName})})()`);
  console.log('滚动后    ', q);
  const { x, y } = JSON.parse(q);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
  await sleep(900);
  console.log('手机点主图', await ev(DUMP));
  const n = await ev(`(function(){var e=document.querySelector(".el-image-viewer__next");if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`);
  if (n !== 'NO') {
    const m = JSON.parse(n);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: m.x, y: m.y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: m.x, y: m.y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: m.x, y: m.y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(900);
    console.log('手机右箭头', await ev(DUMP));
  }
  ws.close(); child.kill();
}
main();
