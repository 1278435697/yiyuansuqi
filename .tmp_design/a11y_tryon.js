// 试穿模块无障碍体检：axe-core 注入 + 键盘 Tab 序列 + 真控件触控尺寸
// 用法：node a11y_tryon.js <baseUrl> <outJson>
import { spawn } from 'child_process';
import fs from 'fs';

const AXE = 'C:/Users/lenovo/AppData/Local/Temp/axe-tool/node_modules/axe-core/axe.min.js';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const PORT = 9411;
const BASE = process.argv[2] || 'http://localhost:5173';
const OUT = process.argv[3] || '.tmp_design/audit/a11y_tryon.json';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', `--remote-debugging-port=${PORT}`, `--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_a11y_${Date.now()}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
async function target() { for (let i = 0; i < 200; i++) { try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) return p; } catch {} await sleep(250); } throw new Error('no target'); }
function cdp(ws) {
  let id = 0; const pend = new Map(); const errs = [];
  ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data);
    if (m.method === 'Runtime.exceptionThrown') errs.push((m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text || '').split('\n')[0]);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } });
  return { send: (method, params = {}) => new Promise((res, rej) => { const n = ++id; pend.set(n, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: n, method, params })); }), errs };
}

const t = await target();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
const { send, errs } = cdp(ws);
const axeSrc = fs.readFileSync(AXE, 'utf8');

const check = (W, H) => `(function(){
  var n=document.elementFromPoint(${Math.round(W / 2)},${Math.round(H / 2)});var s='';
  while(n){s+=' '+(n.id||'')+' '+(n.className||'').toString();n=n.parentElement}
  if(/preload|pl-bg|pl-reveal/.test(s))return 'occluded';
  var m=document.querySelector('.app-main');if(!m)return 'no-main';
  var k=m.firstElementChild;if(!k||k.getBoundingClientRect().height<300)return 'empty-main';
  return 'ok'})()`;

const ALL = [['tryon', '/tryon'], ['gallery', '/tryon/gallery'], ['history', '/tryon/history']];
const routes = process.env.ROUTES ? ALL.filter(r => process.env.ROUTES.split(',').includes(r[0])) : ALL;
const viewports = [['d', 1440, 900], ['m', 390, 844]];
const results = [];

for (const [name, path] of routes) {
  for (const [vk, W, H] of viewports) {
    await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: vk === 'm' });
    await send('Runtime.enable'); await send('Page.enable');
    await send('Page.navigate', { url: BASE + path });
    await sleep(1500);
    let ok = false;
    for (let i = 0; i < 90; i++) {
      const r = await send('Runtime.evaluate', { expression: check(W, H), returnByValue: true });
      if (r.result.value === 'ok') { ok = true; break; }
      await sleep(700);
    }
    if (!ok) { results.push({ name, vk, error: 'not-ready' }); continue; }
    await sleep(2500);

    // axe 注入并运行
    await send('Runtime.evaluate', { expression: axeSrc });
    const axeRun = await send('Runtime.evaluate', {
      expression: `new Promise(res=>window.axe.run(document,{resultTypes:['violations']}).then(r=>res(JSON.stringify({
        violations:r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,n:v.nodes.length,
          sample:v.nodes.slice(0,80).map(nd=>({tgt:(nd.target||[]).join(' '),sum:(nd.failureSummary||'').slice(0,160),html:(nd.html||'').replace(/\\s+/g,' ').slice(0,140)}))})),
        passes:r.passes.length,incomplete:r.incomplete.map(i=>i.id)}))))`,
      awaitPromise: true, returnByValue: true,
    });
    const axe = JSON.parse(axeRun.result.value);

    // 真控件触控尺寸（窄屏 44×44 口径，与 health.js 一致）
    const touch = await send('Runtime.evaluate', {
      expression: `(function(){var out=[];var sel='button,.el-button,.el-tabs__item,.el-radio-button__inner,.el-pager li,.el-segmented__item,input,select,.app-nav a';
        document.querySelectorAll(sel).forEach(function(e){var b=e.getBoundingClientRect();if(!b.width&&!b.height)return;
          if(b.height<43||b.width<43){var w=e.closest('.el-select__wrapper,.el-input__wrapper,.el-textarea');
            if(w&&w.getBoundingClientRect().height>=43)return;
            out.push({p:(function(n){var s=[];while(n&&n.tagName!=='BODY'){s.unshift(n.tagName.toLowerCase()+(n.className&&typeof n.className==='string'?'.'+n.className.trim().split(/\\s+/)[0]:''));n=n.parentElement}return s.slice(-3).join('>')})(e),w:Math.round(b.width),h:Math.round(b.height)})}});
        return JSON.stringify(out)})()`,
      returnByValue: true,
    });

    // 键盘 Tab 序列：走 25 跳，记录落在哪个控件上
    await send('Runtime.evaluate', { expression: `document.activeElement.blur();window.scrollTo(0,0)` });
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    const seq = [];
    for (let i = 0; i < 24; i++) {
      const f = await send('Runtime.evaluate', {
        expression: `(function(){var e=document.activeElement;if(!e||e===document.body)return 'BODY';
          var cs=getComputedStyle(e);var r=e.getBoundingClientRect();
          return [e.tagName.toLowerCase(),(e.id?'#'+e.id:''),(typeof e.className==='string'&&e.className?'.'+e.className.trim().split(/\\s+/)[0]:''),
            (e.getAttribute('aria-label')||e.getAttribute('title')||e.textContent||'').trim().slice(0,16),
            Math.round(r.width)+'x'+Math.round(r.height),
            'ring='+(cs.outlineStyle==='none'?'none':cs.outlineStyle+' '+cs.outlineColor),
            'vis='+(r.width&&r.height?'y':'n')].join(' ')})()`,
        returnByValue: true,
      });
      seq.push(f.result.value);
      await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
      await sleep(60);
    }

    results.push({ name, vk, vw: W, pageH: (await send('Runtime.evaluate', { expression: 'document.documentElement.scrollHeight', returnByValue: true })).result.value, axe, touch: JSON.parse(touch.result.value), tabSeq: seq });
    console.log(`${vk} ${name}: violations ${axe.violations.length} | 触控未达标 ${JSON.parse(touch.result.value).length} | incomplete [${axe.incomplete.join(',')}]`);
    for (const v of axe.violations) console.log(`   [${v.impact}] ${v.id} ×${v.n} — ${v.help}`);
  }
}
fs.mkdirSync(OUT.split('/').slice(0, -1).join('/'), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify({ results, exceptions: errs.slice(0, 10) }, null, 2));
console.log('\nexceptions:', JSON.stringify(errs.slice(0, 5)));
console.log('written ' + OUT);
ws.close(); child.kill();
