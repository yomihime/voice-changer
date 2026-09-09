'use strict';

const path = require('node:path');
const crypto = require('node:crypto');

function serverUrl(value) {
  const url = new URL(value);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' ||
      url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('URL は http://127.0.0.1:<port>/ を指定してください。');
  }
  return url.href;
}

function sameOrigin(value, origin) {
  try {
    const url = new URL(value);
    return url.origin === origin && !url.username && !url.password;
  } catch { return false; }
}

function externalUrl(value) {
  try {
    const url = new URL(value);
    // Only the existing UI's documentation, licence and support destinations.
    const hosts = ['github.com', 'w-okada.github.io', 'www.buymeacoffee.com', 'openvpi.github.io'];
    return url.protocol === 'https:' && !url.username && !url.password &&
      !url.port && hosts.includes(url.hostname) ? url.href : null;
  } catch { return null; }
}

function parseArgs(args) {
  const options = { denyMedia: false };
  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    if (key === '--deny-media') { options.denyMedia = true; continue; }
    if (key === '--wait') { options.wait = true; continue; }
    if (key === '--hidden') { options.hidden = true; continue; }
    if (!['--url', '--profile-root'].includes(key) || !args[i + 1] || args[i + 1].startsWith('--')) {
      throw new Error(`不明または値のない引数: ${key}`);
    }
    const name = key === '--url' ? 'url' : 'profileRoot';
    if (options[name]) throw new Error(`重複した引数: ${key}`);
    options[name] = args[++i];
  }
  if (!options.url) throw new Error('--url が必要です。');
  if (options.hidden && !options.denyMedia) throw new Error('--hidden は --deny-media と併用してください。');
  options.url = serverUrl(options.url);
  if (options.profileRoot && !path.isAbsolute(options.profileRoot)) {
    throw new Error('--profile-root は絶対パスを指定してください。');
  }
  return options;
}

function profileDirectory(root, installation, origin) {
  const canonical = path.resolve(installation).toLowerCase();
  const scope = crypto.createHash('sha256').update(`${canonical}\n${origin}`).digest('hex').slice(0, 24);
  return path.join(root, scope);
}

function audioRequestAllowed(permission, details, origin) {
  return permission === 'media' && details.isMainFrame === true &&
    sameOrigin(details.requestingUrl, origin) && Array.isArray(details.mediaTypes) &&
    details.mediaTypes.length > 0 && details.mediaTypes.every(type => type === 'audio');
}

module.exports = { serverUrl, sameOrigin, externalUrl, parseArgs, profileDirectory, audioRequestAllowed };
