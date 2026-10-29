// 本轮三处修的真实验收：键盘进卡 / 档案权威实例图 / 头像机制（合成同构 DOM）
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const port = 9424;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yskb' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const key = async (k, code, vk) => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(500);
  };
  const clickAt = async (x, y, w = 800) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  const tap = async (sel) => {
    await ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(e)e.scrollIntoView({block:"center"});return 1})()`);
    await sleep(700);
    const q = JSON.parse(await ev(`(function(){var e=document.querySelector(${JSON.stringify(sel)});if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`));
    if (q === 'NO') return false;
    await clickAt(q.x, q.y);
    return true;
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  // 1) 键盘：Tab 走到第一张纹样卡，读焦点环，按回车看是否跳转
  await send('Page.navigate', { url: process.argv[2] + '/pattern' });
  await sleep(5000);
  let hops = 0, on = '';
  for (; hops < 30; hops++) {
    await key('Tab', 'Tab', 9);
    on = await ev(`(document.activeElement.className||document.activeElement.tagName)+""`);
    if (String(on).includes('pattern-card')) break;
  }
  console.log('1 Tab 落点     ', '第 ' + (hops + 1) + ' 次 Tab -> activeElement=' + on);
  console.log('  焦点环        ', await ev(`(function(){var e=document.querySelector(".pattern-card:focus-visible");if(!e)return "focus-visible 未命中";var cs=getComputedStyle(e);return "outline="+cs.outlineStyle+" "+cs.outlineWidth+" "+cs.outlineColor})()`));
  await key('Enter', 'Enter', 13);
  await sleep(900);
  console.log('  回车后路径    ', await ev('location.pathname'));

  // 2) 档案详情权威实例图：点图开自己的 lightbox，再点大图应关闭而不是再套一层
  await send('Page.navigate', { url: process.argv[2] + '/archive/1' });
  await sleep(5000);
  const okImg = await tap('.relic-card img');
  console.log('2 档案·点实例图  ', okImg ? await ev(`JSON.stringify({本页灯箱:!!document.querySelector(".lightbox"),全局单图:!!document.querySelector(".ys-lightbox"),图:((document.querySelector(".lightbox img")||{}).src||"").split("/").pop()})`) : '无实例图');
  await sleep(300);
  await tap('.lightbox img');
  console.log('  再点大图      ', await ev(`JSON.stringify({本页灯箱:!!document.querySelector(".lightbox"),全局单图:!!document.querySelector(".ys-lightbox")})`));

  // 3) 头像同构机制：造一个 data-lb-native 容器（内嵌 img + 容器绑点击）和一个无属性对照
  await send('Page.navigate', { url: process.argv[2] + '/pattern' });
  await sleep(4500);
  await ev(`(function(){
    window.__picked=0;
    var mk=function(native){var d=document.createElement("div");d.id=native?"t-native":"t-plain";
      if(native)d.setAttribute("data-lb-native","");
      d.style.cssText="width:120px;height:120px;position:fixed;left:20px;top:20px;z-index:99999";
      var i=document.createElement("img");i.src="/images/relics/relic_han_susha.jpg";i.style.cssText="width:120px;height:120px";
      d.appendChild(i);d.addEventListener("click",function(){window.__picked++});document.body.appendChild(d);};
    mk(true);return 1})()`);
  await sleep(1200);
  await tap('#t-native img');
  console.log('3 同构·带属性    ', await ev(`JSON.stringify({宿主点击被调用:window.__picked,全局单图:!!document.querySelector(".ys-lightbox")})`));
  await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();window.__picked=0;var d=document.getElementById("t-native");d.id="t-plain";d.removeAttribute("data-lb-native");return 1})()`);
  await sleep(800);
  await tap('#t-plain img');
  console.log('  同构·去掉属性  ', await ev(`JSON.stringify({宿主点击被调用:window.__picked,全局单图:!!document.querySelector(".ys-lightbox")})`));
  ws.close(); child.kill();
}
main();
