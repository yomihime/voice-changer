'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const net = require('node:net');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { startFrontend, backendUrl } = require('../server.cjs');

test('backend accepts only an explicit IPv4 loopback HTTP origin', () => {
  assert.equal(backendUrl('http://127.0.0.1:18000').port, '18000');
  for (const url of ['http://example.com/', 'file:///tmp', 'http://user@127.0.0.1/',
    'http://127.0.0.1/api/', 'http://127.0.0.1/?redirect=1']) assert.throws(() => backendUrl(url));
});

test('static UI, multipart proxy, failure and same-origin isolation', async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vc-frontend-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(path.join(root, 'index.html'), '<h1>UI</h1>');
  const backend = http.createServer((req, res) => {
    let data = '';
    req.on('data', chunk => { data += chunk; });
    req.on('end', () => { res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ url: req.url, method: req.method, type: req.headers['content-type'], data })); });
  });
  await new Promise(resolve => backend.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => backend.close(resolve)));
  const service = await startFrontend({ directory: root, backend: `http://127.0.0.1:${backend.address().port}`, port: 0 });
  t.after(() => service.close());
  assert.equal(await (await fetch(service.url)).text(), '<h1>UI</h1>');
  const payload = '--boundary\r\nContent-Disposition: form-data; name="audio"\r\n\r\n123\r\n--boundary--';
  const result = await (await fetch(service.url + 'api/voice-changer/convert_chunk_bulk?slot=0', {
    method: 'POST', headers: { 'Content-Type': 'multipart/form-data; boundary=boundary' }, body: payload,
  })).json();
  assert.equal(result.data, payload);
  assert.equal(result.method, 'POST');
  assert.equal(result.url, '/api/voice-changer/convert_chunk_bulk?slot=0');
  assert.equal(result.type, 'multipart/form-data; boundary=boundary');
  assert.equal((await fetch(service.url + 'api/test', { headers: { Origin: 'https://untrusted.invalid' } })).status, 403);
  const wrongHost = await new Promise((resolve, reject) => {
    http.get(service.url, { headers: { Host: 'untrusted.invalid' } }, res => {
      res.resume(); resolve(res.statusCode);
    }).on('error', reject);
  });
  assert.equal(wrongHost, 403);
  assert.equal((await fetch(service.url + '%2e%2e%5coutside')).status, 403);
  assert.equal((await fetch(service.url + 'index.html', { method: 'POST' })).status, 405);
  const offline = await startFrontend({ directory: root, port: 0 });
  assert.equal((await fetch(offline.url + 'api/test')).status, 503);
  await offline.close();
  await new Promise(resolve => backend.close(resolve));
  assert.equal((await fetch(service.url + 'api/test')).status, 502);
});

test('WebSocket upgrade is forwarded and closing the frontend closes both peers', async t => {
  const backend = http.createServer();
  const peers = new Set();
  backend.on('upgrade', (_req, socket) => {
    peers.add(socket); socket.on('close', () => peers.delete(socket));
    socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n');
    socket.on('data', data => socket.write(data));
  });
  await new Promise(resolve => backend.listen(0, '127.0.0.1', resolve));
  t.after(() => { for (const peer of peers) peer.destroy(); backend.close(); });
  const service = await startFrontend({ directory: path.join(__dirname, '../public'),
    backend: `http://127.0.0.1:${backend.address().port}`, port: 0 });
  t.after(() => service.close());
  const url = new URL(service.url);
  const socket = net.connect(Number(url.port), url.hostname);
  t.after(() => socket.destroy());
  const result = new Promise((resolve, reject) => {
    let data = '';
    socket.on('error', reject);
    socket.on('data', chunk => { data += chunk; if (data.includes('ping-test')) resolve(data); });
  });
  socket.write(`GET /socket.io/?transport=websocket HTTP/1.1\r\nHost: ${url.host}\r\nOrigin: ${url.origin}\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n\r\nping-test`);
  const text = await result;
  assert.match(text, /101 Switching Protocols/);
  const closed = new Promise(resolve => socket.once('close', resolve));
  await service.close();
  await closed;
});
