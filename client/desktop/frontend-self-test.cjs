'use strict';
// Real packaged UI, unavailable backend, denied media; no microphone or inference.
const { app } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { startDesktop } = require('./runtime.cjs');
async function run(directory) {
  fs.mkdirSync(directory, { recursive: true });
  app.disableHardwareAcceleration();
  app.commandLine.appendSwitch('no-sandbox');
  const timeout = setTimeout(() => app.exit(1), 30000);
  const backend = http.createServer((_req, res) => {
    res.writeHead(503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Offline test fixture' }));
  });
  await new Promise(resolve => backend.listen(0, '127.0.0.1', resolve));
  app.on('before-quit', () => backend.close());
  const client = await startDesktop({ backend: `http://127.0.0.1:${backend.address().port}/`,
    profileRoot: path.join(directory, 'profiles'), denyMedia: true, hidden: true });
  const { win } = client;
  let state;
  for (let attempt = 0; attempt < 60; attempt++) {
    state = await win.webContents.executeJavaScript(`({
      text: document.querySelector('#root')?.textContent,
      disconnected: document.querySelector('#backend-status')?.hidden === false,
      node: typeof require, tauri: typeof window.__TAURI_INTERNALS__, secure: isSecureContext
    })`);
    if (state.text?.length > 30 && state.disconnected) break;
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  assert.ok(state.text?.length > 30, 'Recovered React app must render');
  assert.equal(state.disconnected, true);
  assert.equal(state.node, 'undefined');
  assert.equal(state.tauri, 'undefined');
  assert.equal(state.secure, true);
  const adapter = await win.webContents.executeJavaScript(`import('/src/desktop-adapter.js').then(async module => ({
    config: await module.invokeDesktop('get_shortcut_settings'),
    listener: typeof await module.listenDesktop('shortcut-action', () => {})
  }))`);
  assert.equal(adapter.config.enabled, false);
  assert.equal(adapter.listener, 'function');
  fs.writeFileSync(path.join(directory, 'frontend.png'), (await win.webContents.capturePage()).toPNG());
  fs.writeFileSync(path.join(directory, 'report.json'), JSON.stringify({ passed: true, packaged: app.isPackaged,
    electron: process.versions.electron, state, adapter, actualAudioCapture: false }, null, 2));
  clearTimeout(timeout);
  win.close();
}
module.exports = { run };
