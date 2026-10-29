// 第三轮：试穿按钮文字对照 / SplitReveal 卡 / 面料 viewer 嵌套 / 首页裂图观感截图
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/round3';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9451;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysround3' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const rect = async (sel, i = 0) => {
    await ev(`(function(){var n=document.querySelectorAll(${JSON.stringify(sel)});if(n[${i}])n[${i}].scrollIntoView({block:"center"});return n.length})()`);
    await sleep(900);
    return ev(`(function(){var n=document.querySelectorAll(${JSON.stringify(sel)});if(!n[${i}])return "NONE(0)";
      var r=n[${i}].getBoundingClientRect();if(r.width<4||r.height<4)return "ZERO";
      return JSON.stringify({x:(r.x+r.width/2)|0,y:(r.y+r.height/2)|0})})()`);
  };
  const LB = `JSON.stringify({全局灯箱:!!document.querySelector(".ys-lightbox"),图:((document.querySelector(".ys-lightbox .lb-img")||{}).src||"").split("/").pop()})`;
  const shot = async (name) => {
    const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 60 });
    if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + name + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + name + '.jpg'); }
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  // 1) 试穿：点款式名文字（不含图）能否选中
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(6500);
  const act = `JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`;
  console.log('1 初始 is-active ' + await ev(act));
  let r = await rect(".garment-card .card-body strong", 0);
  console.log('1a 点款式名文字  ' + r);
  if (r[0] === '{') { const o = JSON.parse(r); await clickAt(o.x, o.y, 1500); console.log('    ' + await ev(act) + ' | ' + await ev(LB)); }
  r = await rect(".garment-card .thumb img", 0);
  console.log('1b 点同卡缩略图  ' + r);
  if (r[0] === '{') { const o = JSON.parse(r); await clickAt(o.x, o.y, 1500); console.log('    ' + await ev(act) + ' | ' + await ev(LB)); await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(600); }

  // 2) 档案页：点开分裂卡浮层，再点卡内图（sr-card @click=pick 走详情）
  await send('Page.navigate', { url: base + '/archive' });
  await sleep(6500);
  const cardTitle = await rect(".costume-card h3", 0);
  console.log('2 打开分裂层    点卡标题 ' + cardTitle);
  if (cardTitle[0] === '{') {
    const o = JSON.parse(cardTitle); await clickAt(o.x, o.y, 2600);
    console.log('    浮层 ' + await ev(`JSON.stringify({sr_mask:!!document.querySelector(".sr-mask"),卡数:document.querySelectorAll(".sr-card").length,图:document.querySelectorAll(".sr-card img").length})`));
    await shot('archive_split_mask');
    r = await rect(".sr-card img", 0);
    console.log('2a 点 sr 卡图    ' + r);
    if (r[0] === '{') {
      const o2 = JSON.parse(r); const p0 = await ev('location.pathname');
      await clickAt(o2.x, o2.y, 2000);
      console.log('    路径 ' + p0 + ' -> ' + await ev('location.pathname') + ' | ' + await ev(LB));
      await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700);
      r = await rect(".sr-card .sr-body h3", 0);
      console.log('2b 对照点卡文字  ' + r);
      if (r[0] === '{') { const o3 = JSON.parse(r); await clickAt(o3.x, o3.y, 2200); console.log('    路径 -> ' + await ev('location.pathname') + ' | ' + await ev(LB)); }
    }
  }

  // 3) 面料详情 viewer 嵌套
  await send('Page.navigate', { url: base + '/fabric/1' });
  await sleep(6500);
  r = await rect(".relic-card img", 0);
  console.log('3 面料详情·点图  ' + r);
  if (r[0] === '{') {
    const o = JSON.parse(r); await clickAt(o.x, o.y, 1800);
    console.log('    viewer ' + await ev(`JSON.stringify({elViewer:!!document.querySelector(".el-image-viewer__wrapper"),全局:!!document.querySelector(".ys-lightbox")})`));
    const big = await ev(`(function(){var e=document.querySelector(".el-image-viewer__canvas img");if(!e)return "NO";var b=e.getBoundingClientRect();return JSON.stringify({x:(b.x+b.width/2)|0,y:(b.y+b.height/2)|0})})()`);
    if (big[0] === '{') { const ob = JSON.parse(big); await clickAt(ob.x, ob.y, 1500); console.log('    点大图 ' + await ev(`JSON.stringify({elViewer:!!document.querySelector(".el-image-viewer__wrapper"),全局叠上:!!document.querySelector(".ys-lightbox")})`)); }
  }

  // 4) 首页裂图观感：隐藏后卡片留白情况
  await send('Page.navigate', { url: base + '/' });
  await sleep(7000);
  await ev(`(function(){var c=document.querySelector(".news-cards");if(c)c.scrollIntoView();return 1})()`);
  await sleep(1200);
  console.log('4 首页 news-cover ' + await ev(`(function(){var i=[].slice.call(document.querySelectorAll(".news-cover"));return JSON.stringify({总:i.length,裂:i.filter(function(x){return x.complete&&x.naturalWidth===0}).length,已隐藏:i.filter(function(x){return getComputedStyle(x).display==="none"}).length,卡片空图区:i.filter(function(x){return x.naturalWidth===0&&getComputedStyle(x).display!=="none"}).length})})()`));
  await ev(`(function(){var b=[].slice.call(document.querySelectorAll(".news-card")).find(function(c){var i=c.querySelector("img");return i&&i.complete&&i.naturalWidth===0});if(b)b.scrollIntoView({block:"center"});return 1})()`);
  await sleep(900);
  console.log('    卡片内图占位  ' + await ev(`(function(){var b=[].slice.call(document.querySelectorAll(".news-card")).find(function(c){var i=c.querySelector("img");return i&&i.complete&&i.naturalWidth===0});if(!b)return "无此卡";var im=b.querySelector("img");var cs=getComputedStyle(im);return JSON.stringify({display:cs.display,卡高:Math.round(b.getBoundingClientRect().height),首个子元素:b.firstElementChild.className})})()`));
  await shot('home_news_broken');

  ws.close(); child.kill();
  console.log('\nDONE ' + outDir);
}
main();
