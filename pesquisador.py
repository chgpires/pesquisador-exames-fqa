"""Pesquisa verificável no texto dos exames nacionais FQA (715)."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import argparse
import json
import re
import threading
import unicodedata
import urllib.parse
import urllib.request

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
MAX_BYTES = 15 * 1024 * 1024
ALLOWED_HOSTS = {'iave.pt', 'www.iave.pt', 'aprendeaqui.pt', 'www.aprendeaqui.pt', 'eduqa.pt'}
LISTINGS = [
    ('IAVE', 'https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/'),
    ('Aprende Aqui — cópia do exame IAVE', 'https://aprendeaqui.pt/fisica-e-quimica-a/'),
]
# Fonte adicional verificada; os restantes exames são descobertos nos índices acima.
SEEDS = [{'url': 'https://eduqa.pt/wp-content/uploads/2026/06/fisica_e_quimica_prova_715_enunciado.pdf',
          'source': 'EduQA — cópia do exame IAVE',
          'criteria': 'https://eduqa.pt/wp-content/uploads/2026/06/fisica_e_quimica_prova_715_cc.pdf'}]
TOPICS = {
    'equilibrio quimico': ['equilibrio quimico', 'estado de equilibrio', 'constante de equilibrio', 'le chatelier', 'quociente da reacao'],
    'acido base': ['acido base', 'acido-base', 'titulacao', 'acido fraco', 'base forte', 'acido forte', 'constante de acidez'],
    'oxidacao reducao': ['oxidacao', 'reducao', 'oxidante', 'redutor', 'numero de oxidacao'],
    'solubilidade': ['solubilidade', 'produto de solubilidade', 'precipitacao', 'solucao saturada'],
    'energia e movimentos': ['energia cinetica', 'energia potencial', 'energia mecanica', 'trabalho da forca', 'forca de atrito'],
    'leis de newton': ['lei de newton', 'leis de newton', 'resultante das forcas', 'forca resultante'],
    'movimento circular': ['movimento circular', 'aceleracao centripeta', 'velocidade angular'],
    'ondas': ['comprimento de onda', 'frequencia', 'onda sonora', 'ondas', 'osciloscopio'],
    'refracao': ['refracao', 'indice de refracao', 'angulo limite', 'reflexao total'],
    'eletricidade': ['corrente eletrica', 'resistencia eletrica', 'tensao eletrica', 'lei de ohm', 'circuito eletrico'],
    'energia termica': ['capacidade termica', 'energia interna', 'transferencia de energia', 'calor especifico'],
    'tabela periodica': ['energia de ionizacao', 'raio atomico', 'configuracao eletronica', 'eletronegatividade'],
    'ligacao quimica': ['ligacao covalente', 'ligacao quimica', 'geometria molecular', 'lewis', 'polaridade'],
}
STOP = set('a o as os de da do das dos em no na nos nas e ou um uma que onde qual quais exame exames nacional nacionais aparece aparecem sobre quero queria estudar topico materia estudo procura procurar mostra me por para com'.split())

def normalize(text):
    return re.sub(r'\s+', ' ', ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')).strip()

def checked_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Endereço fora das fontes de exames autorizadas.')
    return url

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def download(url):
    checked_url(url)
    request = urllib.request.Request(url, headers={'User-Agent': 'PesquisadorFQA/1.0 (consulta educativa de exames publicos)'})
    with urllib.request.build_opener(SafeRedirect()).open(request, timeout=12) as response:
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError('Documento demasiado grande.')
    return content

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.context, self.current = [], '', None
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = {'url': dict(attrs).get('href', ''), 'label': '', 'context': self.context[-800:]}
    def handle_data(self, text):
        self.context += ' ' + text
        if self.current is not None:
            self.current['label'] += text
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

def discover(html, base, source):
    parser = Links()
    parser.feed(html)
    found = []
    for link in parser.links:
        url = urllib.parse.urljoin(base, unescape(link['url']))
        name = normalize(urllib.parse.unquote(url))
        label = normalize(link['label'])
        context = normalize(link['context'])
        if '.pdf' not in name or ('715' not in name and not ('exames nacionais fq' in context and 'enunciado' in label)):
            continue
        if re.search(r'[-_]cc[-_.]|criter', name) or 'criter' in label or 'adapt' in name:
            continue
        if 'iave' not in base and 'enunciado' not in label:
            continue
        try:
            checked_url(url)
        except ValueError:
            continue
        # Emparelha apenas links adjacentes do mesmo bloco (enunciado → critérios).
        position = parser.links.index(link)
        criteria = None
        if position + 1 < len(parser.links):
            next_link = parser.links[position + 1]
            if 'criter' in normalize(next_link['label']):
                candidate = urllib.parse.urljoin(base, unescape(next_link['url']))
                try:
                    criteria = checked_url(candidate)
                except ValueError:
                    pass
        found.append({'url': url, 'source': source, 'criteria': criteria})
    return found

def extract_exam(content, candidate):
    if not content.startswith(b'%PDF'):
        raise ValueError('A fonte não devolveu um PDF.')
    reader = PdfReader(BytesIO(content))
    if not 4 <= len(reader.pages) <= 60:
        raise ValueError('Número de páginas inesperado para um exame.')
    pages = [page.extract_text() or '' for page in reader.pages]
    first = normalize(pages[0])
    if not re.search(r'prova\s*715\b', first) or 'exame final nacional' not in first or 'fisica e quimica' not in first:
        raise ValueError('O PDF não foi confirmado como exame nacional de FQA, prova 715.')
    if 'criterios de classificacao' in first:
        raise ValueError('O documento é de critérios; não é um enunciado.')
    header = re.search(r'prova\s*715[^\n]*', pages[0], re.I)
    years = re.findall(r'\b20\d{2}\b', header.group() if header else '')
    if not years:
        years = re.findall(r'\b20\d{2}\b', pages[0][:800])
    if not years:
        raise ValueError('Não foi possível confirmar o ano do exame.')
    phase = 'Época especial' if 'epoca especial' in first else '2.ª fase' if re.search(r'2\s*\.?\s*ª?\s*fase', first) else '1.ª fase' if re.search(r'1\s*\.?\s*ª?\s*fase', first) else None
    if not phase:
        raise ValueError('Não foi possível confirmar a fase.')
    usable = []
    for number, text in enumerate(pages, 1):
        cleaned = re.sub(r'Prova\s*715[^\n]*|Página\s+\d+[^\n]*', '', text, flags=re.I)
        if number <= 3 or len(cleaned.strip()) < 100:
            continue  # Exclui capa, formulário e tabela periódica dos exames recentes.
        usable.append({'page': number, 'text': cleaned})
    if not usable:
        raise ValueError('Não foi possível extrair texto pesquisável (pode ser necessário OCR).')
    return {**candidate, 'year': int(years[0]), 'phase': phase, 'pages': usable,
            'id': sha256(content).hexdigest(), 'indexedAt': datetime.now(timezone.utc).isoformat()}

def query_terms(query):
    normalized = normalize(query).replace('-', ' ')
    terms = [t for t in re.findall(r'[a-z0-9]+', normalized) if t not in STOP and len(t) >= 2]
    cleaned = ' '.join(terms)
    synonyms = []
    for title, related in TOPICS.items():
        if title in normalized or (cleaned and set(title.split()) <= set(terms)):
            synonyms.extend(related)
    return terms, list(dict.fromkeys(synonyms))

def search_exams(exams, query, minimum=2000, maximum=2100):
    tokens, synonyms = query_terms(query)
    if not tokens:
        return []
    matches = []
    for exam in exams:
        if not minimum <= exam['year'] <= maximum:
            continue
        per_exam = []
        for page in exam['pages']:
            text = re.sub(r'\s+', ' ', page['text']).strip()
            norm = normalize(text)
            occurrences = []
            if synonyms:
                for phrase in synonyms:
                    match = re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', norm)
                    if match:
                        occurrences.append((match.start(), len(phrase), phrase))
            else:
                # Todas as palavras úteis têm de ocorrer na mesma página.
                for token in tokens:
                    match = re.search(r'(?<!\w)' + re.escape(token) + r'(?:s|es)?(?!\w)', norm)
                    if match:
                        occurrences.append((match.start(), len(token), token))
                if len(occurrences) != len(tokens):
                    continue
            if not occurrences:
                continue
            position, _, term = min(occurrences)
            excerpt = ('…' if position > 90 else '') + text[max(0,position-90):position+230] + ('…' if position+230 < len(text) else '')
            raw_normalized = ''.join(c for c in unicodedata.normalize('NFD',page['text'].lower()) if unicodedata.category(c) != 'Mn')
            raw_match = re.search(r'\s+'.join(re.escape(part) for part in term.split()),raw_normalized)
            before = page['text'][:raw_match.start()] if raw_match else ''
            questions = re.findall(r'(?:^|\n)\s*(\d{1,2}(?:\.\d{1,2}){0,2})\.(?=\s)', before)
            per_exam.append({'page':page['page'], 'excerpt':excerpt, 'term':term,
                             'questionHint': questions[-1] if questions else None, 'score':len(occurrences)})
        if per_exam:
            per_exam.sort(key=lambda p:(-p['score'],p['page']))
            matches.append({k:exam.get(k) for k in ('year','phase','url','source','criteria')} |
                           {'pages':per_exam[:3], 'score':per_exam[0]['score']})
    return sorted(matches,key=lambda m:(-m['score'],-m['year'],m['phase']))[:20]

class Library:
    def __init__(self, data_dir=DATA):
        self.data_dir = data_dir
        self.exams, self.warnings, self.updated = [], [], None
        self.busy = False
        self.progress = ''
        self.lock = threading.Lock()
        try:
            saved = json.loads((data_dir / 'index.json').read_text(encoding='utf-8'))
            self.exams, self.updated = saved['exams'], saved['updated']
            self.warnings = saved.get('warnings', [])
        except (OSError, ValueError, KeyError):
            pass
    def status(self):
        return {'busy':self.busy,'progress':self.progress,'count':len(self.exams),
                'pages':sum(len(x['pages']) for x in self.exams),'updated':self.updated,
                'warnings':self.warnings,'years':sorted({x['year'] for x in self.exams})}
    def start_refresh(self):
        with self.lock:
            if self.busy:
                return False
            self.busy = True
        threading.Thread(target=self.refresh,daemon=True).start()
        return True
    def refresh(self):
        warnings, candidates = [], list(SEEDS)
        indexed = {e['id']:e for e in self.exams}
        try:
            for source, url in LISTINGS:
                self.progress = 'A consultar ' + source.split(' — ')[0]
                try:
                    candidates += discover(download(url).decode('utf-8',errors='replace'),url,source)
                except Exception as error:
                    warnings.append(f'{source}: não foi possível consultar o índice ({type(error).__name__}).')
            candidates = list({c['url']:c for c in candidates}.values())[:50]
            def index_one(candidate):
                cached = next((e for e in self.exams if e['url'] == candidate['url']), None)
                if cached:
                    return cached
                return extract_exam(download(candidate['url']),candidate)
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(index_one,c):c for c in candidates}
                for i, future in enumerate(as_completed(futures),1):
                    self.progress = f'A analisar documentos: {i}/{len(candidates)}'
                    try:
                        exam = future.result()
                        # Evita listar versões/cópias do mesmo exame como exames diferentes.
                        existing = next((x for x in indexed.values() if (x['year'],x['phase']) == (exam['year'],exam['phase'])),None)
                        if existing is None or urllib.parse.urlsplit(exam['url']).hostname == 'iave.pt':
                            if existing:
                                indexed.pop(existing['id'],None)
                            indexed[exam['id']] = exam
                    except Exception as error:
                        warnings.append(f"Documento indisponível ou não confirmado: {futures[future]['url']} ({type(error).__name__}).")
            self.exams = sorted(indexed.values(),key=lambda e:(-e['year'],e['phase']))
            self.updated = datetime.now(timezone.utc).isoformat()
            self.warnings = warnings
            self.data_dir.mkdir(parents=True,exist_ok=True)
            temporary = self.data_dir / 'index.tmp'
            temporary.write_text(json.dumps({'exams':self.exams,'updated':self.updated,'warnings':warnings},ensure_ascii=False),encoding='utf-8')
            temporary.replace(self.data_dir / 'index.json')
        except Exception as error:
            self.warnings = warnings + [f'Não foi possível concluir a atualização: {type(error).__name__}.']
        finally:
            self.busy = False
            self.progress = ''

def serve(port):
    library = Library()
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, data, code=200):
            body = json.dumps(data,ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            path = urllib.parse.urlsplit(self.path).path
            if path == '/api/status':
                return self.send_json(library.status())
            if path not in ('/','/app.js','/style.css'):
                return self.send_json({'error':'Página não encontrada.'},404)
            name = 'index.html' if path == '/' else path[1:]
            body = (ROOT / 'public' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type',{'index.html':'text/html','app.js':'text/javascript','style.css':'text/css'}[name]+'; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            if self.headers.get('Origin') not in (None,f'http://localhost:{port}',f'http://127.0.0.1:{port}'):
                return self.send_json({'error':'Origem não autorizada.'},403)
            if not self.headers.get('Content-Type','').startswith('application/json'):
                return self.send_json({'error':'Pedido JSON necessário.'},415)
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 4000:
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
                if self.path == '/api/refresh':
                    library.start_refresh()
                    return self.send_json(library.status(),202)
                if self.path != '/api/search':
                    return self.send_json({'error':'Operação não encontrada.'},404)
                query = body.get('query','')
                if not isinstance(query,str) or not 2 <= len(query.strip()) <= 300:
                    return self.send_json({'error':'Escreva um tópico entre 2 e 300 caracteres.'},400)
                minimum, maximum = int(body.get('minimum',2000)), int(body.get('maximum',2100))
                if minimum > maximum:
                    raise ValueError()
                return self.send_json({'results':search_exams(library.exams,query,minimum,maximum),'status':library.status()})
            except (ValueError,TypeError,AttributeError):
                return self.send_json({'error':'Verifique o tópico e o intervalo de anos.'},400)
    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Abra http://localhost:{port}',flush=True)
    if not library.exams:
        library.start_refresh()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8787)
    parser.add_argument('--refresh',action='store_true')
    args = parser.parse_args()
    if args.refresh:
        lib = Library(); lib.busy = True; lib.refresh()
        print(json.dumps(lib.status(),ensure_ascii=False,indent=2))
    else:
        serve(args.port)
