// 第五轮：款式卡几何定位 / 键盘 vs 鼠标对照 / 面料 split 层 / 首页封面 URL 逐张核 / 上传预览抢占
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const base = process.argv[2];
  const outDir = __dirname + '/audit/round5';
  fs.mkdirSync(outDir, { recursive: true });
  const port = 9467;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysround5' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const key = async (k, code, vk) => {
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(700);
  };
  const LB = `JSON.stringify({全局灯箱:!!document.querySelector(".ys-lightbox"),图:((document.querySelector(".ys-lightbox .lb-img")||{}).src||"").split("/").pop()})`;
  const shot = async (n) => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 62 }); if (r.result && r.result.data) { fs.writeFileSync(outDir + '/' + n + '.jpg', Buffer.from(r.result.data, 'base64')); console.log('    截图 ' + n); } };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  // A) 款式卡几何：卡片/缩略图/名文字 各自动弹与命中元素
  await send('Page.navigate', { url: base + '/tryon' });
  await sleep(6500);
  console.log('A 卡片几何       ' + await ev(`(function(){
    var c=document.querySelector(".garment-card");if(!c)return "无卡";
    var R=function(e){if(!e)return null;var r=e.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};
    var st=c.querySelector(".card-body strong");var im=c.querySelector(".thumb img");
    var hs=function(e){if(!e)return null;var r=e.getBoundingClientRect();var h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));return h?h.tagName+"."+(h.getAttribute("src")||"").split("/").pop():"null"};
    return JSON.stringify({卡:R(c),缩略图:R(im),名文字:R(st),点名文字命中:hs(st),点缩略图命中:hs(im),卡overflow:getComputedStyle(c).overflow})})()`));

  const act = `JSON.stringify([].slice.call(document.querySelectorAll(".garment-card")).map(function(b,i){return b.classList.contains("is-active")?i:-1}).filter(function(x){return x>=0}))`;
  // B) 键盘：聚焦第一张卡按 Enter
  await ev(`(function(){var c=document.querySelector(".garment-card");if(c)c.focus();return document.activeElement.className})()`);
  await sleep(400);
  console.log('B 聚焦元素      ' + await ev(`document.activeElement.tagName+"."+(document.activeElement.className||"")`));
  await key('Enter', 'Enter', 13);
  console.log('  Enter 后选中  ' + await ev(act) + ' | ' + await ev(LB));
  await key('Enter', 'Enter', 13);
  console.log('  再 Enter 取消 ' + await ev(act));
  // C) 鼠标：点名文字中心（上一轮证明命中的是 IMG）
  const stPt = await ev(`(function(){var s=document.querySelector(".garment-card .card-body strong");if(!s)return "NO";var r=s.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`);
  console.log('C 鼠标点名文字  ' + stPt);
  if (stPt[0] === '{') { const o = JSON.parse(stPt); await clickAt(o.x, o.y, 1600); console.log('    选中 ' + await ev(act) + ' | ' + await ev(LB)); await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(700); }

  // D) 上传预览图抢占：用 CDP 给 input[type=file] 塞一个本地文件
  await ev(`(function(){var d=document.querySelector(".drop-zone");if(d)d.scrollIntoView({block:"center"});return !!d})()`);
  await sleep(800);
  const doc = await send('DOM.getDocument', {});
  const node = await send('DOM.querySelector', { nodeId: doc.result.root.nodeId, selector: '.drop-zone input[type=file]' });
  const sample = 'C:/Users/lenovo/AppData/Local/Temp/yisu_fe/sample_person.png';
  if (!fs.existsSync(sample)) { try { fs.copyFileSync('C:/Users/lenovo/Documents/Qoder/2026-10-17/0f346206/../../../../yisu-ai-platform/frontend/public/images/dynasty_ming.png', sample); } catch (e) { } }
  console.log('D 文件input     ' + JSON.stringify(node.result) + ' 样本存在=' + fs.existsSync(sample));
  if (node.result && node.result.nodeId && fs.existsSync(sample)) {
    const f = await send('DOM.setFileInputFiles', { nodeId: node.result.nodeId, files: [sample] });
    console.log('    塞文件 ' + JSON.stringify(f.result || f.error || 'ok').slice(0, 90));
    await sleep(3500);
    console.log('    预览图      ' + await ev(`JSON.stringify({dropImg:!!document.querySelector(".drop-zone img"),src:((document.querySelector(".drop-zone img")||{}).src||"").slice(0,42)})`));
    const pv = await ev(`(function(){var i=document.querySelector(".drop-zone img");if(!i)return "NO";var r=i.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`);
    if (pv[0] === '{') { const o = JSON.parse(pv); await clickAt(o.x, o.y, 1500); console.log('    点预览图    ' + await ev(LB)); }
  }

  // E) 面料：点卡 → split 层 → 点层内卡图 vs 文字
  await send('Page.navigate', { url: base + '/fabric' });
  await sleep(6500);
  const fp = await ev(`(function(){var h=document.querySelector(".fabric-card .card-body strong");if(!h)h=document.querySelector(".fabric-card h3");if(!h)return "NO";h.scrollIntoView({block:"center"});var r=h.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`);
  console.log('E1 点面料卡文字 ' + fp);
  if (fp[0] === '{') { const o = JSON.parse(fp); await clickAt(o.x, o.y, 2800); }
  console.log('    层 ' + await ev(`JSON.stringify({sr_mask:!!document.querySelector(".sr-mask"),卡:document.querySelectorAll(".sr-card").length,图:document.querySelectorAll(".sr-card img").length,路径:location.pathname})`));
  const spt = await ev(`(function(){var i=document.querySelector(".sr-card img");if(!i)return "NO";var r=i.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`);
  if (spt[0] === '{') {
    const o = JSON.parse(spt); await clickAt(o.x, o.y, 2200);
    console.log('E2 层内点卡图   路径 ' + await ev('location.pathname') + ' | ' + await ev(LB));
    await ev(`(function(){var b=document.querySelector(".lb-close");if(b)b.click();return 1})()`); await sleep(800);
    const t2 = await ev(`(function(){var e=document.querySelector(".sr-card .sr-body h3");if(!e)return "NO";var r=e.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()`);
    if (t2[0] === '{') { const o2 = JSON.parse(t2); await clickAt(o2.x, o2.y, 2600); console.log('E3 对照点文字   路径 ' + await ev('location.pathname') + ' | ' + await ev(LB)); }
  }

  // F) 首页：逐张封面 URL 与加载结果
  await send('Page.navigate', { url: base + '/' });
  await sleep(4000);
  await ev(`new Promise(function(res){var y=0,t=setInterval(function(){y+=520;window.scrollTo(0,y);if(y>document.body.scrollHeight+600){clearInterval(t);res(1)}},170)})`);
  await sleep(5000);
  const covers = await ev(`JSON.stringify([].slice.call(document.querySelectorAll(".news-cover,.focus-img")).map(function(i){return {ok:i.complete&&i.naturalWidth>0,disp:getComputedStyle(i).display,src:i.getAttribute("src")}}))`);
  const arr = JSON.parse(covers);
  console.log('F 封面 ' + arr.length + ' 张，失败 ' + arr.filter(x => !x.ok).length);
  arr.forEach(x => console.log('    ' + (x.ok ? 'OK ' : 'FAIL') + ' display=' + x.disp + ' ' + String(x.src).slice(0, 92)));

  ws.close(); child.kill();
  console.log('\nDONE ' + outDir);
}
main();
