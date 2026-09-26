'use strict';

const { BrowserWindow } = require('electron');
const { sameOrigin, logViewerUrl } = require('./policy.cjs');

function guardNavigation(contents, origin) {
  contents.on('will-frame-navigate', event => {
    if (!sameOrigin(event.url, origin)) event.preventDefault();
  });
  contents.on('will-redirect', (event, target) => {
    if (!sameOrigin(target, origin)) event.preventDefault();
  });
  contents.on('will-attach-webview', event => event.preventDefault());
}

// Own the one supported auxiliary window here, separately from audio permissions.
function installWindowNavigation(win, { origin, openExternal, hidden = false }) {
  let logWindow;
  guardNavigation(win.webContents, origin);
  win.on('closed', () => { if (logWindow && !logWindow.isDestroyed()) logWindow.destroy(); });
  win.webContents.setWindowOpenHandler(details => {
    if (!sameOrigin(win.webContents.getURL(), origin)) return { action: 'deny' };
    const target = logViewerUrl(details.url, origin);
    if (!target) {
      void openExternal(details.url);
      return { action: 'deny' };
    }
    if (logWindow && !logWindow.isDestroyed()) {
      if (!hidden) { if (logWindow.isMinimized()) logWindow.restore(); logWindow.show(); logWindow.focus(); }
      return { action: 'deny' };
    }
    logWindow = new BrowserWindow({
      parent: win, title: 'VCClient 日志', width: 1000, height: 720,
      minWidth: 640, minHeight: 400, show: false, autoHideMenuBar: true,
      webPreferences: {
        nodeIntegration: false, contextIsolation: true, sandbox: true,
        webSecurity: true, webviewTag: false, spellcheck: false,
      },
    });
    const child = logWindow;
    // The main menu owns client reload/quit. LogViewer has its own Ctrl+R
    // refresh toggle; closing this window must not stop the audio client.
    child.setMenu(null);
    child.webContents.setIgnoreMenuShortcuts(true);
    guardNavigation(child.webContents, origin);
    child.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    child.on('closed', () => { if (logWindow === child) logWindow = undefined; });
    void child.loadURL(target).then(() => {
      if (!hidden && !child.isDestroyed()) child.show();
    }).catch(() => { if (!child.isDestroyed()) child.destroy(); });
    return { action: 'deny' };
  });
}

module.exports = { installWindowNavigation };
