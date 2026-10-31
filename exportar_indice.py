"""Prepara a biblioteca estática. Não é usado durante as pesquisas no browser."""
import argparse
import json
from pesquisador import Library, ROOT, TOPICS

def export_library(refresh=False):
    library=Library()
    if refresh:
        library.refresh()
    if not library.exams:
        raise SystemExit('Sem exames analisados. Execute python exportar_indice.py --atualizar com acesso à Internet.')
    payload={'schema':1,'updated':library.updated,'warnings':library.warnings,
             'topics':TOPICS,'exams':library.exams}
    target=ROOT / 'public' / 'library.json'
    target.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Biblioteca exportada: {len(library.exams)} exames, {target.stat().st_size} bytes.')
    return target

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--atualizar',action='store_true',help='Consulta fontes na Internet antes de exportar.')
    export_library(parser.parse_args().atualizar)
