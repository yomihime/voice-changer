'use strict';

const { app, dialog } = require('electron');
const { parseArgs } = require('./policy.cjs');
const { startDesktop } = require('./runtime.cjs');

if (process.env.VCCLIENT_DESKTOP_SELF_TEST === '1') {
  app.disableHardwareAcceleration();
  app.commandLine.appendSwitch('no-sandbox');
}

let options;
const args = process.argv.slice(app.isPackaged ? 1 : 2)
  .filter(value => process.env.VCCLIENT_DESKTOP_SELF_TEST !== '1' ||
    !['--no-sandbox', '--disable-gpu'].includes(value));
if (['--self-test', '--frontend-self-test'].includes(args[0])) {
  const path = require('node:path');
  if (args.length !== 2 || !path.isAbsolute(args[1])) app.exit(2);
  else require(args[0] === '--self-test' ? './self-test.cjs' : './frontend-self-test.cjs').run(args[1]).catch(error => {
    require('node:fs').writeFileSync(path.join(args[1], 'failure.txt'), error.stack);
    app.exit(1);
  });
} else {
try {
  options = parseArgs(args);
} catch (error) {
  dialog.showErrorBox('VCClient Desktop', error.message);
  app.exit(2);
}
if (options) {
  startDesktop(options).catch(error => {
    dialog.showErrorBox('VCClient Desktop', `Client を起動できませんでした。\n${error.message}`);
    app.exit(1);
  });
}
}
