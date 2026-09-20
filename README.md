# Laboratório 1 — Web scraping de vagas

Portal: [ProgramaThor](https://programathor.com.br/jobs). Área: desenvolvimento de software com **Python**.

## Executar

No macOS, habilite **Permitir Automação Remota** no menu Desenvolvedor do Safari. Feche outras sessões de automação do Safari antes de executar.

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python busca.py
```

São usadas apenas Selenium e BeautifulSoup como bibliotecas externas. `csv`, `datetime`, `pathlib`, `time` e `urllib` fazem parte da biblioteca padrão do Python. Nenhuma API do portal é consultada pelo código.

O programa usa o Selenium para abrir a lista geral de vagas e clicar no link **Vagas programador PYTHON**, oferecido pelo próprio portal. Portanto, a busca por tecnologia é realizada por uma interação com o site, sem começar em uma URL de resultados filtrados. Não se trata de uma pesquisa de texto livre: é o filtro de área/tecnologia do portal.

## Etapas do código

1. Abrir `/jobs` e clicar no filtro de Python.
2. Percorrer três páginas pelos links de próxima página do site.
3. Usar BeautifulSoup para guardar os links dos anúncios e remover links repetidos.
4. Abrir cada vaga, confirmar sua URL canônica e extrair os campos do HTML.
5. Salvar os dados em CSV; o resumo da execução e os erros aparecem no terminal.

`PAGINAS = 3` e `INTERVALO = 5` ficam no começo de `busca.py`. O intervalo é em segundos e reduz o ritmo de acessos; não é garantia contra bloqueios. O Safari usa `page_load_strategy = "none"`; as esperas explícitas verificam os elementos necessários, em vez de depender do término do carregamento de anúncios e outros recursos.

## Arquivos

- `busca.py`: navegação, controle da coleta, deduplicação, tratamento de falhas e gravação.
- `extracao.py`: funções que recebem HTML e retornam os dados, sem acessar a rede.
- `dados/vagas.csv`: arquivo de vagas para a entrega.
- `relatorio_lab1.tex`: relatório para compilar no Overleaf com pdfLaTeX; preencha instituição, curso, turma, participantes e cidade na capa.

Uma nova execução substitui `dados/vagas.csv`. O programa analisa o HTML em memória, sem guardar uma cópia de cada página.

## Campos e limitações

São coletados `titulo`, `empresa`, `local`, `faixa_salarial`, `link`, `descricao` (atividades) e `requisitos`. Acrescentamos `pagina`, `coletado_em` e `situacao` para rastrear a origem. Texto ausente ou vazio recebe **Não informado**; isso não equivale a salário zero.

O salário é preservado como publicado, inclusive expressões como “Até R$18.000”. Não se presume uma remuneração mensal nem se transforma um teto em uma faixa inventada. A descrição e os requisitos são armazenados em colunas separadas.

O portal mistura anúncios com e sem o selo **Vencida**. Ambos são coletados, registrando essa condição. **Sem selo de vencida** significa somente que o selo não apareceu na listagem; não é uma confirmação independente de que a vaga continua aberta.

Deduplicação é feita pelo link canônico do anúncio na lista. Anúncios com IDs distintos são mantidos, mesmo quando seus títulos coincidem. Páginas que não carregam o conteúdo esperado são informadas no terminal e não geram linhas inventadas no CSV. Um bloqueio identificado interrompe novas tentativas; Ctrl+C preserva os registros já coletados.

## Robots e sitemap

Na consulta preparatória de **20/09/2026**, o bloco `User-agent: *` restringiu `/admin/`, `/user/`, `/users/` e `/company/`. As rotas `/jobs`, `/jobs-python` e `/jobs/...` não estão nessas restrições. O programa não acessa os caminhos restringidos, não realiza login e não envia candidaturas. **A verificação de robots.txt e sitemap é manual, fora do código; antes da entrega, confira pessoalmente os documentos atuais.**

O [robots.txt](https://programathor.com.br/robots.txt) indica o [sitemap.xml](https://programathor.com.br/sitemap.xml). Na consulta preparatória, o sitemap continha **30.382 URLs**, incluindo categorias por tecnologia, localidades e anúncios individuais. O sitemap não é usado como fonte de vagas nem como atalho para a busca.

O Vagas.com.br foi abandonado após apresentar uma página de bloqueio. A análise inicial fornecida no contexto também registrou o descarte do Indeed por restrições nas páginas individuais de vagas. Essas observações são histórico do desenvolvimento, não afirmações de que as regras desses portais nunca mudam.

## Métodos de localização usados

| Método | Seletor ou operação | O que localiza |
|---|---|---|
| Selenium `By.LINK_TEXT` | `Vagas programador PYTHON` | Link visível que filtra as vagas por Python. |
| Selenium `By.TAG_NAME` | `h1` | Cabeçalho usado para confirmar que a busca por Python carregou. |
| CSS | `.pagination .active` | Item marcado como página atual na paginação. |
| CSS | `.pagination a[rel="Próx"]` | Link oferecido pelo portal para avançar uma página. |
| CSS | `.cell-list > a[href]` | Link principal de cada card da lista de vagas. |
| BeautifulSoup `select_one` | `h3`, dentro do card | Título de um anúncio. |
| BeautifulSoup `select` | `span`, dentro do título | Selos do título; identifica e remove apenas o texto “Vencida”. |
| CSS | `link[rel="canonical"]` | URL canônica no HTML; confirma qual vaga está carregada. |
| CSS | `.wrapper-content-job-show .line-height-2-4` | Bloco principal de texto da página individual. |
| BeautifulSoup `select_one` | `.wrapper-content-job-show` | Contêiner dos dados da vaga. |
| BeautifulSoup `select_one` | `.wrapper-header-job-show h1` | Título na página individual. |
| BeautifulSoup `select_one` | `h2`, dentro do contêiner da vaga | Nome da empresa, com ou sem link para seu perfil. |
| BeautifulSoup `select` | `.wrapper-details-job-show p` | Parágrafos de metadados; os rótulos “Localização:” e “Salário:” identificam os campos desejados. |
| BeautifulSoup `select` | `.line-height-2-4 h3` | Cabeçalhos das seções de texto. |
| BeautifulSoup `find_next_siblings` | Irmãos até o próximo `h3` | Conteúdo das seções “Atividades e Responsabilidades” e “Requisitos”. |

Não são usados XPath, expressões regulares nem APIs para extrair vagas. `get_text`, `split` e `join` limpam o texto; não são seletores. `urljoin` transforma links relativos em URLs completas.

## Declaração de uso de IA

Foi utilizado o **OpenAI Codex** para auxiliar na escolha e verificação do portal, diagnóstico de problemas do Safari/Selenium, implementação e revisão do código, identificação de seletores, execução e validação da coleta e preparação desta documentação. Os dados foram extraídos do HTML do portal, sem gerar vagas, salários ou requisitos artificialmente.

Antes da entrega, o(s) aluno(s) deve(m) revisar o código e adequar a declaração ao uso efetivamente realizado. A tabela e a metodologia acima servem de base para o relatório de até duas páginas exigido no enunciado; este README não tem limite de duas páginas.
