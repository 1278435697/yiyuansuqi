import { spawn } from 'child_process';
import fs from 'fs';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = Number(process.env.PORT || 9385);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${port}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_v_${Date.now()}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 200; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) { let id = 0; const pend = new Map(); ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }); return (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }); }
const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
const send = cdp(ws);
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
const url = process.argv[2];
await send('Page.navigate', { url });
await sleep(12000);
const ex = `(function(){
  var out=[];
  var main=document.querySelector('.app-main');
  out.push('main rect='+JSON.stringify(main.getBoundingClientRect().toJSON())+' op='+getComputedStyle(main).opacity+' vis='+getComputedStyle(main).visibility);
  var k=main.firstElementChild;
  while(k){var cs=getComputedStyle(k),b=k.getBoundingClientRect();
    out.push(k.tagName+'.'+(k.className||'').toString().slice(0,30)+' y='+Math.round(b.top)+' h='+Math.round(b.height)+' op='+cs.opacity+' vis='+cs.visibility+' disp='+cs.display+' z='+cs.zIndex+' anim='+cs.animationName+' tf='+cs.transform.slice(0,24));
    k=k.nextElementSibling;}
  var h=document.querySelector('[class*=hero]');
  if(h){var hs=getComputedStyle(h),hb=h.getBoundingClientRect();
    out.push('HERO '+h.className+' y='+Math.round(hb.top)+' h='+Math.round(hb.height)+' op='+hs.opacity+' vis='+hs.visibility+' pos='+hs.position+' z='+hs.zIndex+' bgimg='+hs.backgroundImage.slice(0,60));
    var inner=h.querySelector('img'); if(inner) out.push('HERO IMG complete='+inner.complete+' nat='+inner.naturalWidth+' op='+getComputedStyle(inner).opacity);}
  var el=document.elementFromPoint(700,400);
  out.push('point(700,400) = '+(el?el.tagName+'.'+(el.className||'').toString().slice(0,40):'null'));
  return out.join('\\n');
})()`;
const r = await send('Runtime.evaluate', { expression: ex, returnByValue: true });
console.log(r.result.value);
const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 72 });
fs.writeFileSync('audit/pair/debug-home.jpg', Buffer.from(s.data, 'base64'));
ws.close(); child.kill();
