/* 本地验收用的只读外壳：静态伺服 dist，GET/HEAD 转发到生产 API。
   非 GET 一律 405 —— 这套 harness 不可能对生产做任何写入。 */
const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const DIST = "D:/yisu-ai-platform/frontend/dist";
const UPSTREAM = "http://47.93.14.11";
const PORT = Number(process.argv[2] || 5399);
const PROXY_PREFIX = ["/api", "/uploads", "/images"];

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webp": "image/webp",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".ttf": "font/ttf",
  ".txt": "text/plain; charset=utf-8",
  ".map": "application/json",
};

function proxyGet(req, res) {
  const upstream = http.request(
    UPSTREAM + req.url,
    { method: req.method, headers: { "user-agent": "local-render-harness", accept: req.headers.accept || "*/*" } },
    (r) => {
      res.writeHead(r.statusCode || 502, r.headers);
      r.pipe(res);
    }
  );
  upstream.on("error", (e) => {
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: String(e.message) }));
  });
  upstream.end();
}

function serveStatic(req, res, pathname) {
  let file = path.join(DIST, pathname);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(DIST, "index.html");
  const ext = path.extname(file).toLowerCase();
  res.writeHead(200, {
    "content-type": MIME[ext] || "application/octet-stream",
    "cache-control": "no-store",
  });
  fs.createReadStream(file).pipe(res);
}

http
  .createServer((req, res) => {
    const pathname = new URL(req.url, "http://localhost").pathname;
    if (PROXY_PREFIX.some((p) => pathname.startsWith(p))) {
      if (req.method === "GET" || req.method === "HEAD") return proxyGet(req, res);
      res.writeHead(405, { "content-type": "application/json" });
      return res.end(JSON.stringify({ error: "read-only harness: " + req.method + " blocked" }));
    }
    serveStatic(req, res, pathname);
  })
  .listen(PORT, "127.0.0.1", () => console.log("harness on http://127.0.0.1:" + PORT));
