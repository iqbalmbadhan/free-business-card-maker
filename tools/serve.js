#!/usr/bin/env node
// Serves dist/ locally: node tools/serve.js [port]  →  http://localhost:8080/business-card-maker/
// (The wallet's one-tap passes need PHP; everything else works here.)
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', 'dist');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.xml': 'application/xml', '.css': 'text/css', '.svg': 'image/svg+xml' };

function start(port = 8080) {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p === '/') {   // list the editions
      const eds = fs.readdirSync(ROOT).filter(d => fs.existsSync(path.join(ROOT, d, 'index.html')));
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(eds.map(d => `<p><a href="/${d}/">${d}</a></p>`).join(''));
    }
    let file = path.normalize(path.join(ROOT, p));
    if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
      if (!p.endsWith('/')) { res.writeHead(301, { Location: p + '/' }); return res.end(); }
      file = path.join(file, 'index.html');
    }
    if (!fs.existsSync(file)) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(resolve => server.listen(port, '127.0.0.1', () => resolve(server)));
}
module.exports = { start };
if (require.main === module) {
  const port = Number(process.argv[2]) || 8080;
  start(port).then(() => console.log(`Serving dist/ at http://localhost:${port}/`));
}
