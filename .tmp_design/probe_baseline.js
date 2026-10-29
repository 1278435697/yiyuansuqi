// 线上现状探针：这些文字只有「在途工作树」才有，用来判断线上是否已含他的未提交改动
const { spawn } = require('child_process');
const os = require('os');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const MARKERS = ['创建纹样', '用户作品', '华夏衣冠志', '虚拟试穿', '衣冠', '返回列表', '返回上一纹样', '删除纹样', '常见搭配纹样', '实物文物图'];

async function main() {
  const port = 9421;
  const child = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${port}`,
      '--user-data-dir=' + os.tmpdir() + '/ysbase' + port, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
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
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true }); if (r.result.exceptionDetails) return 'EXC'; return r.result.result.value; };
  await send('Page.enable', {}); await send('Runtime.enable', {});
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  const probe = async (label, url) => {
    await send('Page.navigate', { url });
    await sleep(5000);
    const txt = await ev('document.body.innerText');
    const found = MARKERS.filter(m => String(txt).includes(m));
    console.log(label.padEnd(22), '命中: ' + (found.join('、') || '无'));
  };
  const base = process.argv[2];
  await probe('线上 /pattern', base + '/pattern');
  await probe('线上 /pattern/32', base + '/pattern/32');
  await probe('线上 /', base + '/');
  console.log('标题          ', await ev('document.title'));
  ws.close(); child.kill();
}
main();
