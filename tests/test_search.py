import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pesquisador import normalize, search_exams, discover, checked_url, Library, extract_exam

class SearchTests(unittest.TestCase):
    def exam(self,text,year=2024):
        return {'id':'test','year':year,'phase':'1.ª fase','url':'https://iave.pt/exame.pdf',
                'source':'IAVE','criteria':None,'pages':[{'page':6,'text':text}]}
    def test_accent_and_case(self):
        self.assertEqual(normalize('  EQUILÍBRIO   químico '),'equilibrio quimico')
    def test_topic_uses_specific_related_expressions(self):
        result=search_exams([self.exam('A constante de equilíbrio da reação aumenta.')],'equilíbrio químico')
        self.assertEqual(result[0]['pages'][0]['page'],6)
        self.assertIn('constante',result[0]['pages'][0]['excerpt'])
        self.assertEqual(search_exams([self.exam('Equilíbrio térmico entre dois corpos.')],'equilíbrio químico'),[])
    def test_custom_topic_requires_all_words(self):
        self.assertEqual(search_exams([self.exam('Uma substância.')],'ácido sulfúrico'),[])
        self.assertTrue(search_exams([self.exam('O ácido sulfúrico é utilizado.')],'ácido sulfúrico'))
    def test_year_filter_and_no_fabricated_question(self):
        exam=self.exam('Solubilidade do sal.')
        self.assertEqual(search_exams([exam],'solubilidade',2025,2026),[])
        self.assertIsNone(search_exams([exam],'solubilidade')[0]['pages'][0]['questionHint'])
    def test_no_cross_page_false_match(self):
        exam=self.exam('Um ácido.')
        exam['pages'].append({'page':7,'text':'O sulfúrico.'})
        self.assertEqual(search_exams([exam],'ácido sulfúrico'),[])
    def test_question_hint_with_accents(self):
        result=search_exams([self.exam('5.2. Calcule o valor.\nA constante de equilíbrio depende da temperatura.')],'equilíbrio químico')
        self.assertEqual(result[0]['pages'][0]['questionHint'],'5.2')
        result=search_exams([self.exam('4.2. Outra questão.\n5. Considere o equilíbrio químico.')],'equilíbrio químico')
        self.assertEqual(result[0]['pages'][0]['questionHint'],'5')
    def test_discovery_skips_criteria_and_pairs_links(self):
        html='<h2>Exames Nacionais FQ A 715</h2><a href="/EX-FQA715-F1-2024-V1.pdf">1ª Fase enunciado</a><a href="/EX-FQA715-F1-2024-CC.pdf">1ª Fase critérios</a>'
        found=discover(html,'https://aprendeaqui.pt/','Cópia')
        self.assertEqual(len(found),1)
        self.assertTrue(found[0]['criteria'].endswith('-CC.pdf'))
    def test_download_allowlist(self):
        for url in ['http://iave.pt/a.pdf','https://iave.pt.evil.test/a.pdf','https://127.0.0.1/x','https://iave.pt:8443/x']:
            with self.assertRaises(ValueError): checked_url(url)
    def test_rejects_html_as_pdf(self):
        with self.assertRaises(ValueError): extract_exam(b'<html>blocked</html>',{})
    def test_failed_refresh_preserves_library_and_reports_partial_coverage(self):
        with TemporaryDirectory() as folder:
            lib=Library(Path(folder));lib.exams=[self.exam('Solubilidade do sal.')]
            with patch('pesquisador.download',side_effect=OSError('indisponível')):
                lib.refresh()
            self.assertEqual(len(lib.exams),1)
            self.assertGreater(len(lib.warnings),0)
            self.assertFalse(lib.busy)

if __name__=='__main__': unittest.main()
