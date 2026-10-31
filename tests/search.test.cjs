const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const engine=require('../public/search.js');
const library=JSON.parse(fs.readFileSync(path.join(__dirname,'../public/library.json'),'utf8'));
const exam=text=>({year:2024,phase:'1.ª fase',url:'https://iave.pt/exame.pdf',source:'IAVE',pages:[{page:6,text}]});
test('acentos e maiúsculas',()=>assert.equal(engine.normalize(' EQUILÍBRIO   químico '),'equilibrio quimico'));
test('expressões relacionadas sem confundir equilíbrio térmico',()=>{
  assert.equal(engine.search([exam('A constante de equilíbrio da reação aumenta.')],'equilíbrio químico',library.topics).length,1);
  assert.equal(engine.search([exam('Equilíbrio térmico entre dois corpos.')],'equilíbrio químico',library.topics).length,0);
});
test('consulta livre requer todas as palavras na mesma página',()=>{
  assert.equal(engine.search([exam('Um ácido.')],'ácido sulfúrico',{}).length,0);
  assert.equal(engine.search([exam('O ácido sulfúrico reage.')],'ácido sulfúrico',{}).length,1);
  const split=exam('Um ácido.');split.pages.push({page:7,text:'O sulfúrico.'});
  assert.equal(engine.search([split],'ácido sulfúrico',{}).length,0);
});
test('intervalo de anos',()=>assert.equal(engine.search([exam('Solubilidade.')],'solubilidade',library.topics,2025,2026).length,0));
test('referência da questão preserva acentos e reconhece mudança de grupo',()=>{
  const result=engine.search([exam('4.2. Outra questão.\n5. Considere o equilíbrio químico.')],'equilíbrio químico',library.topics);
  assert.equal(result[0].pages[0].questionHint,'5');
});
test('não inventa números de questão',()=>{
  assert.equal(engine.search([exam('Solubilidade do sal.')],'solubilidade',library.topics)[0].pages[0].questionHint,null);
});
test('pesquisa real no índice publicado',()=>{
  assert.equal(library.schema,1);assert.ok(library.exams.length>0);
  const results=engine.search(library.exams,'equilíbrio químico',library.topics,2022,2026);
  assert.ok(results.some(e=>e.year===2026&&e.pages.some(p=>p.page===6)));
  for (const result of results) {assert.match(result.url,/^https:\/\//);assert.ok(result.pages.every(p=>p.excerpt.length>0));}
});
test('recursos relativos e ausência de pedidos ao servidor de pesquisa',()=>{
  const html=fs.readFileSync(path.join(__dirname,'../public/index.html'),'utf8');
  const app=fs.readFileSync(path.join(__dirname,'../public/app.js'),'utf8');
  assert.doesNotMatch(html,/(?:src|href)="\//);
  assert.doesNotMatch(app,/\/api\//);
  assert.ok(html.includes('search.js'));
});
