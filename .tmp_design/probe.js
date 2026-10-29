import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = Number(process.env.PORT || 9380);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_dbg_${Date.now()}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 200; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); const errs = []; ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.method === 'Runtime.exceptionThrown') errs.push(m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); const send = (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); return { send, errs }; }
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
const { send, errs } = cdp(ws);
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
const url = process.argv[2];
await send('Page.navigate', { url });
const probe = `(function(){var q=function(s){return document.querySelectorAll(s).length};return JSON.stringify({
  ready:document.readyState, scrollY:window.scrollY, docH:document.documentElement.scrollHeight,
  preloader:q('#yisu-preloader,[class*=preload]'), hero:q('.ph-hero,.page-hero,[class*=hero]'),
  app:q('#app'), appKids:document.querySelector('#app')?document.querySelector('#app').children.length:-1,
  header:q('.app-header'), main:q('.app-main'), mainKids:document.querySelector('.app-main')?document.querySelector('.app-main').children.length:-1,
  cards:q('.ys-card'), imgs:q('img'), imgsBad:[...document.querySelectorAll('img')].filter(i=>!i.complete||i.naturalWidth===0).length,
  bodyCls:document.body.className, opacityTop:[...document.body.children].map(c=>c.tagName+'.'+(c.className||'').toString().slice(0,24)+'@'+getComputedStyle(c).opacity)
})})()`;
for (let i = 0; i < 12; i++) {
  await sleep(2000);
  const r = await send('Runtime.evaluate', { expression: probe, returnByValue: true });
  console.log('t=' + ((i + 1) * 2) + 's ' + r.result.value);
}
console.log('exceptions:', JSON.stringify(errs.slice(0, 5), null, 1));
ws.close(); child.kill();
