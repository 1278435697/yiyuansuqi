// 生产站逐路由体检：控制台报错 / 网络失败 / 裂图 / 横向溢出 / 点击被抢占的图
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const ROUTES = [
  '/', '/pattern', '/fabric', '/archive', '/archive/1', '/timeline', '/geomap',
  '/tryon', '/accessories', '/heritage', '/aiqa', '/user', '/costume', '/textile'
];

async function main() {
  const base = process.argv[2];
  const port = 9431;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/yssweep' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let ws;
  for (let i = 0; i < 60; i++) {
    try {
      const j = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const t = j.find(x => x.type === 'page');
      if (t) { ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; }); break; }
    } catch (e) { await sleep(250); }
  }
  let id = 0; const pending = {}; const events = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending[m.id]) { pending[m.id](m); delete pending[m.id]; return; }
    events.push(m);
  };
  const send = (m, p) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async (x) => {
    const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return 'EXC ' + JSON.stringify((r.result.exceptionDetails.exception || {}).description || r.result.exceptionDetails.text);
    return r.result.result.value;
  };

  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Network.enable', {}); await send('Log.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: Number(process.argv[3]||1440), height: Number(process.argv[4]||900), deviceScaleFactor: 1, mobile: false });

  const SNAP = `(function(){
    var imgs=[].slice.call(document.images);
    var broken=imgs.filter(function(i){return i.complete&&i.naturalWidth===0}).map(function(i){return (i.currentSrc||i.src||"").replace(location.origin,"")+" [alt="+(i.alt||"空")+"]"});
    var de=document.documentElement;
    var over=de.scrollWidth-de.clientWidth;
    var wide=[];
    if(over>2){[].slice.call(document.querySelectorAll("body *")).forEach(function(e){var r=e.getBoundingClientRect();if(r.width>de.clientWidth+4&&r.height>0&&r.top<de.clientHeight)wide.push((e.className&&String(e.className).slice(0,40)||e.tagName)+" w="+Math.round(r.width))});}
    var hijack=[];
    imgs.forEach(function(i){if(i.closest(".museum")||i.closest("[data-lb-native]"))return;
      var h=i.closest("a,button");
      if(h&&h!==i)hijack.push((i.alt||"无alt").slice(0,28)+" 在"+h.tagName+"内");});
    return JSON.stringify({img:imgs.length,broken:broken,hijack:hijack.slice(0,6),
      overflow:over,wide:wide.slice(0,5),
      title:document.title,
      empty:document.body.innerText.replace(/\\s+/g,"").length,
      h1:[].slice.call(document.querySelectorAll("h1")).length,
      focusables:document.querySelectorAll("a[href],button:not([disabled]),input:not([type=hidden]),select,textarea,[tabindex]:not([tabindex='-1'])").length});
  })()`;

  const rows = [];
  for (const r of ROUTES) {
    events.length = 0;
    await send('Page.navigate', { url: base + r });
    await sleep(6000);
    await ev(`new Promise(function(res){window.scrollTo(0,document.body.scrollHeight);setTimeout(function(){window.scrollTo(0,0);res(1)},1200)})`);
    await sleep(1500);
    let snap;
    try { snap = JSON.parse(await ev(SNAP)); } catch (e) { snap = { err: String(e).slice(0, 80) }; }
    const netFail = events.filter(m => m.method === 'Network.loadingFailed')
      .map(m => (m.params.type || '') + ' ' + (m.params.errorText || '') + ' ' + ((m.params.request && m.params.request.url) || ''))
      .filter(s => !/aborted|ERR_INSUFFICIENT_RESOURCES/i.test(s));
    const badStatus = [];
    for (const m of events) {
      if (m.method === 'Network.responseReceived' && m.params.response && m.params.response.status >= 400)
        badStatus.push(m.params.response.status + ' ' + m.params.response.url.replace(base, ''));
    }
    const consoleErr = events.filter(m => m.method === 'Runtime.consoleAPICalled' && (m.params.type === 'error' || m.params.type === 'warning'))
      .map(m => (m.params.args || []).map(a => a.value !== undefined ? String(a.value) : (a.description || a.type)).join(' ').slice(0, 140));
    const pageErr = events.filter(m => m.method === 'Runtime.exceptionThrown')
      .map(m => ((m.params.exceptionDetails.exception || {}).description || m.params.exceptionDetails.text || '').split('\n')[0].slice(0, 140));
    const logErr = events.filter(m => m.method === 'Log.entryAdded' && m.params.entry.level === 'error')
      .map(m => (m.params.entry.text || '').slice(0, 120));

    rows.push({ r, ...snap, netFail, badStatus, consoleErr, pageErr, logErr });
    console.log('\n### ' + r);
    console.log('  图 ' + snap.img + ' 裂 ' + snap.broken.length + ' | 溢出 ' + snap.overflow + 'px | 正文 ' + snap.empty + ' 字 | h1 ' + snap.h1 + ' | 可聚焦 ' + snap.focusables);
    if (snap.broken.length) console.log('  裂图: ' + snap.broken.join(' , '));
    if (snap.wide && snap.wide.length) console.log('  超宽: ' + snap.wide.join(' / '));
    if (snap.hijack && snap.hijack.length) console.log('  A/BUTTON 内的 img: ' + snap.hijack.join(' / '));
    if (badStatus.length) console.log('  4xx/5xx: ' + [...new Set(badStatus)].join(' | '));
    if (netFail.length) console.log('  网络失败: ' + [...new Set(netFail)].join(' | '));
    if (pageErr.length) console.log('  JS异常: ' + [...new Set(pageErr)].join(' | '));
    if (consoleErr.length) console.log('  控制台: ' + [...new Set(consoleErr)].slice(0, 4).join(' || '));
    if (logErr.length) console.log('  日志错误: ' + [...new Set(logErr)].join(' | '));
  }
  require('fs').writeFileSync(__dirname + '/sweep_prod.json', JSON.stringify(rows, null, 1));
  ws.close(); child.kill();
  console.log('\nDONE');
}
main();
