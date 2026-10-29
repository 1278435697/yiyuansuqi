// 面料详情三处图 + 纹样搭配卡：真鼠标逐条验收
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const STATE = `
(function(){
  var v=document.querySelector(".el-image-viewer__wrapper");
  var cur=v?document.querySelector(".el-image-viewer__canvas img"):null;
  return JSON.stringify({页面:location.pathname,
    本页灯箱:!!v, 全局单图:!!document.querySelector(".ys-lightbox"),
    箭头:!!document.querySelector(".el-image-viewer__next"),
    放大条:!!document.querySelector(".el-image-viewer__actions"),
    图:cur?cur.src.split("/").pop().slice(0,26):""});
})()
`;

async function main() {
  const port = 9417;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysfix' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify(r.result.exceptionDetails.exception || r.result.exceptionDetails.text); return r.result.result.value; };
  const clickAt = async (x, y, wait = 800) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(wait);
  };
  // 滚到元素中间再量坐标，避免懒加载图未进入视口
  const prep = (sel) => ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(!e)return "NO::"+${JSON.stringify(sel)};
    e.scrollIntoView({block:"center"});return "ok"})()`);
  const hit = (sel) => ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});var r=e.getBoundingClientRect();
    var x=(r.x+r.width/2)|0,y=(r.y+r.height/2)|0;var h=document.elementFromPoint(x,y);
    return JSON.stringify({x:x,y:y,hit:h?(h.tagName+"#"+h.id+"."+String(h.className||"").split(" ")[0]):"none"})})()`);
  const closeViewer = async () => {
    const c = await ev(`(function(){var b=document.querySelector(".el-image-viewer__close");if(b){b.click();return 1}return 0})()`);
    await ev(`(function(){var b=document.querySelector(".lb-close");if(b){b.click();return 1}return 0})()`);
    await sleep(600); return c;
  };
  const step = async (label, sel) => {
    const p = await prep(sel);
    if (p.startsWith('NO')) { console.log(label.padEnd(16), '选择器不存在', p); return; }
    await sleep(700);
    const q = JSON.parse(await hit(sel));
    if (q.hit !== 'IMG#' && !/IMG/.test(q.hit)) { console.log(label.padEnd(16), '命中不是图：', JSON.stringify(q)); return; }
    await clickAt(q.x, q.y);
    console.log(label.padEnd(16), await ev(STATE));
    await closeViewer();
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  await send('Page.navigate', { url: process.argv[2] });  // /fabric/11
  await sleep(5000);
  console.log('== 面料详情 /fabric/11 ==');
  await step('实物图', '.relic-card img');
  await step('工艺·完整流程', '.craft-img-block:nth-child(1) img');
  await step('工艺·细节特写', '.craft-img-block:nth-child(2) img');

  await send('Page.navigate', { url: process.argv[3] });  // /pattern/32
  await sleep(4500);
  console.log('== 纹样详情 /pattern/32 ==');
  await step('主图（多图轮换）', '.img-col img');
  const before = await ev('location.pathname');
  await prep('.partner-card img'); await sleep(700);
  const pc = JSON.parse(await hit('.partner-card img'));
  await clickAt(pc.x, pc.y, 1200);
  console.log('搭配卡（应跳转）  命中', pc.hit, '路径', before, '->', await ev('location.pathname'), await ev(STATE));

  await send('Page.navigate', { url: process.argv[4] });  // /pattern 列表
  await sleep(4500);
  console.log('== 纹样列表（未改，应仍是全局单图） ==');
  await step('列表卡图', '.pattern-card img');
  ws.close(); child.kill();
}
main();
