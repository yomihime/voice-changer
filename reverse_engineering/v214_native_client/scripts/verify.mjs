import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const load = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const native = load('evidence/binary-report.json');
const release = load('evidence/release-report.json');
let verified=0, syntaxChecks=0;
for(const [dir,entries] of [['extracted',native.assets],['web_front',release.files]]) {
  for(const entry of entries) {
    const file = path.join(root,dir,entry.path.replace(/^\//,''));
    const b=fs.readFileSync(file);
    if(b.length!==entry.bytes || hash(b)!==entry.sha256) throw new Error('Integrity mismatch: '+file);
    if(file.endsWith('.json')) JSON.parse(b.toString('utf8'));
    if(file.endsWith('.js')) {
      execFileSync(process.execPath,['--check','--input-type=module'],{input:b});syntaxChecks++;
    }
    verified++;
  }
}
for(const file of ['readable/main-ui.js','readable/native-client.js']) {
  execFileSync(process.execPath,['--check','--input-type=module'],{input:fs.readFileSync(path.join(root,file))});syntaxChecks++;
}
if(release.nativeSha256!==native.sha256 || release.version!=='2.1.4-alpha') throw new Error('Release mismatch');
for(const active of [release.activeJs,release.activeCss]) if(!fs.existsSync(path.join(root,'web_front',active))) throw new Error('Missing entry asset');
const main=fs.readFileSync(path.join(root,'web_front',release.activeJs),'utf8');
const localImports=[...main.matchAll(/(?:import\(|from\s*)["'](\.\.?\/[^"']+)["']/g)].map(m=>m[1]);
for(const ref of localImports) if(!fs.existsSync(path.resolve(root,'web_front',path.dirname(release.activeJs),ref))) throw new Error('Missing import: '+ref);
const result={verifiedFiles:verified,moduleSyntaxChecks:syntaxChecks,localImports,version:release.version,nativeExactMatch:true};
fs.writeFileSync(path.join(root,'evidence/verification.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
