// 真鼠标验收：纹样详情点击 → 多图灯箱（左右轮换 + 放大）；其它图片仍走全局放大
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const VIEWER = `
(function(){
  var lb=document.querySelector(".ys-lightbox");
  var w=document.querySelector(".el-image-viewer-wrap");
  if(!w) return "全局灯箱="+!!lb+" | el-image-viewer 未打开";
  var img=document.querySelector(".el-image-viewer__canvas img");
  return "全局灯箱="+!!lb+" | 多图灯箱已开 当前="+(img?img.src.slice(-12):"none")
    +" 右箭头="+(document.querySelector(".el-image-viewer__next")?"有":"无")
    +" 放大按钮="+(document.querySelector(".el-image-viewer__actions .el-icon")?"有":"无");
})()
`;

async function main() {
  const port = 9413;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysverify' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const send = (method, params) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => {
    const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (res.result.exceptionDetails) return 'EXC: ' + JSON.stringify(res.result.exceptionDetails.exception || res.result.exceptionDetails.text);
    return res.result.result.value;
  };
  const clickAt = async (x, y) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(700);
  };
  const centerOf = (sel) => ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`);

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: process.argv[2] });
  await sleep(4500);

  console.log('改前状态      ', await ev(VIEWER));
  const c = await centerOf('.img-col img');
  console.log('主图中心      ', c);
  const p = JSON.parse(c);
  await clickAt(p.x, p.y);
  console.log('真鼠标点主图  ', await ev(VIEWER));

  // 左右轮换：点右箭头三次，看 URL 是否变化
  for (let i = 1; i <= 3; i++) {
    const a = await centerOf('.el-image-viewer__next');
    if (a === 'NO') { console.log('右箭头不存在'); break; }
    await clickAt(JSON.parse(a).x, JSON.parse(a).y);
    console.log('点右箭头 #' + i + '  ', await ev(VIEWER));
  }

  // 放大：点工具条第一个动作按钮（放大）
  const z = await centerOf('.el-image-viewer__actions .el-image-viewer__actions__inner .el-icon');
  if (z !== 'NO') { await clickAt(JSON.parse(z).x, JSON.parse(z).y); console.log('点放大按钮    缩放比=', await ev(`(document.querySelector(".el-image-viewer__canvas img")||{}).style.transform`)); }

  // 关闭后确认全局放大在别的图上仍然可用（同页的常见搭配缩略图）
  await ev(`(function(){var b=document.querySelector(".el-image-viewer__close");if(b)b.click();return 1})()`);
  await sleep(600);
  const t = await centerOf('.partner-card img');
  if (t !== 'NO') {
    await clickAt(JSON.parse(t).x, JSON.parse(t).y);
    console.log('真鼠标点搭配图', await ev(`"全局灯箱="+!!document.querySelector(".ys-lightbox")+" | 跳转纹样="+location.pathname`));
  } else {
    console.log('本页无搭配缩略图，改测列表页图片');
  }
  ws.close(); child.kill();
}
main();
