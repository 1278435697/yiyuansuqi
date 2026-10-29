import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = Number(process.env.PORT || 9357);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_m2_${Date.now()}`, '--window-size=390,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 200; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); }
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
const send = cdp(ws);
const W = Number(process.env.W || 390), H = Number(process.env.H || 844);
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: W < 800 });
const [url, scrollTo, out] = process.argv.slice(2);
await send('Page.navigate', { url });
await sleep(1500);
// 就绪判据见下面 check：开场层退场 + .app-main 有内容，两个条件缺一不可。
const clickPoint = async () => {
  const b = await send('Runtime.evaluate', { expression: `(function(){var e=document.querySelector('.pl-center,.pl-ring,#yisu-preloader');if(!e)return null;var r=e.getBoundingClientRect();return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2})})()`, returnByValue: true });
  if (!b.result.value) return;
  const { x, y } = JSON.parse(b.result.value);
  for (const type of ['mousePressed', 'mouseReleased']) {
    await send('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1, buttons: type === 'mousePressed' ? 1 : 0 });
  }
};
let ready = false;
// 两道都要过：
// 1) 视口中心不再被开场层盖住；
// 2) .app-main 里真的有内容（首子元素高度 >400）。
// 第 2 条是必须的：路由懒加载 + Vite dev 现场编译，chunk 没到之前头部和页脚已经在了，
// 只看 opacity 或只看开场层都会放行，拍到一张「只有壳」的空页。
const check = `(function(){
  var n=document.elementFromPoint(${Math.round(W / 2)},${Math.round(H / 2)});var s='';
  while(n){s+=' '+(n.id||'')+' '+(n.className||'').toString();n=n.parentElement}
  if(/preload|pl-bg|pl-reveal|pl-center|pl-ring/.test(s))return 'occluded';
  var m=document.querySelector('.app-main');if(!m)return 'no-main';
  var k=m.firstElementChild;if(!k||k.getBoundingClientRect().height<400)return 'empty-main';
  return 'ok'})()`;
let streak = 0;
for (let i = 0; i < 90; i++) {
  const r = await send('Runtime.evaluate', { expression: check, returnByValue: true });
  const st = r.result.value;
  if (st === 'occluded' && (i === 8 || i === 20)) await clickPoint();
  streak = st === 'ok' ? streak + 1 : 0;
  if (streak >= 3) { ready = true; break; }   // 连续 3 次合格，避开编译完成的瞬间抖动
  await sleep(700);
}
if (!ready) { ws.close(); child.kill(); throw new Error('页面未就绪（开场层未退或 .app-main 为空），拒绝拍空图: ' + url); }
await sleep(2500);
await send('Runtime.evaluate', { expression: `window.scrollTo(0, ${scrollTo})` });
await sleep(1200);
const pre = await send('Runtime.evaluate', { expression: check, returnByValue: true });
if (pre.result.value !== 'ok') { ws.close(); child.kill(); throw new Error('拍摄前状态回退为 ' + pre.result.value + ': ' + url); }
const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 72 });
fs.writeFileSync(out, Buffer.from(s.data, 'base64'));
const scroll = await send('Runtime.evaluate', { expression: `JSON.stringify({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,bodySw:document.body.scrollWidth})`, returnByValue: true });
console.log('saved ' + out + ' ' + scroll.result.value);
ws.close(); child.kill();
