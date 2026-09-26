'use strict';

const { app, BrowserWindow, dialog, Menu, shell, session } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const crypto = require('node:crypto');
const { serverUrl, sameOrigin, externalUrl, profileDirectory, audioRequestAllowed } = require('./policy.cjs');
const { installWindowNavigation } = require('./window-navigation.cjs');

async function startDesktop(options, hooks = {}) {
  const url = serverUrl(options.url);
  const origin = new URL(url).origin;
  // In a package the application lives in <repo>/.runtime/desktop/resources/app.
  // In a packaged build app/resources/app is four levels below the checkout;
  // during source runs client/desktop is only two levels below it.
  const installation = fs.realpathSync(path.resolve(__dirname,
    app.isPackaged ? '../../../..' : '../..'));
  const root = options.profileRoot || path.join(process.env.LOCALAPPDATA || app.getPath('appData'),
    'Yomihime', 'VoiceChanger', 'Desktop');
  const profile = profileDirectory(root, installation, origin);
  fs.mkdirSync(profile, { recursive: true });
  app.setName('VCClient Desktop');
  app.setAppUserModelId('io.github.yomihime.voicechanger.desktop');
  app.setPath('userData', profile);
  app.setPath('sessionData', profile);
  const pipe = `\\\\.\\pipe\\vcclient-desktop-${crypto.createHash('sha256').update(profile).digest('hex')}`;
  if (!app.requestSingleInstanceLock()) {
    if (options.wait) {
      // An owning launcher must wait for the existing window, not the short-lived
      // activation process. This channel has no renderer access or commands.
      const deadline = Date.now() + 10000;
      const connect = () => {
        const socket = net.connect(pipe);
        let connected = false;
        socket.on('connect', () => { connected = true; });
        socket.on('error', () => {
          if (!connected && Date.now() < deadline) setTimeout(connect, 100);
          else process.exit(1);
        });
        socket.on('end', () => app.exit(0));
        socket.on('close', () => { if (connected) process.exit(0); });
      };
      connect();
    } else process.exit(10);
    return null;
  }
  const waiters = new Set();
  const lifetime = net.createServer(socket => {
    waiters.add(socket);
    socket.on('error', () => socket.destroy());
    socket.on('close', () => waiters.delete(socket));
  });
  await new Promise((resolve, reject) => { lifetime.once('error', reject); lifetime.listen(pipe, resolve); });
  app.on('before-quit', () => {
    lifetime.close();
    for (const socket of waiters) socket.end();
  });

  let win;
  app.on('second-instance', () => {
    if (win && !win.isDestroyed()) {
      if (win.isMinimized()) win.restore();
      if (!options.hidden) { win.show(); win.focus(); }
      hooks.secondInstance?.();
    }
  });
  app.on('window-all-closed', () => app.quit());
  await app.whenReady();
  const ses = session.defaultSession;
  // Approval is remembered only for this process. Closing the window releases capture.
  let microphoneAllowed = false;
  let microphonePrompt;
  ses.setPermissionCheckHandler((contents, permission, requestingOrigin, details = {}) => {
    return !options.denyMedia && microphoneAllowed && contents === win?.webContents &&
      permission === 'media' && details.isMainFrame === true && details.mediaType === 'audio' &&
      sameOrigin(requestingOrigin, origin) && sameOrigin(contents.getURL(), origin);
  });
  ses.setPermissionRequestHandler((contents, permission, callback, details) => {
    hooks.permissionRequest?.(permission, details);
    if (options.denyMedia || contents !== win?.webContents ||
        !sameOrigin(contents.getURL(), origin) || !audioRequestAllowed(permission, details, origin)) {
      callback(false);
      return;
    }
    if (!microphonePrompt) {
      microphonePrompt = dialog.showMessageBox(win, {
        type: 'question', title: 'マイクの使用',
        message: 'VCClient でマイクを使用しますか？',
        detail: '音声デバイスの確認と音声変換に使用します。この Client を閉じるとマイクの使用を終了します。',
        buttons: ['許可しない', '許可する'], defaultId: 0, cancelId: 0,
      }).then(result => { microphoneAllowed = result.response === 1; return microphoneAllowed; });
    }
    microphonePrompt.then(allowed => callback(allowed && !win.isDestroyed() &&
      sameOrigin(contents.getURL(), origin))).catch(() => callback(false));
  });
  // Electron asks this handler after the media permission callback for each
  // concrete device. Keep the allow decision scoped to this window/origin;
  // returning false unconditionally would make an approved microphone unusable.
  ses.setDevicePermissionHandler(details => {
    const requestingOrigin = details?.origin || details?.securityOrigin || details?.requestingOrigin;
    const deviceType = details?.deviceType || details?.mediaType;
    return !options.denyMedia && microphoneAllowed &&
      deviceType === 'microphone' && sameOrigin(requestingOrigin, origin);
  });
  ses.setDisplayMediaRequestHandler((_request, callback) => callback({}));
  ses.on('will-download', (event, item, contents) => {
    const source = item.getURL();
    if (contents !== win?.webContents || !sameOrigin(contents.getURL(), origin) ||
        !(sameOrigin(source, origin) || source.startsWith(`blob:${origin}/`))) event.preventDefault();
  });

  win = new BrowserWindow({
    title: 'VCClient Desktop', width: 1280, height: 900, minWidth: 900, minHeight: 640,
    show: false, autoHideMenuBar: true, icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false, contextIsolation: true, sandbox: true, webSecurity: true,
      webviewTag: false, spellcheck: false,
      // The window hosts a continuous audio processor even when minimized.
      backgroundThrottling: false,
    },
  });
  const openExternal = async value => {
    const target = externalUrl(value);
    if (!target) return;
    try { await (hooks.openExternal || shell.openExternal)(target); }
    catch (error) {
      if (!options.hidden) dialog.showErrorBox('VCClient Desktop', `リンクを開けませんでした。\n${error.message}`);
    }
  };
  installWindowNavigation(win, { origin, openExternal, hidden: options.hidden });
  win.webContents.on('page-title-updated', event => {
    event.preventDefault();
    win.setTitle('VCClient Desktop');
  });
  win.webContents.on('render-process-gone', (_event, details) => {
    if (details.reason !== 'clean-exit') {
      if (!options.hidden) dialog.showErrorBox('VCClient Desktop', 'Client が停止しました。Client を開き直してください。');
      app.exit(1);
    }
  });
  const reload = () => { void win.loadURL(url).catch(() => showConnectionError()); };
  const showConnectionError = () => {
    if (!options.hidden && !win.isDestroyed()) {
      void dialog.showMessageBox(win, {
        type: 'error', title: 'VCClient Desktop', message: 'Server に接続できません。',
        detail: 'Server の状態を確認し、メニューから再読み込みしてください。',
        buttons: ['OK'],
      });
    }
  };
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    { label: 'Client', submenu: [
      { label: '再読み込み', accelerator: 'CmdOrCtrl+R', click: reload },
      { label: 'マイクの許可を再確認', click: () => { microphoneAllowed = false; microphonePrompt = undefined; reload(); } },
      { type: 'separator' }, { label: '終了', accelerator: 'Alt+F4', click: () => win.close() },
    ] },
    { label: '編集', submenu: [{ role: 'undo' }, { role: 'redo' }, { type: 'separator' },
      { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }] },
    { label: '表示', submenu: [{ role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }] },
  ]));
  try { await win.loadURL(url); } catch { showConnectionError(); }
  win.setTitle('VCClient Desktop');
  if (!options.hidden && !win.isDestroyed()) win.show();
  return { win, profile, session: ses };
}

module.exports = { startDesktop };
