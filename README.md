# Encontra no exame — Física e Química A (715)

Assistente de pesquisa que funciona inteiramente no browser, em **HTML, CSS e JavaScript**, sem servidor Python e sem chaves de API.

**[Abrir aplicação](https://chgpires.github.io/pesquisador-exames-fqa/)** · [Repositório](https://github.com/chgpires/pesquisador-exames-fqa)

Introduza um tópico para obter exames, páginas do PDF, pequenas passagens e ligações para os documentos consultados. O aluno não precisa de instalar nada.

## Como funciona

O browser carrega `public/library.json`, um índice de texto preparado previamente. A pesquisa é feita localmente por `public/search.js`, com palavras e expressões relacionadas. Os enunciados e critérios abrem nos sites de origem. Não há pedidos a `/api`, envio das perguntas para um modelo de IA ou dependência de um computador ligado.

O botão **Recarregar biblioteca** obtém a última versão do índice publicado. Não descarrega nem analisa novos PDF durante a conversa. A data da recolha, as fontes e os avisos de cobertura são visíveis na aplicação.

A biblioteca inicial inclui **12 exames, de 2022 a 2026**, com **142 páginas de exercícios**. O IAVE estava indisponível durante a recolha; os documentos usados foram obtidos nas cópias identificadas da Aprende Aqui e EduQA. Não se garante a cobertura de todas as fases ou anos.

## Abrir e editar no Visual Studio Code

1. Abra esta pasta no VS Code.
2. Execute `iniciar.cmd`, ou `node previsualizar.cjs` no terminal (precisa de Node.js apenas para esta pré-visualização).
3. Abra **http://localhost:8787**. Termine com Ctrl+C.

Pode também usar uma pré-visualização estática do VS Code, servindo a pasta do projeto. Abrir o HTML por duplo clique pode bloquear o carregamento de `library.json`; use a pré-visualização ou o endereço HTTPS publicado.

## Publicação no GitHub Pages

Em **Settings → Pages**, use **Deploy from a branch → main → / (root)**. O `index.html` da raiz encaminha para `public/`. Os caminhos dos recursos são relativos, para funcionar no endereço do projeto.

Para atualizar a interface, publique os ficheiros alterados em `public/`. Para atualizar os exames, siga a secção seguinte. O GitHub Pages volta a publicar quando a branch é atualizada.

## Atualizar o índice de exames (opcional, pelo professor)

Python é usado apenas como ferramenta de preparação dos documentos, fora da utilização da aplicação. Os alunos e o GitHub Pages não executam Python.

Com Python 3.10 ou superior, no terminal desta pasta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe exportar_indice.py --atualizar
```

Publique depois o ficheiro gerado **`public/library.json`** no repositório. Para exportar uma recolha local existente sem voltar à Internet, omita `--atualizar`. As fontes e o vocabulário podem ser ajustados em `pesquisador.py`. Não é necessário alterar a interface para acrescentar exames ao índice.

O preparador verifica na capa dos PDF a disciplina, o código 715, o ano e a fase. Se uma fonte falhar, conserva o que já tinha sido analisado e regista avisos. Deduplica por ano/fase e mantém uma versão de cada prova. Reutiliza documentos cujo endereço já tenha sido analisado. Para forçar a releitura de um PDF substituído no mesmo endereço, remova a cópia local `data/index.json` antes da recolha; o índice público só é substituído se houver exames analisados para exportar.

## Limitações da pesquisa

- Pesquisa textual e por expressões relacionadas de um pequeno vocabulário de FQA; não é uma classificação semântica exaustiva nem um modelo de linguagem. Cada mensagem é uma pesquisa independente.
- Não lê imagens, gráficos ou PDF digitalizados sem texto; não inclui OCR. Fórmulas extraídas podem aparecer deformadas. Confirme sempre no PDF.
- As primeiras três páginas dos exames recentes (capa, formulário e tabela periódica) são excluídas. Antes de incluir exames mais antigos com outra estrutura, esse critério deve ser revisto.
- As páginas indicadas são páginas do ficheiro PDF. A questão é uma referência próxima extraída do texto, quando possível; não substitui a confirmação no enunciado.
- Apresenta até 20 exames e três páginas por exame. Os critérios são ligações de apoio, sem análise do seu conteúdo nesta versão.
- Uma pesquisa sem resultados não prova que o tópico nunca saiu em exame.

## Testes

Motor que corre no browser: `node --test tests/search.test.cjs`.

Preparador de documentos: `python -m unittest discover -s tests -v` (com as dependências Python instaladas).

`pesquisador.py` conserva a implementação anterior de pesquisa/servidor local para desenvolvimento e comparação. A interface publicada usa exclusivamente JavaScript e o índice estático.

Fontes: [IAVE](https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/), [Aprende Aqui](https://aprendeaqui.pt/fisica-e-quimica-a/), [EduQA](https://eduqa.pt/). Preparação dos PDF: [pypdf](https://pypdf.readthedocs.io/).
