'use strict';
const path = require('node:path');
const { startFrontend } = require('./server.cjs');
const args = process.argv.slice(2);
const options = { port: 21416 };
for (let i = 0; i < args.length; i++) {
  if (!['--backend', '--port'].includes(args[i]) || !args[i + 1]) throw new Error('Use --backend URL --port PORT');
  const key = args[i].slice(2);
  options[key] = key === 'port' ? Number(args[++i]) : args[++i];
}
startFrontend({ ...options, directory: path.join(__dirname, 'dist') }).then(service => {
  console.log(`Frontend: ${service.url} (backend: ${options.backend || 'not configured'})`);
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => { service.close(); });
}).catch(error => { console.error(error.message); process.exitCode = 1; });
