'use strict';
// Hidden, synthetic integration check. Never loads the real UI, captures audio,
// chooses physical output devices, or opens an external browser.
const { app, BrowserWindow } = require('electron');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { spawn } = require('node:child_process');
const { startDesktop } = require('./runtime.cjs');
const { audioRequestAllowed } = require('./policy.cjs');

async function run(directory) {
  process.env.VCCLIENT_DESKTOP_SELF_TEST = '1';
  // The mock fixture must be runnable on a headless build host without a GPU.
  // This is test-only; production keeps Electron's normal hardware path.
  app.disableHardwareAcceleration();
  // Some Windows CI/service sessions cannot create a Chromium sandbox token.
  // Keep this relaxation confined to the synthetic test entry point.
  app.commandLine.appendSwitch('no-sandbox');
  fs.mkdirSync(directory, { recursive: true });
  const timeout = setTimeout(() => app.exit(1), 45000);
  const children = [];
  app.on('will-quit', () => { for (const child of children) if (child.exitCode === null) child.kill(); });
  let uploaded = '';
  const server = http.createServer((request, response) => {
    if (request.url === '/upload') {
      request.on('data', data => { uploaded += data.toString(); });
      request.on('end', () => response.end('ok'));
    } else {
      response.setHeader('Content-Type', 'text/html');
      response.end('<!doctype html><title>Fixture</title><h1>VCClient desktop test</h1><input type="file" id="upload"><div id="drop">Drop fixture</div>');
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  app.on('will-quit', () => server.close());
  const url = `http://127.0.0.1:${server.address().port}/`;
  const external = [], requests = [];
  const profileRoot = path.join(directory, 'profiles');
  let instances = 0;
  const client = await startDesktop({ url, profileRoot, hidden: true, denyMedia: true }, {
    openExternal: value => external.push(value),
    permissionRequest: (permission, details) => requests.push({ permission, details }),
    secondInstance: () => { instances++; },
  });
  const { win, session } = client;
  assert.equal(win.isVisible(), false);
  assert.equal(win.getTitle(), 'VCClient Desktop');
  const features = await win.webContents.executeJavaScript(`({
    node: typeof require, process: typeof process, bridge: typeof window.electronAPI,
    secure: isSecureContext, media: typeof navigator.mediaDevices.getUserMedia,
    worklet: typeof AudioWorkletNode, sink: typeof HTMLMediaElement.prototype.setSinkId
  })`);
  assert.equal(features.node, 'undefined');
  assert.equal(features.process, 'undefined');
  assert.equal(features.bridge, 'undefined');
  assert.equal(features.secure, true);
  for (const key of ['media', 'worklet', 'sink']) assert.equal(features[key], 'function');
  const media = await win.webContents.executeJavaScript(`navigator.mediaDevices.getUserMedia({audio:true})
    .then(stream => { stream.getTracks().forEach(t => t.stop()); return 'UNEXPECTED_CAPTURE'; })
    .catch(error => error.name)`);
  assert.equal(media, 'NotAllowedError');
  // Validate the actual Electron request fields, without granting capture.
  const audio = requests.find(item => item.permission === 'media');
  assert.ok(audio, 'Electron must emit a real media permission request');
  assert.equal(audioRequestAllowed(audio.permission, audio.details, new URL(url).origin), true);

  await win.webContents.executeJavaScript(`window.open('https://github.com/w-okada/voice-changer', '_blank'); void 0`, true);
  await win.webContents.executeJavaScript(`window.open('file:///C:/Windows/notepad.exe', '_blank'); void 0`, true);
  await new Promise(resolve => setTimeout(resolve, 150));
  assert.deepEqual(external, ['https://github.com/w-okada/voice-changer']);
  assert.equal(BrowserWindow.getAllWindows().length, 1);
  await win.webContents.executeJavaScript(`location.href='https://example.invalid/'; void 0`);
  await new Promise(resolve => setTimeout(resolve, 100));
  assert.equal(win.webContents.getURL(), url);

  const upload = await win.webContents.executeJavaScript(`(async()=>{
    const transfer = new DataTransfer(); transfer.items.add(new File(['fixture upload'], 'fixture.txt'));
    document.querySelector('#upload').files=transfer.files;
    const form=new FormData(); form.append('file',document.querySelector('#upload').files[0]);
    return await (await fetch('/upload',{method:'POST',body:form})).text();
  })()`);
  assert.equal(upload, 'ok');
  assert.ok(uploaded.includes('fixture upload'));
  const storage = await win.webContents.executeJavaScript(`(async()=>{
    localStorage.setItem('desktop-test','retained');
    await new Promise((resolve,reject)=>{const request=indexedDB.open('desktop-test',1);
      request.onupgradeneeded=()=>request.result.createObjectStore('settings');
      request.onerror=()=>reject(request.error);
      request.onsuccess=()=>{const db=request.result;const tx=db.transaction('settings','readwrite');
        tx.objectStore('settings').put('retained','key');tx.oncomplete=()=>{db.close();resolve();};};});
    return true;
  })()`);
  assert.equal(storage, true);
  session.flushStorageData();
  await win.loadURL(url);
  assert.equal(await win.webContents.executeJavaScript(`localStorage.getItem('desktop-test')`), 'retained');
  const preferences = win.webContents.getLastWebPreferences();
  for (const key of ['sandbox', 'contextIsolation', 'webSecurity']) assert.equal(preferences[key], true);
  assert.equal(preferences.nodeIntegration, false);
  // Electron 44 omits this field from getLastWebPreferences even though the
  // BrowserWindow option is accepted; treat an omitted value as its default.
  assert.equal(preferences.backgroundThrottling ?? false, false);

  function child(extra) {
    const proc = spawn(process.execPath, ['--no-sandbox', '--disable-gpu', '--profile-root', profileRoot,
      '--deny-media', '--hidden', ...extra, '--url', url], {
      windowsHide: true,
      stdio: ['ignore', fs.openSync(path.join(directory, `child-${children.length}.out`), 'w'),
        fs.openSync(path.join(directory, `child-${children.length}.err`), 'w')],
    });
    children.push(proc);
    return proc;
  }
  const activated = child([]);
  const activationExit = await new Promise((resolve, reject) => {
    activated.on('error', reject); activated.on('exit', resolve);
  });
  assert.equal(activationExit, 10, 'normal activation has an explicit reused result');
  const waiter = child(['--wait']);
  await new Promise(resolve => setTimeout(resolve, 700));
  assert.equal(waiter.exitCode, null, 'owning launcher waits for the real window lifetime');
  assert.ok(instances >= 2);
  const image = await win.webContents.capturePage();
  fs.writeFileSync(path.join(directory, 'mock-window.png'), image.toPNG());
  // Delay application shutdown to observe that the waiter exits after the window's
  // lifetime signal. Production before-quit sends the same pipe close.
  app.removeAllListeners('window-all-closed');
  win.close();
  app.emit('before-quit', { preventDefault() {} });
  const waitExit = await new Promise(resolve => waiter.on('exit', resolve));
  assert.equal(waitExit, 0);
  const report = { passed: true, electron: process.versions.electron, packaged: app.isPackaged,
    executable: process.execPath, features, media, permissionRequests: requests, external,
    upload: true, reloadPersistence: true, activationExit, waitExit, instances, profile: client.profile,
    actualAudioCapture: false, actualAudioPlayback: false };
  fs.writeFileSync(path.join(directory, 'report.json'), JSON.stringify(report, null, 2));
  clearTimeout(timeout);
  app.exit(0);
}

module.exports = { run };
