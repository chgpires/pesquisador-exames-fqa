# Encontra no exame — Física e Química A (715)

Primeira versão local de um assistente de pesquisa em formato de conversa. Introduza um tópico e obtenha exames, páginas do PDF, pequenas passagens e ligações para os documentos consultados. É um projeto separado do reconhecedor de material de laboratório.

Repositório: <https://github.com/chgpires/pesquisador-exames-fqa>.

**Alojamento:** este repositório guarda o código. A aplicação usa um servidor Python e, por isso, não pode funcionar diretamente no GitHub Pages. Para já, execute-a no computador seguindo as instruções abaixo. Os PDF e o índice local de pesquisa não são incluídos no repositório; a biblioteca é construída na primeira execução.

## Abrir no Visual Studio Code

**Neste computador:** pode executar `iniciar.cmd` nesta pasta, ou escrever `.\iniciar.cmd` no terminal do VS Code. O iniciador procura primeiro o ambiente local do projeto e depois o Python disponível no computador. O primeiro ensaio analisou 12 exames (2022–2026), 142 páginas de exercícios, e encontrou sete provas para «equilíbrio químico». O índice inicial ficou guardado localmente em `data/index.json`. O IAVE estava indisponível; os documentos foram obtidos nas fontes alternativas identificadas.

1. Em **Ficheiro → Abrir Pasta**, escolha esta pasta `pesquisador-exames-fqa`.
2. Instale Python 3.10 ou superior e, no VS Code, a extensão oficial Python da Microsoft, caso ainda não os tenha.
3. Abra **Terminal → Novo Terminal** e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe pesquisador.py
```

4. Abra **http://localhost:8787** no browser. Mantenha o terminal aberto.
5. Na primeira execução, o programa consulta as fontes e analisa os exames. Aguarde a contagem da biblioteca e depois pesquise. O botão **Atualizar exames na Internet** volta a consultar as fontes. Não é necessária uma chave de API.

Se o comando `py` não existir, use `python` para criar o ambiente. No macOS/Linux: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt` e `.venv/bin/python pesquisador.py`.

## Como funciona e o que garante

- Consulta os índices públicos configurados no ficheiro `pesquisador.py`: IAVE e Aprende Aqui, mais um exame inicial da EduQA. Os índices podem disponibilizar apenas alguns anos; não existe promessa de cobertura de todo o arquivo nacional.
- Descarrega os enunciados pela Internet. Confirma no texto da capa a disciplina, o código 715, o ano e a fase. Os critérios não entram como enunciados. Ligações adjacentes para critérios são disponibilizadas quando encontradas, mas não são analisadas nesta versão.
- Se uma fonte falhar, a aplicação mantém os exames já analisados e mostra avisos. As cópias alojadas fora do IAVE são identificadas. O ficheiro `data/index.json` guarda o texto e a proveniência para pesquisas seguintes; não faz uma pesquisa geral no Google a cada pergunta. O botão de atualização pesquisa novamente os índices conhecidos.
- Pesquisa no texto por palavras e expressões relacionadas de um pequeno vocabulário de FQA. Não é um modelo de linguagem nem uma classificação semântica exaustiva. Cada mensagem é uma pesquisa independente. Tópicos que só apareçam em imagens, gráficos, fórmulas ilegíveis ou PDF digitalizados podem não ser encontrados. Não inclui OCR.
- Exclui as primeiras três páginas dos exames recentes (capa, formulário e tabela periódica), para reduzir correspondências sem perguntas. Este critério terá de ser adaptado antes de alargar a exames mais antigos com outra estrutura.
- As páginas indicadas são as páginas do ficheiro PDF. A indicação de questão é apenas uma referência próxima extraída do texto, quando possível; confirme-a no documento. Os resultados não inventam números de questões em falta.
- Deduplica por ano/fase e conserva uma versão de cada prova; não compara todas as versões nem resolve exercícios. No máximo, apresenta 20 exames e três páginas por exame.
- A atualização automática acrescenta documentos, mas reutiliza o texto de URLs já analisados. Para forçar a releitura de um documento substituído no mesmo endereço, feche a aplicação e remova `data/index.json` antes de voltar a iniciá-la.
- O programa serve apenas no computador local. A publicação para alunos exigirá alojamento do programa Python; o GitHub Pages por si só não executa este servidor.

## Exemplos

`equilíbrio químico`, `energia e movimentos`, `solubilidade`, `constante de acidez`, `refração`.

## Testar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Para atualizar sem iniciar o servidor: `python pesquisador.py --refresh`.

## Próximas melhorias possíveis

Expandir o arquivo de anos, melhorar a identificação exata das questões, rever as correspondências com um professor, acrescentar OCR e, se necessário, um modelo de linguagem com respostas ancoradas nas passagens encontradas. A primeira versão privilegia referências verificáveis.

Fontes: [IAVE](https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/), [Aprende Aqui](https://aprendeaqui.pt/fisica-e-quimica-a/), [EduQA](https://eduqa.pt/). Leitura de PDF: [pypdf](https://pypdf.readthedocs.io/).
