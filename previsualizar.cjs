const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const port = Number(process.env.PORT || 8787);
const files = new Set(['index.html','app.js','search.js','style.css','library.json']);
const types = {html:'text/html',js:'text/javascript',css:'text/css',json:'application/json'};
http.createServer((req,res)=>{
  const url = new URL(req.url,'http://localhost');
  if (url.pathname==='/'||url.pathname==='/public') {res.writeHead(302,{Location:'/public/'});res.end();return;}
  const name = url.pathname==='/public/'?'index.html':url.pathname.startsWith('/public/')?url.pathname.slice(8):'';
  if (!files.has(name)) {res.writeHead(404);res.end('Não encontrado');return;}
  fs.readFile(path.join(__dirname,'public',name),(error,body)=>{
    if (error) {res.writeHead(404);res.end('Ficheiro indisponível');return;}
    res.writeHead(200,{'Content-Type':`${types[name.split('.').pop()]}; charset=utf-8`,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(body);
  });
}).listen(port,'127.0.0.1',()=>console.log(`Abra http://localhost:${port}`));
