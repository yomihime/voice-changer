// AST-based navigation and verbatim app declarations, not decompiled TypeScript.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.resolve(root,'../../client/demo/package.json'));
const ts = require('typescript');
const input = path.join(root,'readable/main-ui.js');
const text = fs.readFileSync(input,'utf8');
const sf = ts.createSourceFile(input,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS);
if (sf.parseDiagnostics.length) throw new Error('Recovered JavaScript has parse errors');
const names = new Set(['FileUploaderClient','RestClient','VCRestClient','VoiceChangerClient',
  'HeaderArea','InputControls','VolumeControls','VoiceControls','Controls','PerformanceArea',
  'ControlArea','AdvancedSettingDialog','ShortcutSettingDialog','AdvancedArea','Demo','App',
  'useAppGuiSetting','useGlobalSetting','useAudioConfig','useServerConfig','DefaultServerConfiguration',
  'AppRootProvider','useVoiceChangerClient','AppStateProvider','useHotKeySetting','HotkeyProvider',
  'LinkArea','ModelSelector','ModelList','ModelUploadDialog','ModelEditDialog','SampleModelDailog',
  'IconArea','InfoArea','PortraitArea','VoiceCharacterEditDialog','SettingsDialog','MainControls']);
const index = [];
function save(node,name,isVariable) {
  if (!names.has(name)) return;
  const start = sf.getLineAndCharacterOfPosition(node.getStart()).line+1;
  const end = sf.getLineAndCharacterOfPosition(node.end).line+1;
  const output = `readable/modules/${name}.js`;
  const header = `// Extracted declaration from ../main-ui.js:${start}-${end}.\n// Navigation/reference excerpt; shared bundle dependencies are NOT imported.\n// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.\n`;
  fs.writeFileSync(path.join(root,output),header+(isVariable?'const ':'')+node.getText(sf)+(isVariable?';':'')+'\n');
  index.push({name,start,end,output});
}
fs.mkdirSync(path.join(root,'readable/modules'),{recursive:true});
for (const st of sf.statements) {
  if (ts.isVariableStatement(st)) for (const d of st.declarationList.declarations) save(d,d.name.getText(sf),true);
  else if (st.name) save(st,st.name.getText(sf),false);
}
const lines = text.split('\n');
const endpoints = [];
function walk(node) {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) || ts.isTemplateExpression(node)) {
    const value = node.getText(sf).slice(1,-1);
    if (value.startsWith('/api/')) endpoints.push({path:value,line:sf.getLineAndCharacterOfPosition(node.getStart()).line+1});
  }
  ts.forEachChild(node,walk);
}
walk(sf);
const nativeCalls = [...text.matchAll(/\b(?:invoke|listen)\(\s*"([^"]+)"/g)].map(m=>({name:m[1],line:text.slice(0,m.index).split('\n').length}));
fs.writeFileSync(path.join(root,'evidence/code-index.json'),JSON.stringify({declarations:index,endpoints,nativeCalls},null,2)+'\n');
fs.writeFileSync(path.join(root,'readable/CODE_INDEX.md'),[
  '# 主界面代码导航', '',
  '以下名称由发布包保留下来。行号对应 `main-ui.js`；modules 只是便于阅读的声明摘录，不能单独运行。', '',
  '| 名称 | 完整文件行号 | 声明摘录 |','| --- | --- | --- |',
  ...index.map(x=>`| ${x.name} | ${x.start}–${x.end} | [查看](modules/${x.name}.js) |`), '',
  '## 原生调用', '', ...nativeCalls.map(x=>`- \`${x.name}\`：${x.line}`), '',
  '## HTTP 接口', '', ...endpoints.map(x=>`- \`${x.path}\`：${x.line}`), '',
].join('\n'));
console.log(`Indexed ${index.length} declarations, ${endpoints.length} API references, ${nativeCalls.length} native calls; ${lines.length} lines.`);
