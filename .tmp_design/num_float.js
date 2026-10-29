// 数值量一遍：各视口下球/面板/滚动区的真实矩形
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const { spawn } = require('child_process');
const port = 9346;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_num_${Date.now()}`,
  '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 60; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find((t) => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); }
const dump = (send) => send('Runtime.evaluate', {
  expression: `(()=>{const q=(s)=>{const e=document.querySelector(s);if(!e)return null;const b=e.getBoundingClientRect();const cs=getComputedStyle(e);return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),sh:Math.round(e.scrollHeight),oh:Math.round(e.offsetHeight),ta:cs.transform.slice(0,28)}};return JSON.stringify({vw:innerWidth,lw:document.documentElement.clientWidth,scrollY:Math.round(scrollY),ball:q('.ai-float'),panel:q('.af-panel'),quick:q('.af-quick'),msgs:q('.af-msgs'),input:q('.af-input'),tip:q('.af-ball-tip')})})()`,
  returnByValue: true,
}).then((r) => JSON.parse(r.result.value));

(async () => {
  const t = await target(); const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  const send = cdp(ws);
  await send('Page.enable');
  const open = async () => { const b = await dump(send); const x = b.ball.x + 29, y = b.ball.y + 29;
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }); await sleep(600); };
  const type = async (q) => { await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 700, y: 400 }); await sleep(250);
    await send('Runtime.evaluate', { expression: `(()=>{const i=document.querySelector('.af-input input');i.focus();const d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;d.call(i,${JSON.stringify(q)});i.dispatchEvent(new Event('input',{bubbles:true}))})()` });
    await sleep(150);
    await send('Runtime.evaluate', { expression: `document.querySelector('.af-send').click()` }); await sleep(1500); };

  for (const [w, h] of [[1440, 900], [768, 900], [390, 780]]) {
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
    await sleep(500);
    if (w === 1440) { await send('Page.navigate', { url: 'http://localhost:5199/' }); await sleep(9000); }
    console.log(`\n=== ${w}x${h} 空态 ===`);
    console.log(JSON.stringify(await dump(send)));
    await open();
    console.log(`--- ${w}x${h} 打开(空) ---`);
    console.log(JSON.stringify(await dump(send)));
    await type('曲裾深衣属于哪个朝代？');
    console.log(`--- ${w}x${h} 真实一轮对话后 ---`);
    console.log(JSON.stringify(await dump(send)));
    await send('Page.captureScreenshot', { format: 'png' }).then((r) => require('fs').writeFileSync(`D:/yisu-ai-platform/.tmp_design/audit/real-${w}.png`, Buffer.from(r.data, 'base64')));
  }
  ws.close(); child.kill(); process.exit(0);
})().catch((e) => { console.error('ERR', e.message); child.kill(); process.exit(1); });
