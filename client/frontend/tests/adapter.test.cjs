'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
test('non-Tauri startup is safe and unsupported shortcuts do not report success', async () => {
  const { invokeDesktop, listenDesktop } = await import('../src/desktop-adapter.js');
  global.window = { open: () => {} };
  try {
    assert.deepEqual(await invokeDesktop('get_shortcut_settings'), { enabled: false, shortcuts: [] });
    assert.equal(typeof await listenDesktop('shortcut-action', () => {}), 'function');
    await assert.rejects(invokeDesktop('register_shortcuts'), /全局快捷键/);
    await assert.rejects(invokeDesktop('open_browser_url', { url: 'file:///C:/Windows' }), /HTTPS/);
    window.__TAURI_INTERNALS__ = { invoke: async (command, args) => ({ command, args }) };
    assert.deepEqual(await invokeDesktop('native-test', { value: 1 }), { command: 'native-test', args: { value: 1 } });
  } finally { delete global.window; }
});
