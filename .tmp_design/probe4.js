import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = Number(process.env.PORT || 9401);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_seq_${Date.now()}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
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
  var g=function(e){if(!e)return '-';var cs=getComputedStyle(e),b=e.getBoundingClientRect();return 'op='+cs.opacity+' vis='+cs.visibility+' disp='+cs.display+' y='+Math.round(b.top)+' h='+Math.round(b.height)};
  var hp=document.querySelector('.home-page'), hero=document.querySelector('[class*=hero]'), news=document.querySelector('.news-stream,[class*=news]');
  var hit=document.elementFromPoint(720,300);
  var hs=[];var n=hit;while(n&&n!==document.body){hs.push(n.tagName+'.'+(n.className||'').toString().slice(0,20));n=n.parentElement}
  return JSON.stringify({scrollY:window.scrollY,pl:!!document.querySelector('#yisu-preloader,[class*=preload]'),
    home:g(hp),hero:g(hero),news:g(news),chain:hs.join('<'),visCount:[...document.querySelectorAll('.home-page *')].filter(e=>getComputedStyle(e).visibility==='hidden').length});
})()`;
for (let i = 1; i <= 10; i++) {
  await sleep(2000);
  const r = await send('Runtime.evaluate', { expression: ex, returnByValue: true });
  const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 60 });
  fs.writeFileSync('audit/pair/seq-' + String(i * 2) + 's.jpg', Buffer.from(s.data, 'base64'));
  console.log('t=' + (i * 2) + 's ' + r.result.value);
}
ws.close(); child.kill();
