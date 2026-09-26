// Readability pass only: identifiers and runtime behavior remain as shipped.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.resolve(root, '../../client/demo/package.json'));
const prettier = require('prettier');
const report = JSON.parse(fs.readFileSync(path.join(root,'evidence/release-report.json'),'utf8'));
fs.mkdirSync(path.join(root,'readable'),{recursive:true});
for (const [input,output] of [
  ['extracted/assets/index-DXT-JtqG.js','readable/native-client.js'],
  ['web_front/'+report.activeJs,'readable/main-ui.js'],
  ['web_front/'+report.activeCss,'readable/main-ui.css'],
]) {
  const source = fs.readFileSync(path.join(root,input),'utf8');
  const formatted = await prettier.format(source,{parser:input.endsWith('.css')?'css':'babel'});
  fs.writeFileSync(path.join(root,output),formatted);
  console.log(output);
}
