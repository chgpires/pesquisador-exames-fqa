'use strict';
const $ = id => document.getElementById(id);
let searchBusy = false, library = null, libraryPromise = null;
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function libraryStatus() {
  return {busy:false,count:library.exams.length,pages:library.exams.reduce((n,e)=>n+e.pages.length,0),
    years:[...new Set(library.exams.map(e=>e.year))].sort(),updated:library.updated,warnings:library.warnings||[]};
}
async function loadLibrary(force=false) {
  if (libraryPromise&&!force) return libraryPromise;
  $('refresh').disabled=true;
  libraryPromise=(async()=>{
    const response=await fetch('library.json',{cache:'no-store'});
    if (!response.ok) throw new Error('Não foi possível carregar a biblioteca de exames. Tente recarregá-la.');
    const next=await response.json();
    if (next.schema!==1||!Array.isArray(next.exams)||!next.topics) throw new Error('O índice de exames tem um formato incompatível.');
    library=next;
    showStatus(libraryStatus());
    return library;
  })();
  try{return await libraryPromise;}
  catch(error){libraryPromise=null;throw error;}
  finally{$('refresh').disabled=false;}
}
function showStatus(status) {
  $('libraryCount').textContent = `${status.count} exames analisados`;
  $('libraryDetail').textContent = status.busy ? status.progress || 'A atualizar…' : `${status.pages} páginas · ${status.years.join(', ') || 'Sem documentos ainda'}`;
  $('refresh').disabled = status.busy;
  $('refresh').textContent = '↻ Recarregar biblioteca';
  const details = $('sourceDetails'); details.replaceChildren();
  details.append(element('p','Fontes: IAVE, Aprende Aqui e EduQA. As cópias são identificadas nos resultados. Só entram PDF confirmados como prova 715.'));
  details.append(element('p','A pesquisa corre neste browser, num índice preparado previamente. Recarregar obtém a última biblioteca publicada; não procura novos PDF.'));
  if (status.updated) details.append(element('p','Índice preparado em: '+new Date(status.updated).toLocaleString('pt-PT')));
  if (status.warnings.length) {
    details.append(element('p',`${status.warnings.length} avisos de acesso ou leitura. A cobertura é parcial.`));
    const list = element('ul');
    for (const warning of status.warnings) list.append(element('li',warning));
    details.append(list);
  }
}
function link(text, url) {
  const node = element('a',text); node.href = url; node.target = '_blank'; node.rel = 'noopener noreferrer'; return node;
}
function displayAnswer(container, data) {
  container.replaceChildren();
  const head = element('div',undefined,'answer-head');head.append(element('span','FQ','avatar'),element('span','Encontra no exame'));container.append(head);
  const {results,status} = data;
  if (!status.count) {
    container.append(element('p','A biblioteca publicada ainda não contém exames. Consulte «Fontes e disponibilidade».','message'));
    return;
  }
  if (!results.length) container.append(element('p','Não encontrei correspondências no texto dos exames analisados para este intervalo de anos. Experimente uma expressão mais específica ou um intervalo mais amplo. Isto não significa que o tópico nunca tenha saído em exame.','empty-results'));
  else {
    container.append(element('p',`Encontrei passagens em ${results.length} exame${results.length===1?'':'s'}. Abra o enunciado para confirmar o contexto.`, 'answer-intro'));
    for (const result of results) {
      const card = element('article',undefined,'card'), top = element('div',undefined,'card-top');
      top.append(element('h3',`${result.year} · ${result.phase}`),element('span',result.source,'source'));card.append(top);
      for (const page of result.pages) {
        card.append(element('div',`Página ${page.page} do PDF${page.questionHint ? ` · Questão próxima: ${page.questionHint} (confirmar)` : ''}`,'page'));
        card.append(element('p',`Expressão encontrada: ${page.term}`,'answer-note'));
        card.append(element('blockquote',page.excerpt,'excerpt'));
      }
      const links = element('div',undefined,'links');links.append(link('Abrir enunciado ↗',`${result.url}#page=${result.pages[0].page}`));
      if (result.criteria) links.append(link('Critérios de classificação ↗',result.criteria));
      card.append(links);container.append(card);
    }
  }
  container.append(element('p',`Pesquisa em ${status.count} exames analisados. As correspondências são textuais ou por expressões relacionadas; não constituem uma classificação completa por tópico.`, 'answer-note'));
  if (status.warnings.length || status.busy) container.append(element('p','Há documentos por consultar ou indisponíveis. Veja «Fontes e disponibilidade».','answer-note'));
}
async function search(query) {
  if (searchBusy) return;
  const minimum = Number($('minimum').value), maximum = Number($('maximum').value);
  if (minimum > maximum) {$('minimum').setCustomValidity('O ano inicial deve ser anterior ou igual ao final.');$('minimum').reportValidity();return;}
  searchBusy = true; $('send').disabled = true;
  const conversation = $('conversation');conversation.append(element('div',query,'user'));
  $('intro').hidden = true;
  const answer = element('div','A procurar nos enunciados…','assistant processing');conversation.append(answer);
  $('topic').value = '';
  answer.scrollIntoView({block:'nearest',behavior:'smooth'});
  try {await loadLibrary();const data={results:FQSearch.search(library.exams,query,library.topics,minimum,maximum),status:libraryStatus()};answer.classList.remove('processing');displayAnswer(answer,data);showStatus(data.status);}
  catch(error){answer.className = 'assistant message';answer.textContent = error.message;}
  finally{searchBusy=false;$('send').disabled=false;$('topic').focus({preventScroll:true});answer.scrollIntoView({block:'start',behavior:'smooth'});}
}
$('minimum').addEventListener('input',()=> $('minimum').setCustomValidity(''));
$('searchForm').addEventListener('submit',event=>{event.preventDefault();search($('topic').value.trim());});
for (const button of document.querySelectorAll('.examples button')) button.addEventListener('click',()=>search(button.textContent));
$('refresh').addEventListener('click',async()=>{try{await loadLibrary(true);}catch(error){$('libraryDetail').textContent=error.message;}});
loadLibrary().catch(error=>{$('libraryCount').textContent='Biblioteca indisponível';$('libraryDetail').textContent=error.message;});
