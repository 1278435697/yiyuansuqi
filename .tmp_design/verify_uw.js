// 用户作品卡无生产数据 → 只在浏览器内存里塞一条，真点验证（不写库、不发请求）
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const INJECT = `
(function(){
  var host=document.querySelector(".user-works");
  var ins=host && (host.__vueParentComponent);
  if(!ins) return "NO INSTANCE";
  var ss=ins.setupState || ins.ctx;
  if(!ss || !ss.userWorks) return "NO userWorks binding";
  ss.userWorks.push({id:32,name:"内存测试纹样",code:"T01",dynasty:"明",category:"几何抽象",meaning:"仅用于点击验证",image_url:"/images/relics/relic_geo_dingling_zhuanghua.jpg"});
  return "已注入 "+ss.userWorks.length+" 条";
})()
`;

async function main() {
  const port = 9419;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysuw' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'http://localhost:5173/pattern' });
  await sleep(5000);
  console.log('注入    ', await ev(INJECT));
  await sleep(600);
  const ok = await ev(`(function(){var e=document.querySelector(".uw-card img");if(!e)return "NO";e.scrollIntoView({block:"center"});return "ok"})()`);
  console.log('渲染    ', ok);
  if (ok === 'ok') {
    await sleep(700);
    const q = JSON.parse(await ev(`(function(){var e=document.querySelector(".uw-card img");var r=e.getBoundingClientRect();var x=(r.x+r.width/2)|0,y=(r.y+r.height/2)|0;var h=document.elementFromPoint(x,y);return JSON.stringify({x:x,y:y,hit:h?h.tagName+"."+String(h.className||"").split(" ")[0]:"none"})})()`));
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: q.x, y: q.y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: q.x, y: q.y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: q.x, y: q.y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(1200);
    console.log('点用户卡图 命中', q.hit, '->', await ev(`JSON.stringify({路径:location.pathname,全局单图:!!document.querySelector(".ys-lightbox"),本页灯箱:!!document.querySelector(".el-image-viewer__wrapper")})`));
  }
  ws.close(); child.kill();
}
main();
