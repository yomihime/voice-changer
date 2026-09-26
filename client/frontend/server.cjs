'use strict';
// Shared by Node development and Electron. Never owns the inference process.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon',
  '.wav': 'audio/wav', '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8' };
function backendUrl(value) {
  if (!value) return null;
  const url = new URL(value);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password ||
      url.pathname !== '/' || url.search || url.hash) throw new Error('Backend must be http://127.0.0.1:<port>/');
  return url;
}
function startFrontend({ directory, backend, port = 21416 }) {
  const root = fs.realpathSync(directory);
  const target = backendUrl(backend);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Invalid frontend port');
  const sockets = new Set(), upstreams = new Set();
  let origin;
  function fail(res, status, error) {
    res.writeHead(status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error }));
  }
  function allowed(req) {
    return req.headers.host === new URL(origin).host &&
      (!req.headers.origin || req.headers.origin === origin) &&
      req.headers['sec-fetch-site'] !== 'cross-site';
  }
  function request(req, callback) {
    const upstream = http.request({ hostname: target.hostname, port: target.port || 80,
      method: req.method, path: req.url, headers: { ...req.headers, host: target.host } }, callback);
    upstreams.add(upstream);
    upstream.on('close', () => upstreams.delete(upstream));
    // Inference/model uploads can take time, but a dead service must not hang forever.
    upstream.setTimeout(300000, () => upstream.destroy(new Error('Backend timeout')));
    return upstream;
  }
  const server = http.createServer((req, res) => {
    if (!allowed(req)) return fail(res, 403, 'Cross-origin requests are not allowed');
    let pathname;
    try { pathname = decodeURIComponent(new URL(req.url, origin).pathname); }
    catch { return fail(res, 400, 'Invalid path'); }
    if (pathname.includes('\0')) return fail(res, 400, 'Invalid path');
    if (/^\/(api(?:\/|_)|socket\.io\/|model_dir\/|upload_dir\/|tmp_dir\/)/.test(pathname) || pathname === '/vcclient.log') {
      if (!target) return fail(res, 503, 'No 2.x backend configured');
      const upstream = request(req, reply => { res.writeHead(reply.statusCode, reply.headers); reply.pipe(res); });
      upstream.on('error', error => { if (!res.headersSent) fail(res, 502, error.message); else res.destroy(); });
      res.on('close', () => upstream.destroy());
      req.pipe(upstream);
      return;
    }
    if (!['GET', 'HEAD'].includes(req.method)) return fail(res, 405, 'Static files are read-only');
    const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(root + path.sep)) return fail(res, 403, 'Outside document root');
    try {
      if (!fs.statSync(file).isFile()) return fail(res, 404, 'File not found');
      if (!fs.realpathSync(file).startsWith(root + path.sep)) return fail(res, 403, 'Outside document root');
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' });
      if (req.method === 'HEAD') res.end();
      else fs.createReadStream(file).on('error', () => res.destroy()).pipe(res);
    } catch { fail(res, 404, 'File not found'); }
  });
  server.on('connection', socket => { sockets.add(socket); socket.on('close', () => sockets.delete(socket)); });
  server.on('upgrade', (req, socket, head) => {
    if (!allowed(req) || !target || !req.url.startsWith('/socket.io/')) return socket.destroy();
    const upstream = request(req);
    upstream.on('upgrade', (reply, peer, peerHead) => {
      sockets.add(peer); peer.on('close', () => sockets.delete(peer));
      socket.write(`HTTP/1.1 ${reply.statusCode} ${reply.statusMessage}\r\n` +
        Object.entries(reply.headers).map(([key, value]) => `${key}: ${value}\r\n`).join('') + '\r\n');
      if (head.length) peer.write(head);
      if (peerHead.length) socket.write(peerHead);
      peer.on('error', () => socket.destroy()); socket.on('error', () => peer.destroy());
      peer.on('close', () => socket.destroy()); socket.on('close', () => peer.destroy());
      socket.pipe(peer).pipe(socket);
    });
    upstream.on('response', reply => { reply.resume(); socket.destroy(); });
    upstream.on('error', () => socket.destroy());
    upstream.end();
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => {
      origin = `http://127.0.0.1:${server.address().port}`;
      if (target?.origin === origin) { server.close(); reject(new Error('Frontend and backend ports must differ')); return; }
      resolve({ url: origin + '/', close: () => {
        for (const upstream of upstreams) upstream.destroy();
        for (const socket of sockets) socket.destroy();
        return new Promise(done => server.close(done));
      } });
    });
  });
}
module.exports = { startFrontend, backendUrl };
