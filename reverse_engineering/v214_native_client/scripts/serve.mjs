// Local development server. Backend forwarding is opt-in; no fake API responses.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const option = (name,fallback) => {const i=args.indexOf(name);return i<0?fallback:args[i+1];};
const mode = option('--mode','dev');
if (!['dev','original','native'].includes(mode)) throw new Error('Mode must be dev, original, or native');
const directory = fs.realpathSync(path.join(root,{dev:'dev_front',original:'web_front',native:'extracted'}[mode]));
const port = Number(option('--port','21414'));
const backend = option('--backend',null) ? new URL(option('--backend')) : null;
if (backend && (backend.protocol !== 'http:' || !['localhost','127.0.0.1','[::1]'].includes(backend.hostname) || backend.username || backend.password || backend.pathname !== '/')) {
  throw new Error('Backend must be a local HTTP origin, e.g. http://127.0.0.1:18000');
}
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.ico':'image/x-icon','.png':'image/png','.wav':'audio/wav','.txt':'text/plain; charset=utf-8'};
function fail(res,status,message) {res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify({error:message}));}
function proxy(req,res) {
  if (!backend) return fail(res,503,'No backend configured. Use --backend with a running 2.1.4-alpha server.');
  const upstream = http.request({hostname:backend.hostname,port:backend.port || 80,path:req.url,method:req.method,headers:{...req.headers,host:backend.host}}, reply => {
    res.writeHead(reply.statusCode,reply.headers);reply.pipe(res);
  });
  upstream.on('error',e=>{if(!res.headersSent)fail(res,502,e.message);else res.destroy();});
  req.pipe(upstream);
}
const server = http.createServer((req,res) => {
  let pathname;
  try {pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);} catch {return fail(res,400,'Invalid path');}
  if (/^\/(api(?:\/|_)|socket\.io(?:\/|\?)|model_dir\/|upload_dir\/|tmp_dir\/)/.test(pathname) || pathname==='/vcclient.log') return proxy(req,res);
  const target = path.resolve(directory,'.'+(pathname==='/'?'/index.html':pathname));
  if (!target.startsWith(directory+path.sep)) return fail(res,403,'Outside document root');
  if (!['GET','HEAD'].includes(req.method)) return fail(res,405,'Static files are read-only');
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return fail(res,404,'File not found');
  if (!fs.realpathSync(target).startsWith(directory+path.sep)) return fail(res,403,'Outside document root');
  res.writeHead(200,{'Content-Type':mime[path.extname(target)] || 'application/octet-stream','Cache-Control':'no-store'});
  if(req.method==='HEAD')res.end();else fs.createReadStream(target).pipe(res);
});
server.on('upgrade',(req,socket,head)=>{
  if(!backend || !req.url.startsWith('/socket.io/')) return socket.destroy();
  const upstream = http.request({hostname:backend.hostname,port:backend.port||80,path:req.url,headers:{...req.headers,host:backend.host}});
  upstream.on('upgrade',(reply,peer,peerHead)=>{
    socket.write(`HTTP/1.1 ${reply.statusCode} ${reply.statusMessage}\r\n`+Object.entries(reply.headers).map(([k,v])=>`${k}: ${v}\r\n`).join('')+'\r\n');
    if(head.length)peer.write(head);if(peerHead.length)socket.write(peerHead);
    peer.on('error',()=>socket.destroy());socket.on('error',()=>peer.destroy());
    socket.pipe(peer).pipe(socket);
  });
  upstream.on('response',()=>socket.destroy());upstream.on('error',()=>socket.destroy());upstream.end();
});
server.listen(port,'127.0.0.1',()=>console.log(`Serving ${mode}: http://127.0.0.1:${port} (backend: ${backend || 'none'})`));
