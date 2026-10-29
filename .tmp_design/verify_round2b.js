// 第二轮复测：资讯卡/款式按钮对照、全局灯箱自噬、多图灯箱嵌套、社区帖图、/login 空白、上传预览抢占
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const port = 9443;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysround2' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const clickAt = async (x, y, w = 1500) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  // 取某个选择器元素的中心点（真实几何）
  const box = (sel, i = 0, dx = 0, dy = 0) => ev(`(function(){
    var n=[].slice.call(document.querySelectorAll(${JSON.stringify(sel)}));
    if(!n[${i}])return "NONE("+n.length+")";
    n[${i}].scrollIntoView({block:"center"});return 1})().then?0:0`);
  const rect = async (sel, i = 0) => {
    await ev(`(function(){var n=document.querySelectorAll(${JSON.stringify(sel)});if(n[${i}])n[${i}].scrollIntoView({block:"center"});return 1})()`);
    await sleep(800);
    return ev(`(function(){var n=document.querySelectorAll(${JSON.stringify(sel)});if(!n[${i}])return "NONE(" + n.length + ")";
      var r=n[${i}].getBoundingClientRect();if(r.width<4||r.height<4)return "ZERO";
      return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0,w:Math.round(r.width),h:Math.round(r.height)})})()`);
  };
  const LB = `JSON.stringify({全局灯箱:!!document.querySelector(".ys-lightbox"),图:((document.querySelector(".ys-lightbox .lb-img")||{}).src||"").split("/").pop(),full:!!document.querySelector(".ys-lightbox .lb-img.full"),提示:(document.querySelector(".lb-hint")||{}).innerText||""})`;

  // 1) 首页资讯卡：点封面 vs 点标题（同一张卡内）
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: base + '/' });
  await sleep(6500);
  let r = await rect(".focus-item .focus-img", 0);
  console.log('1a 头条·点封面   ' + r);
  if (r[0] === '{') { const o = JSON.parse(r); await clickAt(o.x, o.y, 1700); console.log('    结果 路径=' + await ev('location.pathname') + ' ' + await ev(LB)); await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700); }
  r = await rect(".focus-item h3", 0);
  console.log('1b 头条·点标题   ' + r + '  (对照)');
  if (r[0] === '{') { const o = JSON.parse(r); await clickAt(o.x, o.y, 1900); console.log('    结果 路径=' + await ev('location.pathname') + ' ' + await ev(LB)); }

  // 2) 试穿款式按钮：点缩略图 vs 点名称文字
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(6500);
  const active = `JSON.stringify([].slice.call(document.querySelectorAll(".garment-card.is-active")).map(function(b){return (b.getAttribute("aria-label")||b.innerText||"").replace(/\\s+/g,"").slice(0,10)}))`;
  console.log('2 初始选中      ' + await ev(active));
  r = await rect(".garment-card .thumb img", 0);
  console.log('2a 点缩略图     ' + r);
  if (r[0] === '{') {
    const o = JSON.parse(r); const a0 = await ev(active);
    await clickAt(o.x, o.y, 1500);
    console.log('    选中 ' + a0 + ' -> ' + await ev(active) + ' | ' + await ev(LB));
    await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700);
  }
  r = await rect(".garment-card .card-body", 0);
  if (r[0] === 'NONE' || String(r).startsWith('NONE')) r = await rect(".garment-card", 0);
  console.log('2b 点卡片文字区  ' + r + '  (对照)');
  if (r[0] === '{') { const o = JSON.parse(r); const a0 = await ev(active); await clickAt(o.x, o.y + Math.round(o.h / 2) - 12, 1500); console.log('    选中 ' + a0 + ' -> ' + await ev(active) + ' | ' + await ev(LB)); }

  // 3) 全局灯箱自身：点大图能否放大
  await send('Page.navigate', { url: base + '/pattern' });
  await sleep(6000);
  r = await rect(".pattern-card .p-img", 0);
  console.log('3 列表卡图点开  ' + r);
  if (r[0] === '{') {
    const o = JSON.parse(r); await clickAt(o.x, o.y, 1600);
    console.log('    打开 ' + await ev(LB));
    const im = await ev(`(function(){var e=document.querySelector(".ys-lightbox .lb-img");if(!e)return "NO";var b=e.getBoundingClientRect();return JSON.stringify({x:(b.x+b.width/2)|0,y:(b.y+b.height/2)|0})})()`);
    const oi = JSON.parse(im); await clickAt(oi.x, oi.y, 1300);
    console.log('    点大图后 ' + await ev(LB));
    await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700);
  }

  // 4) 纹样详情多图灯箱：点大图会不会再叠一层全局灯箱
  await send('Page.navigate', { url: base + '/pattern/32' });
  await sleep(6500);
  r = await rect(".img-col", 0);
  console.log('4a 详情·点图列   ' + r);
  if (r[0] === '{') {
    const o = JSON.parse(r); await clickAt(o.x, o.y, 1800);
    console.log('    本页多图 ' + await ev(`JSON.stringify({elImageViewer:!!document.querySelector(".el-image-viewer__wrapper"),轮换箭头:!!document.querySelector(".el-image-viewer__next"),全局:!!document.querySelector(".ys-lightbox")})`));
    const big = await ev(`(function(){var e=document.querySelector(".el-image-viewer__canvas img");if(!e)return "NO";var b=e.getBoundingClientRect();return JSON.stringify({x:(b.x+b.width/2)|0,y:(b.y+b.height/2)|0})})()`);
    if (big[0] === '{') { const ob = JSON.parse(big); await clickAt(ob.x, ob.y, 1500);
      console.log('    点viewer大图 ' + await ev(`JSON.stringify({本页viewer:!!document.querySelector(".el-image-viewer__wrapper"),全局叠在上面:!!document.querySelector(".ys-lightbox"),全局z:document.querySelector(".ys-lightbox")?getComputedStyle(document.querySelector(".ys-lightbox")).zIndex:null})`)); }
    await ev(`(function(){var b=document.querySelector(".el-image-viewer__close");if(b)b.click();return 1})()`); await sleep(600);
  }

  // 5) 社区帖子缩略图
  await send('Page.navigate', { url: base + '/community' });
  await sleep(6000);
  r = await rect(".post-main .post-img img", 0);
  console.log('5 社区·点帖图   ' + r + ' | 页面 ' + await ev('document.body.innerText.replace(/\\s+/g,"").length') + '字');
  if (r[0] === '{') {
    const o = JSON.parse(r); const p0 = await ev('location.pathname+location.search');
    await clickAt(o.x, o.y, 1700);
    console.log('    ' + p0 + ' -> ' + await ev('location.pathname+location.search') + ' | ' + await ev(LB));
  }

  // 6) /login 死链
  await send('Page.navigate', { url: base + '/login' });
  await sleep(5000);
  console.log('6 /login        正文 ' + await ev('document.body.innerText.replace(/\\s+/g,"").length') + ' 字 | 可见卡 ' + await ev('document.querySelectorAll(".ys-card").length') + ' | 路由 ' + await ev('location.pathname'));

  // 7) 上传预览图抢占 + drop-zone 键盘
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(6000);
  console.log('7 drop-zone     ' + await ev(`(function(){var d=document.querySelector(".drop-zone");if(!d)return "无";var cs=getComputedStyle(d);return JSON.stringify({tabindex:d.getAttribute("tabindex"),role:d.getAttribute("role"),有input文件:!!document.querySelector(".drop-zone input[type=file]")})})()`));

  ws.close(); child.kill();
  console.log('\nDONE');
}
main();
