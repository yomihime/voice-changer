// Keep platform integration outside the recovered React application.
export async function invokeDesktop(command, args = {}, options) {
  if (window.__TAURI_INTERNALS__) return window.__TAURI_INTERNALS__.invoke(command, args, options);
  switch (command) {
    case 'get_shortcut_settings':
      return { enabled: false, shortcuts: [] };
    case 'update_shortcut_settings':
    case 'register_shortcuts':
      throw new Error('当前 Electron / 浏览器版本尚未实现全局快捷键。');
    case 'open_browser_url': {
      const url = new URL(args.url);
      if (url.protocol !== 'https:') throw new Error('Only HTTPS links are supported');
      window.open(url.href, '_blank', 'noopener,noreferrer');
      return;
    }
    case 'set_clear_site_data_and_stop_app':
      localStorage.clear();
      sessionStorage.clear();
      for (const key of await caches.keys()) await caches.delete(key);
      // Browser storage only. The separately managed inference service keeps running.
      window.location.reload();
      return;
    default:
      throw new Error(`Unsupported desktop command: ${command}`);
  }
}

export async function listenDesktop(event, callback) {
  if (event !== 'shortcut-action') throw new Error(`Unsupported desktop event: ${event}`);
  // No native global shortcut provider is registered in this first Electron entry.
  return () => {};
}
