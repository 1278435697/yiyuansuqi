// 一次性把「点击去哪了」问清楚：真实鼠标坐标 + 全链路监听 + 事件对象细节
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const INSTALL = `
window.__log=[];
var sels=["img-col","img-row","detail-main","detail-layout"];
sels.forEach(function(sel){var el=document.querySelector("."+sel);if(!el)return;
  ["capture","bubble"].forEach(function(ph){el.addEventListener("click",function(e){
    window.__log.push(sel+"#"+ph+" tgt="+(e.target.tagName||"")+" stopped="+e.cancelBubble);
  },ph==="capture");});});
document.addEventListener("click",function(e){window.__log.push("DOC#bubble tgt="+(e.target.tagName||""));},false);
"installed";
`;

const INFO = `
(function(){
  var col=document.querySelector(".img-col"); if(!col) return "NO .img-col";
  var img=col.querySelector("img");
  var rc=col.getBoundingClientRect(), ri=img.getBoundingClientRect();
  var hit=document.elementFromPoint(ri.x+ri.width/2, ri.y+ri.height/2);
  return JSON.stringify({
    colRect:[rc.x|0,rc.y|0,rc.width|0,rc.height|0],
    imgRect:[ri.x|0,ri.y|0,ri.width|0,ri.height|0],
    scroll:[window.scrollX|0,window.scrollY|0],
    colVei:Object.keys(col._vei||{}),
    imgVei:Object.keys(img._vei||{}),
    colInvokers:Object.keys(col._vei||{}).map(function(k){return k+":"+JSON.stringify(Object.keys(col._vei[k]));}),
    inside:col.contains(img),
    hitTag:hit?hit.tagName+"."+hit.className:"none",
    badge:(document.querySelector(".count-badge")||{}).textContent,
    viewerNow:!!document.querySelector(".el-image-viewer-wrap")
  });
})()
`;

const CENTER = `
(function(){var r=document.querySelector(".img-col img").getBoundingClientRect();
 return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0});})()
`;

const LOGS = `window.__log.join("  ||  ")`;

const AFTER = `
(function(){
  var w=document.querySelector(".el-image-viewer-wrap");
  if(!w) return "灯箱未打开";
  var imgs=w.querySelectorAll("img");
  var next=document.querySelector(".el-image-viewer__next");
  return "灯箱已打开 imgs=" + imgs.length + " 右箭头=" + (next?"有":"无") + " src0=" + (imgs[0]?imgs[0].src.slice(-24):"none");
})()
`;

async function main() {
  const port = 9411;
  const args = ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
    '--user-data-dir=' + os.tmpdir() + '/ysprobe' + port, '--hide-scrollbars', 'about:blank'];
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', args, { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/list`);
      const j = await r.json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  if (!ws) { console.log('NO WS'); child.kill(); return; }
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (method, params) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => {
    const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (res.result.exceptionDetails) return 'EXC: ' + JSON.stringify(res.result.exceptionDetails.exception || res.result.exceptionDetails.text);
    return res.result.result.value;
  };
  await send('Page.enable', {});
  await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: process.argv[2] });
  await sleep(4500);
  console.log('INSTALL', await ev(INSTALL));
  console.log('INFO   ', await ev(INFO));
  const cx = await ev(CENTER);
  console.log('CENTER ', cx);
  const { x, y } = JSON.parse(cx);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
  await sleep(1200);
  console.log('LOG    ', await ev(LOGS));
  console.log('AFTER  ', await ev(AFTER));
  ws.close(); child.kill();
}
main();
