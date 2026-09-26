// Assemble an editable copy without touching original application or extracted evidence.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const report = JSON.parse(fs.readFileSync(path.join(root,'evidence/release-report.json'),'utf8'));
const js = fs.readFileSync(path.join(root,'readable/main-ui.js'),'utf8');
execFileSync(process.execPath,['--check','--input-type=module'],{input:js});
const target = path.join(root,'dev_front');
fs.cpSync(path.join(root,'web_front'),target,{recursive:true});
fs.writeFileSync(path.join(target,report.activeJs),js);
fs.copyFileSync(path.join(root,'readable/main-ui.css'),path.join(target,report.activeCss));
const overrides = path.join(root,'editable/overrides.css');
fs.copyFileSync(overrides,path.join(target,'overrides.css'));
let html = fs.readFileSync(path.join(target,'index.html'),'utf8');
html = html.replace('</head>','<link rel="stylesheet" href="./overrides.css">\n</head>');
fs.writeFileSync(path.join(target,'index.html'),html);
console.log('Built '+target);
