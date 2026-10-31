(function(root) {
  'use strict';
  const STOP = new Set('a o as os de da do das dos em no na nos nas e ou um uma que onde qual quais exame exames nacional nacionais aparece aparecem sobre quero queria estudar topico materia estudo procura procurar mostra me por para com'.split(' '));
  function unaccent(text) {return String(text).toLowerCase().normalize('NFD').replace(/\p{M}/gu,'');}
  function normalize(text) {return unaccent(text).replace(/\s+/g,' ').trim();}
  function escapeRegex(text) {return text.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
  function occurrence(text, phrase, plural=false) {
    const match = new RegExp('(^|[^a-z0-9_])('+escapeRegex(phrase)+(plural?'(?:s|es)?':'')+')(?=$|[^a-z0-9_])').exec(text);
    return match ? {position:match.index+match[1].length,term:phrase} : null;
  }
  function queryTerms(query, topics={}) {
    const normalized=normalize(query).replace(/-/g,' ');
    const tokens=(normalized.match(/[a-z0-9]+/g)||[]).filter(t=>t.length>=2&&!STOP.has(t));
    const synonyms=[];
    for (const [title,related] of Object.entries(topics)) {
      if (normalized.includes(title)||title.split(' ').every(t=>tokens.includes(t))) synonyms.push(...related);
    }
    return {tokens,synonyms:[...new Set(synonyms)]};
  }
  function search(exams,query,topics={},minimum=2000,maximum=2100) {
    const {tokens,synonyms}=queryTerms(query,topics);
    if (!tokens.length) return [];
    const results=[];
    for (const exam of exams) {
      if (exam.year<minimum||exam.year>maximum) continue;
      const pages=[];
      for (const page of exam.pages) {
        const text=page.text.replace(/\s+/g,' ').trim(), norm=normalize(text);
        const terms=synonyms.length?synonyms:tokens;
        const occurrences=terms.map(t=>occurrence(norm,t,!synonyms.length)).filter(Boolean);
        if (!occurrences.length||(!synonyms.length&&occurrences.length!==tokens.length)) continue;
        occurrences.sort((a,b)=>a.position-b.position);
        const {position,term}=occurrences[0];
        const excerpt=(position>90?'…':'')+text.slice(Math.max(0,position-90),position+230)+(position+230<text.length?'…':'');
        const raw=unaccent(page.text), rawMatch=new RegExp(term.split(' ').map(escapeRegex).join('\\s+')).exec(raw);
        const before=rawMatch?raw.slice(0,rawMatch.index):'';
        const hints=[...before.matchAll(/(?:^|\n)\s*(\d{1,2}(?:\.\d{1,2}){0,2})\.(?=\s)/g)];
        pages.push({page:page.page,excerpt,term,questionHint:hints.length?hints[hints.length-1][1]:null,score:occurrences.length});
      }
      if (pages.length) {
        pages.sort((a,b)=>b.score-a.score||a.page-b.page);
        results.push({year:exam.year,phase:exam.phase,url:exam.url,source:exam.source,criteria:exam.criteria,pages:pages.slice(0,3),score:pages[0].score});
      }
    }
    return results.sort((a,b)=>b.score-a.score||b.year-a.year||a.phase.localeCompare(b.phase,'pt')).slice(0,20);
  }
  const api={normalize,queryTerms,search};
  if (typeof module!=='undefined'&&module.exports) module.exports=api;
  else root.FQSearch=api;
})(typeof globalThis!=='undefined'?globalThis:this);
