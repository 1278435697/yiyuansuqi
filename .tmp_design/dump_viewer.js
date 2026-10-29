// 用真实类名复测：真鼠标点主图 → 到底开了哪个覆盖层？含哪些控件？
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const DUMP = `
(function(){
  var names={};
  document.querySelectorAll("[class]").forEach(function(el){
    String(el.className).split(/\\s+/).forEach(function(c){
      if(/viewer|lightbox|lb-/.test(c)) names[c]=(names[c]||0)+1;
    });
  });
  var v=document.querySelector(".el-image-viewer__wrapper");
  var imgs=v?v.querySelectorAll("img").length:0;
  return JSON.stringify({classes:Object.keys(names).sort(),viewerOpen:!!v,viewerImgs:imgs,
    globalLb:!!document.querySelector(".ys-lightbox"),
    curSrc:(function(){var i=document.querySelector(".el-image-viewer__canvas img");return i?i.src.slice(-12):""})()});
})()
`;

async function main() {
  const port = 9414;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysdump' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  if (!ws) { console.log('NO WS'); child.kill(); return; }
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC: ' + JSON.stringify(r.result.exceptionDetails.exception || r.result.exceptionDetails.text);
    return r.result.result.value;
  };
  const clickAt = async (x, y) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(700);
  };
  const ctr = (sel) => ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`);

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: process.argv[2] });
  await sleep(4500);
  console.log('初始   ', await ev(DUMP));
  const a = JSON.parse(await ctr('.img-col img'));
  await clickAt(a.x, a.y);
  console.log('点主图 ', await ev(DUMP));
  for (let i = 1; i <= 3; i++) {
    const n = await ctr('.el-image-viewer__next');
    if (n === 'NO') { console.log('无右箭头'); break; }
    const q = JSON.parse(n); await clickAt(q.x, q.y);
    console.log('右箭头' + i + ' ', await ev(DUMP));
  }
  const prev = await ctr('.el-image-viewer__prev');
  if (prev !== 'NO') { const q = JSON.parse(prev); await clickAt(q.x, q.y); console.log('左箭头 ', await ev(DUMP)); }
  // 关闭按钮
  const cl = await ctr('.el-image-viewer__close');
  console.log('关闭按钮', cl === 'NO' ? '未找到' : '已找到');
  if (cl !== 'NO') { const q = JSON.parse(cl); await clickAt(q.x, q.y); console.log('关闭后 ', await ev(DUMP)); }
  // 全局灯箱是否仍服务其它图片：去列表页点一张卡图
  await send('Page.navigate', { url: process.argv[3] });
  await sleep(4000);
  const g = await ctr('.pattern-card img, .card img, .ys-card img');
  console.log('列表图坐标', g);
  if (g !== 'NO') { const q = JSON.parse(g); await clickAt(q.x, q.y); console.log('点列表图 ', await ev(DUMP)); }
  ws.close(); child.kill();
}
main();
