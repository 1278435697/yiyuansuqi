const { spawn } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function run(url, W, H, port) {
  const args = ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
    '--user-data-dir=' + require('os').tmpdir() + '/ysm' + port, '--hide-scrollbars', 'about:blank'];
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', args, { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = l.find(x => x.type === 'page'); if (!t) throw new Error('no target');
      ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; }); break; }
    catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (pending[m.id]) { pending[m.id](m); delete pending[m.id]; } };
  const send = (method, params) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Runtime.enable', {});
  await send('Page.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: W < 800 });
  await send('Page.navigate', { url });
  await sleep(9000);
  const expr = `(function(){
    var out={};
    out.scrollW=document.documentElement.scrollWidth; out.clientW=document.documentElement.clientWidth; out.bodyW=document.body.scrollWidth;
    var of=[];document.querySelectorAll('.app-main *').forEach(function(n){
      if(n.scrollWidth-n.clientWidth>2 && getComputedStyle(n).overflowX!=='visible' && n.clientWidth>0)
        of.push({t:n.tagName+'.'+(n.className||'').toString().split(' ').slice(0,2).join('.'),sw:n.scrollWidth,cw:n.clientWidth,txt:(n.textContent||'').trim().slice(0,28)});
    });
    out.clipped=of.slice(0,12);
    var over=[];document.querySelectorAll('.app-main *').forEach(function(n){var r=n.getBoundingClientRect();
      if(r.width>0&&r.right>window.innerWidth+2) over.push({t:n.tagName+'.'+(n.className||'').toString().split(' ').slice(0,2).join('.'),right:Math.round(r.right)});});
    out.overflow=over.slice(0,12);
    var nav=document.querySelector('.tryon-subnav,.tryon-tabs,.app-main nav');
    out.nav=nav?{cls:nav.className.toString().slice(0,40),h:Math.round(nav.getBoundingClientRect().height),
      items:[].map.call(nav.querySelectorAll('button,.el-tabs__item,a'),function(b){var r=b.getBoundingClientRect();return {t:(b.textContent||'').trim().slice(0,8),w:Math.round(r.width),h:Math.round(r.height)};})}:null;
    var btns=[];document.querySelectorAll('.app-main button,.app-main .el-button').forEach(function(b){var r=b.getBoundingClientRect();
      if(r.width>0)btns.push({t:(b.textContent||'').trim().slice(0,10),w:Math.round(r.width),h:Math.round(r.height)});});
    btns.sort(function(a,b){return a.h-b.h}); out.btnShort=btns.slice(0,6); out.btnN=btns.length;
    var fs={};document.querySelectorAll('.app-main *').forEach(function(n){
      if(!n.children.length&&(n.textContent||'').trim()){var f=parseInt(getComputedStyle(n).fontSize);fs[f]=(fs[f]||0)+1;}});
    out.fontSizes=Object.keys(fs).map(Number).sort(function(a,b){return a-b;}).slice(0,4).map(function(k){return k+'px x'+fs[k];});
    return JSON.stringify(out);})()`;
  const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
  const v = res.result && res.result.result && res.result.result.value;
  ws.close(); child.kill();
  if (!v) throw new Error('eval失败 ' + JSON.stringify(res).slice(0, 400));
  return JSON.parse(v);
}

(async () => {
  const W = Number(process.env.W || 390), H = Number(process.env.H || 844);
  const routes = (process.env.ROUTES || 'tryon,gallery,history').split(',');
  const port = Number(process.env.PORT || 9390);
  for (const n of routes) {
    const sub = n === 'tryon' ? '' : n;
    for (const [side, base] of [['before', 'http://47.93.14.11'], ['after', 'http://localhost:5173']]) {
      const o = await run(`${base}/tryon/${sub}`, W, H, port + (side === 'before' ? 0 : 1));
      console.log(`\n### ${n} ${side} ${W}px`);
      console.log(`  横滚 docW=${o.scrollW} client=${o.clientW} body=${o.bodyW}`);
      console.log('  截断文字: ' + (o.clipped.length ? o.clipped.map(c => `${c.t}[${c.cw}<${c.sw}]${c.txt}`).join(' | ') : '无'));
      console.log('  越界元素: ' + (o.overflow.length ? o.overflow.map(c => `${c.t}@${c.right}`).join(' | ') : '无'));
      console.log('  导航: ' + (o.nav ? o.nav.cls + ' h=' + o.nav.h + ' ' + JSON.stringify(o.nav.items) : 'n/a'));
      console.log(`  最矮按钮(n=${o.btnN}): ` + o.btnShort.map(b => `${b.t||'?'} ${b.w}x${b.h}`).join(' | '));
      console.log('  最小字号: ' + o.fontSizes.join(', '));
    }
  }
})();
