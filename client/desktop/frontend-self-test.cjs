'use strict';
// Real packaged UI, unavailable backend, denied media; no microphone or inference.
const { app, BrowserWindow } = require('electron');
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
  // Exercise the recovered lazy module as well as the initial entry point.
  assert.equal(await win.webContents.executeJavaScript(
    `import('/recovered/browser-ponyfill-8xTspxQN.js').then(module => typeof module.b)`), 'object');
  await win.webContents.executeJavaScript(`window.open(location.origin + '/?app_mode=LogViewer', '_blank'); void 0`, true);
  let logWindow;
  for (let attempt = 0; attempt < 60; attempt++) {
    logWindow = BrowserWindow.getAllWindows().find(candidate => candidate !== win);
    if (logWindow && !logWindow.webContents.isLoading() && logWindow.webContents.getURL().includes('app_mode=LogViewer')) break;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(logWindow, 'Log button must open its supported window');
  assert.equal(logWindow.isVisible(), false, 'Hidden tests must not expose windows');
  assert.equal(new URL(logWindow.webContents.getURL()).searchParams.get('app_mode'), 'LogViewer');
  assert.equal(await logWindow.webContents.executeJavaScript('typeof require'), 'undefined');
  let mainReloaded = false;
  const markReload = () => { mainReloaded = true; };
  win.webContents.on('did-start-loading', markReload);
  await logWindow.webContents.executeJavaScript(`window.__logShortcutSeen = false;
    window.addEventListener('keydown', event => {
      if (event.ctrlKey && event.key === 'r') window.__logShortcutSeen = true;
    });`);
  logWindow.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'R', modifiers: ['control'] });
  logWindow.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'R', modifiers: ['control'] });
  await new Promise(resolve => setTimeout(resolve, 100));
  assert.equal(await logWindow.webContents.executeJavaScript('window.__logShortcutSeen'), true,
    'LogViewer must receive its own refresh shortcut');
  assert.equal(mainReloaded, false, 'A log shortcut must not reload the audio client');
  win.webContents.removeListener('did-start-loading', markReload);
  const childCapture = await logWindow.webContents.executeJavaScript(`navigator.mediaDevices.getUserMedia({audio:true})
    .then(stream => { stream.getTracks().forEach(track => track.stop()); return 'UNEXPECTED_CAPTURE'; })
    .catch(error => error.name)`);
  assert.equal(childCapture, 'NotAllowedError');
  await win.webContents.executeJavaScript(`window.open(location.origin + '/?app_mode=LogViewer', '_blank'); void 0`, true);
  await logWindow.webContents.executeJavaScript(`window.open(location.origin, '_blank'); void 0`, true);
  assert.equal(BrowserWindow.getAllWindows().length, 2, 'Log windows are reused and cannot open other windows');
  logWindow.close();
  assert.equal(win.isDestroyed(), false, 'Closing logs must leave the main client alive');
  fs.writeFileSync(path.join(directory, 'frontend.png'), (await win.webContents.capturePage()).toPNG());
  fs.writeFileSync(path.join(directory, 'report.json'), JSON.stringify({ passed: true, packaged: app.isPackaged,
    electron: process.versions.electron, state, adapter, logViewer: true, actualAudioCapture: false }, null, 2));
  clearTimeout(timeout);
  win.close();
}
module.exports = { run };
