// 真鼠标到底有没有产生 click？img-col 的监听器究竟在哪？
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const INSTALL = `
window.__ev=[];
["mousedown","mouseup","pointerdown","pointerup","click","auxclick","contextmenu"].forEach(function(t){
  document.addEventListener(t,function(e){
    var tgt=e.target, path=e.composedPath().map(function(n){return n.nodeType===1?(n.tagName+(n.className?"."+String(n.className).split(" ")[0]:"")):n.nodeName;}).join(">");
    window.__ev.push(t+" btn="+e.button+" isTrusted="+e.isTrusted+" path="+(path||"").slice(0,120));
  },true);
});
"installed";
`;

const PROBE = `
(function(){
  var col=document.querySelector(".img-col");
  var keys=Object.getOwnPropertyNames(col).filter(function(k){return k.charAt(0)==="_";});
  var out={ownKeys:keys, vueInternalKeys:Object.getOwnPropertySymbols(col).map(String)};
  out.veiType=typeof col._vei;
  out.veiKeys=col._vei?Object.keys(col._vei):null;
  // 手动挂一个原生监听，验证事件能否沿链上传
  window.__manual=[];
  col.addEventListener("click",function(e){window.__manual.push("COL");},false);
  document.querySelector(".img-row").addEventListener("click",function(e){window.__manual.push("ROW");},false);
  return JSON.stringify(out);
})()
`;

const DUMP = `[...window.__ev,...(window.__manual||[]).map(function(m){return "MANUAL "+m;})].join("  ||  ")`;

const CLICKIT = `
(function(){
  var col=document.querySelector(".img-col"), img=col.querySelector("img");
  var r=img.getBoundingClientRect();
  var x=(r.x+r.width/2)|0, y=(r.y+r.height/2)|0;
  var hit=document.elementFromPoint(x,y);
  window.__ev=[]; window.__manual=[];
  hit.dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true,clientX:x,clientY:y}));
  return "合成派发于 "+hit.tagName+"."+String(hit.className||"");
})()
`;

const COLCLICK = `(window.__ev=[], window.__manual=[], document.querySelector(".img-col").click(), "col.click() 已调用")`;

async function main() {
  const port = 9412;
  const args = ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
    '--user-data-dir=' + os.tmpdir() + '/ysprobe2' + port, '--hide-scrollbars', 'about:blank'];
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', args, { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
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
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: process.argv[2] });
  await sleep(4500);
  console.log('INSTALL', await ev(INSTALL));
  console.log('PROPS  ', await ev(PROBE));

  const c = JSON.parse(await ev(`(function(){var r=document.querySelector(".img-col img").getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`));
  await ev(`(window.__ev=[],window.__manual=[],1)`);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: c.x, y: c.y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: c.x, y: c.y, button: 'left', buttons: 1, clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: c.x, y: c.y, button: 'left', buttons: 0, clickCount: 1 });
  await sleep(900);
  console.log('真鼠标 ->', await ev(DUMP));

  await ev(`(window.__ev=[],window.__manual=[],1)`);
  console.log(await ev(CLICKIT), '->', await ev(DUMP));

  await ev(`(window.__ev=[],window.__manual=[],1)`);
  console.log(await ev(COLCLICK), '->', await ev(DUMP));
  ws.close(); child.kill();
}
main();
