// 本地只读数据代理：把 dev 的 127.0.0.1:8765 转发到生产，只放 GET/HEAD。
// 目的：让本地 dev 拿到真实数据，做「改前 / 改后」同数据条件下的对比。
// 非 GET 一律 502 —— 这个代理在物理上不可能改动生产。
import http from 'http';
const UPSTREAM = process.env.UPSTREAM || 'http://47.93.14.11';
const PORT = Number(process.env.PORT || 8765);
let denied = 0, passed = 0;
http.createServer((req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, HEAD, OPTIONS',
      'access-control-allow-headers': req.headers['access-control-request-headers'] || '*',
      'access-control-max-age': '600',
    });
    res.end();
    return;
  }
  if (!['GET', 'HEAD'].includes(req.method)) {
    denied++;
    res.writeHead(502, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: 'readonly-proxy: 非 GET 已拒绝', method: req.method, path: req.url }));
    console.log('DENY ' + req.method + ' ' + req.url);
    return;
  }
  passed++;
  const up = http.request(UPSTREAM + req.url, { method: 'GET', headers: { 'user-agent': 'yisu-local-audit' } }, (p) => {
    const h = { ...p.headers };
    delete h['content-encoding']; delete h['content-length']; delete h['transfer-encoding'];
    h['access-control-allow-origin'] = '*';
    res.writeHead(p.statusCode, h);
    p.pipe(res);
  });
  up.on('error', (e) => { res.writeHead(502); res.end('upstream error ' + e.message); });
  up.end();
}).listen(PORT, '127.0.0.1', () => console.log('只读代理已启动 127.0.0.1:' + PORT + ' -> ' + UPSTREAM));
