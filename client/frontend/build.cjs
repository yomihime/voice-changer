'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

function build(destination = path.join(__dirname, 'dist')) {
  const target = path.resolve(destination);
  if (target !== path.join(__dirname, 'dist')) throw new Error('Build output must be frontend/dist');
  for (const name of fs.readdirSync(path.join(__dirname, 'src'))) {
    if (!name.endsWith('.js')) continue;
    const result = spawnSync(process.execPath, ['--check', path.join(__dirname, 'src', name)], { encoding: 'utf8' });
    if (result.status !== 0) throw new Error(result.stderr);
  }
  if (fs.existsSync(target) && fs.realpathSync(target) !== target) throw new Error('Refusing linked output directory');
  fs.rmSync(target, { recursive: true, force: true });
  fs.mkdirSync(target, { recursive: true });
  fs.cpSync(path.join(__dirname, 'public'), target, { recursive: true });
  fs.cpSync(path.join(__dirname, 'src'), path.join(target, 'src'), { recursive: true });
  for (const name of ['index.html', 'NOTICE.md']) fs.copyFileSync(path.join(__dirname, name), path.join(target, name));
  console.log(`Frontend built: ${target}`);
  return target;
}
if (require.main === module) build();
module.exports = { build };
