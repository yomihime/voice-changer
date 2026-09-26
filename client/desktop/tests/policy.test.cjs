'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { serverUrl, sameOrigin, externalUrl, parseArgs, profileDirectory, audioRequestAllowed } = require('../policy.cjs');

test('only the exact loopback HTTP entry is accepted', () => {
  assert.equal(serverUrl('http://127.0.0.1:18888/'), 'http://127.0.0.1:18888/');
  for (const value of ['file:///a', 'https://example.com/', 'http://127.0.0.1.evil/',
    'http://localhost:18888/', 'http://user@127.0.0.1:18888/', 'http://127.0.0.1:18888/?url=evil',
    'http://127.0.0.1:18888/other']) assert.throws(() => serverUrl(value), undefined, value);
});
test('external URLs never grant a command or alternate host', () => {
  assert.equal(externalUrl('https://github.com/w-okada/voice-changer'), 'https://github.com/w-okada/voice-changer');
  for (const value of ['javascript:alert(1)', 'file:///C:/Windows/notepad.exe', 'ms-settings:test',
    'https://github.com.evil/', 'https://github.com@evil/', 'https://evil@github.com/',
    'https://github.com:8080/', 'http://github.com/']) assert.equal(externalUrl(value), null, value);
});
test('navigation keeps exact origin and rejects credentials', () => {
  const origin = 'http://127.0.0.1:18888';
  assert.equal(sameOrigin(`${origin}/info`, origin), true);
  assert.equal(sameOrigin('http://127.0.0.1:18889/', origin), false);
  assert.equal(sameOrigin('http://user@127.0.0.1:18888/', origin), false);
  assert.equal(sameOrigin('not a url', origin), false);
});
test('strict CLI rejects old Electron switches and duplicate options', () => {
  assert.equal(parseArgs(['--url', 'http://127.0.0.1:18888/', '--deny-media']).denyMedia, true);
  assert.equal(parseArgs([]).backend, 'http://127.0.0.1:18000/');
  assert.equal(parseArgs(['--backend', 'http://127.0.0.1:18001']).backend, 'http://127.0.0.1:18001/');
  for (const args of [['--url', 'http://127.0.0.1/', '--backend', 'http://127.0.0.1/'], ['-u', 'http://127.0.0.1/'], ['--url'],
    ['--url', 'http://127.0.0.1/', '--url', 'http://127.0.0.1/'],
    ['--url', 'http://127.0.0.1/', '--profile-root', 'relative']]) assert.throws(() => parseArgs(args));
});
test('profile persists for a scope, but ports and installations are isolated', () => {
  const root = path.resolve('profiles');
  const a = profileDirectory(root, path.resolve('copy A'), 'http://127.0.0.1:18888');
  assert.equal(a, profileDirectory(root, path.resolve('copy A'), 'http://127.0.0.1:18888'));
  assert.notEqual(a, profileDirectory(root, path.resolve('copy B'), 'http://127.0.0.1:18888'));
  assert.notEqual(a, profileDirectory(root, path.resolve('copy A'), 'http://127.0.0.1:18889'));
  assert.equal(path.dirname(a), root);
});
test('microphone permission excludes camera, unknown requests, and child frames', () => {
  const origin = 'http://127.0.0.1:18888';
  const request = { isMainFrame: true, requestingUrl: `${origin}/`, mediaTypes: ['audio'] };
  assert.equal(audioRequestAllowed('media', request, origin), true);
  for (const override of [{ isMainFrame: false }, { requestingUrl: 'https://evil/' },
    { mediaTypes: ['audio', 'video'] }, { mediaTypes: [] }, { mediaTypes: undefined }]) {
    assert.equal(audioRequestAllowed('media', { ...request, ...override }, origin), false);
  }
  assert.equal(audioRequestAllowed('notifications', request, origin), false);
});
