// 线上复核刀1 的另一处：空态描述文字对比度（改前 3.36 / 目标 >=4.5）
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const MEASURE = `
(function(){
  function lum(c){var s=c.map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)});
    return 0.2126*s[0]+0.7152*s[1]+0.0722*s[2];}
  function parse(str){var m=str.match(/[\\d.]+/g);return m?m.slice(0,3).map(Number):null;}
  function bgOf(el){var e=el;while(e&&e!==document.documentElement){var b=getComputedStyle(e).backgroundColor;
    var m=b.match(/rgba?\\(([^)]*)\\)/); if(m){var parts=m[1].split(',');var alpha=parts.length>3?Number(parts[3]):1;
      if(alpha>0.99) return {c:parts.slice(0,3).map(Number),from:String(e.className||e.tagName)};}
    e=e.parentElement;}
    return {c:[255,255,255],from:'fallback'};}
  var t=document.querySelector('.el-empty__description p, .ys-empty, .empty-tip, .no-data');
  if(!t) return JSON.stringify({有空态:false});
  var cs=getComputedStyle(t), fg=parse(cs.color), bg=bgOf(t.parentElement||t);
  var L1=lum(fg),L2=lum(bg.c);var ratio=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
  return JSON.stringify({有空态:true, 前景:cs.color, 背景:'rgb('+bg.c.join(',')+') 来自 '+String(bg.from).slice(0,30),
    字号:cs.fontSize, 对比度:Math.round(ratio*100)/100, AA正文:ratio>=4.5});
})()
`;

async function main() {
  const port = 9423;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysct' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify(r.result.exceptionDetails.exception || r.result.exceptionDetails.text); return r.result.result.value; };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  for (const path of ['/tryon/history','/tryon/gallery','/pattern','/user']) {
    await send('Page.navigate', { url: process.argv[2] + path });
    await sleep(7000);
    console.log(path.padEnd(16), await ev(MEASURE));
  }
  ws.close(); child.kill();
}
main();
