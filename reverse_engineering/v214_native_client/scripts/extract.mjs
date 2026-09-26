// Static PE/Tauri resource extraction. Does not execute the input program.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = path.resolve(process.argv[2] || 'E:/AI/voice-changer-native-client-win.exe');
const b = fs.readFileSync(input);
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
if (b.toString('ascii', 0, 2) !== 'MZ') throw new Error('Not a PE file');
const pe = b.readUInt32LE(60);
if (b.toString('ascii', pe, pe + 4) !== 'PE\0\0') throw new Error('Invalid PE signature');
const opt = pe + 24;
if (b.readUInt16LE(opt) !== 0x20b) throw new Error('Expected PE32+');
const imageBase = Number(b.readBigUInt64LE(opt + 24));
const sections = Array.from({length: b.readUInt16LE(pe + 6)}, (_, i) => {
  const o = opt + b.readUInt16LE(pe + 20) + i * 40;
  return {name:b.toString('ascii',o,o+8).replace(/\0/g,''),virtualSize:b.readUInt32LE(o+8),rva:b.readUInt32LE(o+12),size:b.readUInt32LE(o+16),offset:b.readUInt32LE(o+20)};
});
function offset(va, length = 1) {
  const rva = va - imageBase;
  const s = sections.find(s => rva >= s.rva && rva + length <= s.rva + s.size);
  return s ? s.offset + rva - s.rva : null;
}
const hex = n => '0x' + n.toString(16);
const assets = [];
// Rust PHF entries contain ((path_ptr,path_len),(data_ptr,data_len)).
for (const section of sections.filter(s => s.name === '.rdata')) {
  for (let o = section.offset; o + 32 <= section.offset + section.size; o += 8) {
    const values = [0,8,16,24].map(d => Number(b.readBigUInt64LE(o+d)));
    const [kp,kl,dp,dl] = values;
    if (kl < 2 || kl > 260 || dl < 1 || dl > b.length) continue;
    const ko = offset(kp,kl), dataOffset = offset(dp,dl);
    if (ko === null || dataOffset === null) continue;
    const key = b.toString('utf8',ko,ko+kl);
    if (!/^\/[a-zA-Z0-9_./@-]+\.(html|js|css|json|map|ico|png|svg|woff2?|wasm)$/.test(key)) continue;
    if (key.split('/').includes('..') || assets.some(a => a.path === key)) continue;
    const compressed = b.subarray(dataOffset,dataOffset+dl);
    let content;
    try { content = zlib.brotliDecompressSync(compressed,{maxOutputLength:64*1024*1024}); }
    catch { continue; }
    const relative = key.slice(1);
    const target = path.resolve(root,'extracted',relative);
    if (!target.startsWith(path.resolve(root,'extracted')+path.sep)) throw new Error('Unsafe asset path');
    fs.mkdirSync(path.dirname(target),{recursive:true}); fs.writeFileSync(target,content);
    assets.push({path:key,tableOffset:hex(o),keyOffset:hex(ko),dataOffset:hex(dataOffset),compressedBytes:dl,bytes:content.length,sha256:hash(content)});
  }
}
if (!assets.some(a => a.path === '/index.html')) throw new Error('No Tauri index.html recovered');
const strings = [];
// Include UTF-8 Japanese strings and paths; avoid emitting compressed data as text.
for (const s of sections.filter(s => s.name === '.rdata')) {
  const data = b.subarray(s.offset,s.offset+s.size);
  for (const match of data.toString('latin1').matchAll(/[\x20-\x7e\x80-\xff]{6,}/g)) {
    const raw = Buffer.from(match[0],'latin1');
    const text = raw.toString('utf8');
    if (!text.includes('\ufffd') && /(?:src[\\/]|https?:|shortcut|notification|vcclient|webview2|greet|config\.json|\.pdb)/i.test(text)) {
      strings.push({offset:hex(s.offset+match.index),text});
    }
  }
}
fs.mkdirSync(path.join(root,'evidence'),{recursive:true});
const report = {input,size:b.length,sha256:hash(b),machine:hex(b.readUInt16LE(pe+4)),imageBase:hex(imageBase),entryPoint:hex(imageBase+b.readUInt32LE(opt+16)),peTimestamp:new Date(b.readUInt32LE(pe+8)*1000).toISOString(),sections,assets};
fs.writeFileSync(path.join(root,'evidence','binary-report.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(root,'evidence','native-strings.json'),JSON.stringify(strings,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
