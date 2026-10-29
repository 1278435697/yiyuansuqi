import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = Number(process.env.PORT || 9395);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_t_${Date.now()}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 200; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); }
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
const send = cdp(ws);
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: process.argv[2] });
const ex = `(function(){
  var g=function(e){if(!e)return '-';var cs=getComputedStyle(e),b=e.getBoundingClientRect();return 'op='+cs.opacity+' vis='+cs.visibility+' h='+Math.round(b.height)+' anim='+cs.animationName+' cls='+(e.className||'').toString().slice(0,26)};
  var m=document.querySelector('.app-main');
  var hp=document.querySelector('.home-page');
  var hero=document.querySelector('[class*=hero]');
  var pl=document.querySelector('#yisu-preloader,[class*=preload]');
  var hit=document.elementFromPoint(720,300);
  return JSON.stringify({pl:pl?('YES '+(pl.className||'').toString().slice(0,26)+' op='+getComputedStyle(pl).opacity):'gone',
    main:m?g(m):'-', home:hp?g(hp):'-', hero:hero?g(hero):'-',
    hit:hit?hit.tagName+'.'+(hit.className||'').toString().slice(0,26):'-'});
})()`;
for (let i = 0; i < 26; i++) {
  await sleep(1000);
  const r = await send('Runtime.evaluate', { expression: ex, returnByValue: true });
  console.log('t=' + (i + 1) + 's ' + r.result.value);
}
ws.close(); child.kill();
