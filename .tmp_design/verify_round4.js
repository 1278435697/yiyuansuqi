// 第四轮：干净对照（elementFromPoint 定位）+ viewer 内嵌套 + 首页裂图观感
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/round4';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9459;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysround4' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
    if (r.result.exceptionDetails) return 'EXC ' + String((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text).slice(0, 200);
    return r.result.result.value;
  };
  const clickAt = async (x, y, w = 1500) => {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: 1 });
    await sleep(w);
  };
  const LB = `JSON.stringify({全局灯箱:!!document.querySelector(".ys-lightbox"),图:((document.querySelector(".ys-lightbox .lb-img")||{}).src||"").split("/").pop()})`;
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };
  // 找一个点：elementFromPoint 命中 targetSel（或其后代），保证没被别的元素盖住
  const pointOver = (targetSel, notImg) => ev(`(function(){
    var e=document.querySelector(${JSON.stringify(targetSel)});if(!e)return "NO_TARGET";
    e.scrollIntoView({block:"center"});
    var r=e.getBoundingClientRect();
    for(var fy=0.2;fy<=0.9;fy+=0.1){for(var fx=0.2;fx<=0.9;fx+=0.1){
      var x=Math.round(r.x+r.width*fx), y=Math.round(r.y+r.height*fy);
      var hit=document.elementFromPoint(x,y);
      if(hit&&(hit===e||e.contains(hit)${notImg ? '&&hit.tagName!=="IMG"' : ''}))
        return JSON.stringify({x:x,y:y,hit:hit.tagName+"."+(String(hit.className.baseVal!==undefined?hit.className.baseVal:hit.className)||"").slice(0,18)});}}
    return "NO_CLEAN_POINT";})()`);
  const closeLB = async () => { await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700); };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  // 1) 试穿款式卡：干净对照（名文字命中的必须不是 IMG）
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(6500);
  const act = `JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`;
  const cardCount = await ev(`document.querySelectorAll(".garment-card").length`);
  console.log('1 款式卡数=' + cardCount + ' 初始 is-active ' + await ev(act));
  let p = await pointOver('.garment-card .card-body strong', true);
  console.log('1a 名文字干净点  ' + p);
  if (p[0] === '{') { const o = JSON.parse(p); await clickAt(o.x, o.y, 1600); console.log('    is-active ' + await ev(act) + ' | ' + await ev(LB)); await closeLB(); }
  p = await pointOver('.garment-card .thumb img', false);
  console.log('1b 缩略图干净点  ' + p);
  if (p[0] === '{') { const o = JSON.parse(p); const a0 = await ev(act); await clickAt(o.x, o.y, 1600); console.log('    is-active ' + a0 + ' -> ' + await ev(act) + ' | ' + await ev(LB)); await closeLB(); }

  // 2) 面料：列表卡文字 -> 详情 -> 点实物图（已上线让路）-> 点 viewer 大图
  await send('Page.navigate', { url: base + '/fabric' });
  await sleep(6500);
  p = await pointOver('.fabric-card h3', true);
  if (p[0] === 'NO_TARGET') p = await pointOver('.fabric-card .f-body', true);
  console.log('2 点面料卡文字   ' + p);
  if (p[0] === '{') { const o = JSON.parse(p); await clickAt(o.x, o.y, 2600); }
  console.log('    路径 ' + await ev('location.pathname'));
  p = await pointOver('.relic-card img', false);
  console.log('2a 点面料实物图  ' + p);
  if (p[0] === '{') {
    const o = JSON.parse(p); await clickAt(o.x, o.y, 1900);
    console.log('    ' + await ev(`JSON.stringify({elViewer:!!document.querySelector(".el-image-viewer__wrapper"),全局:!!document.querySelector(".ys-lightbox"),箭头:!!document.querySelector(".el-image-viewer__next")})`));
    const big = await ev(`(function(){var e=document.querySelector(".el-image-viewer__canvas img");if(!e)return "NO";var b=e.getBoundingClientRect();return JSON.stringify({x:(b.x+b.width/2)|0,y:(b.y+b.height/2)|0})})()`);
    if (big[0] === '{') { const ob = JSON.parse(big); await clickAt(ob.x, ob.y, 1600);
      console.log('    点viewer大图后 ' + await ev(`JSON.stringify({elViewer:!!document.querySelector(".el-image-viewer__wrapper"),全局叠上:!!document.querySelector(".ys-lightbox"),z:document.querySelector(".ys-lightbox")?getComputedStyle(document.querySelector(".ys-lightbox")).zIndex:null})`));
      await shot('fabric_viewer_nested'); }
  }

  // 3) 首页：滚动触发懒加载后统计裂图
  await send('Page.navigate', { url: base + '/' });
  await sleep(4000);
  await ev(`new Promise(function(res){var y=0;var t=setInterval(function(){y+=500;window.scrollTo(0,y);if(y>document.body.scrollHeight){clearInterval(t);res(1)}},180)})`);
  await sleep(4500);
  console.log('3 首页封面      ' + await ev(`(function(){var i=[].slice.call(document.querySelectorAll(".news-cover,.focus-img"));return JSON.stringify({张数:i.length,加载失败:i.filter(function(x){return x.complete&&x.naturalWidth===0}).length,已被error隐藏:i.filter(function(x){return getComputedStyle(x).display==="none"}).length})})()`));
  console.log('    失败域名     ' + await ev(`JSON.stringify([...new Set([].slice.call(document.images).filter(function(x){return x.complete&&x.naturalWidth===0}).map(function(x){try{return new URL(x.src).host}catch(e){return x.src.slice(0,20)}}))])`));
  await ev(`(function(){var b=[].slice.call(document.querySelectorAll(".news-card")).find(function(c){var i=c.querySelector("img");return i&&i.complete&&i.naturalWidth===0});if(b)b.scrollIntoView({block:"center"});return 1})()`);
  await sleep(1000);
  console.log('    失败卡形态   ' + await ev(`(function(){var b=[].slice.call(document.querySelectorAll(".news-card")).find(function(c){var i=c.querySelector("img");return i&&i.complete&&i.naturalWidth===0});if(!b)return "无";var im=b.querySelector("img");return JSON.stringify({图display:getComputedStyle(im).display,卡宽:Math.round(b.getBoundingClientRect().width),卡高:Math.round(b.getBoundingClientRect().height),首子:b.firstElementChild.className})})()`));
  await shot('home_after_scroll');

  ws.close(); child.kill();
  console.log('\nDONE ' + outDir);
}
main();
