# USI Generator / TalentMaterialGenerator - Fonte completa do projeto

Este documento descreve o estado atual real da codebase do projeto `TalentMaterialGenerator`, tambem chamado na interface de **USI Generator**. Ele foi escrito para servir como fonte de contexto em conversas com ChatGPT Web ou outros agentes de IA.

## Resumo executivo

O projeto e um aplicativo desktop Windows feito em Python para gerar materiais de Talent Development a partir de uma planilha Excel de colaboradores.

O app possui dois fluxos principais:

- **Ficha de Curriculo**: busca um colaborador por nome ou matricula em uma base padronizada e gera uma ficha individual em PowerPoint.
- **Carometro**: carrega colaboradores da base, permite pesquisar e selecionar pessoas, escolhe um template de carometro e gera um PowerPoint com os selecionados distribuídos nos slots do template.

A aplicacao roda localmente, usa PySide6 para interface desktop, `openpyxl` para leitura de planilhas e `python-pptx` para manipulacao e geracao de arquivos PowerPoint. O projeto tambem tem suporte de infraestrutura para download/cache de fonte remota via URL HTTPS/OneDrive, embora a UI atual trabalhe de forma explicita apenas com **arquivo local** e com a **base padrao cacheada/configurada**.

## Objetivo do produto

O objetivo e reduzir trabalho manual na montagem de materiais de RH/Talent Development. Em vez de copiar dados manualmente da planilha para PowerPoint, o usuario configura uma base Excel, busca pessoas e gera arquivos `.pptx` com layout padronizado.

O projeto foi reconstruido para abandonar uma base antiga em CustomTkinter e adotar uma arquitetura PySide6 com:

- telas separadas;
- tema claro/escuro por QSS;
- sidebar recolhivel;
- workers em `QThread` para nao travar a interface;
- geracao de PPTX baseada em templates e funcoes core;
- cache local de base;
- testes unitarios e de integracao.

## Stack tecnologica

### Linguagem e runtime

- Python 3.11+ como alvo de desenvolvimento.
- Projeto orientado a Windows, especialmente para build e exportacao via COM/PowerPoint.

### Interface grafica

- `PySide6>=6.6.0`
- Componentes principais:
  - `QApplication`
  - `QMainWindow`
  - `QStackedWidget`
  - `QFrame`
  - `QPushButton`
  - `QLineEdit`
  - `QComboBox`
  - `QTableWidget`
  - `QListWidget`
  - `QProgressBar`
  - `QTextEdit`
  - `QThread`
  - `Signal`

### PowerPoint

- `python-pptx>=0.6.23`
- Usado para:
  - criar fichas do zero;
  - abrir templates `.pptx` de carometro;
  - clonar slides;
  - trocar textos preservando estilos;
  - trocar imagens por placeholder circular;
  - salvar arquivos `.pptx`.

### Planilhas

- `openpyxl>=3.1.2`
- A leitura e feita diretamente da primeira aba ativa do `.xlsx`.
- O projeto nao usa pandas no estado atual, apesar de documentos antigos citarem essa dependencia.

### Rede/cache

- `requests>=2.31.0`
- Usado por `app/core/reader.py` para baixar planilhas remotas quando a fonte informada começa com `https://`.

### PDF

- `comtypes>=1.4.0` apenas no Windows.
- `app/core/pdf_exporter.py` tenta converter PPTX para PDF usando:
  1. LibreOffice headless, se encontrado em caminhos padrao;
  2. fallback por automacao COM do PowerPoint via `comtypes`.
- Importante: o fluxo principal atual da UI gera `.pptx`; o exportador PDF existe como utilitario core, mas nao e o centro da UX atual.

### Build e empacotamento

- `pyinstaller>=6.0.0`
- `build.bat` executa:

```bat
pyinstaller ^
  --noconfirm ^
  usi_generator.spec
```

- `usi_generator.spec` coleta:
  - todos os dados/binarios/hidden imports do PySide6;
  - todos os templates `.pptx` da pasta `carometros`;
  - executavel final chamado `USI Generator`.

### Qualidade e testes

- `pytest`
- `pytest-cov`
- `pytest-mock`
- `pytest-qt`
- `black`
- `flake8`
- `mypy`

O comando de entrega completo esta em `scripts/delivery_check.bat` e roda:

1. `scripts/check_architecture.py`
2. `black --check app tests`
3. `flake8 app tests`
4. `mypy app`
5. `pytest -q`

## Estrutura do repositorio

```text
TalentMaterialGenerator/
  main.py
  README.md
  requirements.txt
  requirements-dev.txt
  pytest.ini
  build.bat
  usi_generator.spec
  Ficha Curriculo modelo.pptx
  PlanilhaFichaCarom.xlsx
  carometros/
    Carometro-big.pptx
    Carometro-mini.pptx
    CarometroProjetoTrainee.pptx
    CarometroTalentReview.pptx
  app/
    config/
      settings.py
      theme.py
    core/
      base_cache.py
      carom_templates.py
      generator_carom.py
      generator_ficha.py
      pdf_exporter.py
      pptx_template_utils.py
      reader.py
      resource_paths.py
      worker.py
    ui/
      app_window.py
      components.py
      screen_carom.py
      screen_ficha.py
      screen_home.py
      screen_progress.py
      screen_settings.py
  scripts/
    check_architecture.py
    delivery_check.bat
  tests/
    conftest.py
    fixtures/
    integration/
    unit/
  docs/
    estado_atual_projeto_para_ia.md
    rebuild_v2_plan.md
```

## Ponto de entrada

O ponto de entrada e `main.py`.

Fluxo:

1. cria `QApplication`;
2. carrega configuracao persistida com `settings.load_config()`;
3. define o nome da aplicacao como `USI Generator`;
4. aplica stylesheet QSS com `theme.build_stylesheet(config.get("theme", "dark"))`;
5. instancia `AppWindow(config)`;
6. exibe a janela e entra no loop `app.exec()`;
7. se ocorrer erro no bootstrap, imprime em `stderr` e retorna codigo `1`.

## Arquitetura em camadas

### `app/config`

Responsavel por configuracao persistida e tema visual.

- `settings.py`: leitura, escrita, defaults e caminhos de configuracao/cache.
- `theme.py`: paleta clara/escura e geracao de QSS.

### `app/core`

Responsavel por regras e operacoes sem dependencia da UI.

- `reader.py`: leitura de planilha, deteccao de colunas, remapeamento, validacao, download/cache de origem remota.
- `base_cache.py`: cadastro/validacao/cache da base padrao local.
- `generator_ficha.py`: geracao de ficha individual em PPTX.
- `generator_carom.py`: geracao de carometros a partir de templates PPTX.
- `carom_templates.py`: metadados dos templates, capacidades, slots e campos obrigatorios.
- `pptx_template_utils.py`: utilitarios para clonar slides, substituir texto, resolver shapes por caminho e gerar placeholders circulares.
- `pdf_exporter.py`: conversao PPTX para PDF.
- `resource_paths.py`: resolucao de recursos tanto em dev quanto em executavel empacotado.
- `worker.py`: workers `QThread` para validacao/busca/geracao.

Regra de arquitetura: `app/core` nao deve importar `app/ui`. Essa regra e checada por `scripts/check_architecture.py`.

### `app/ui`

Responsavel por interface, navegacao e interacao com usuario.

- `app_window.py`: janela principal, sidebar, topbar, navegacao, tema, workers e historico.
- `components.py`: cards, badges, botoes de navegacao e helpers visuais.
- `screen_home.py`: dashboard inicial.
- `screen_ficha.py`: fluxo de busca e geracao de ficha.
- `screen_carom.py`: fluxo de selecao e geracao de carometro.
- `screen_progress.py`: progresso e log de jobs.
- `screen_settings.py`: configuracao da base padrao e TTL do cache.

## Configuracao persistida

Configuracoes sao salvas em:

```text
%APPDATA%\USIGenerator\config.json
```

Cache fica em:

```text
%APPDATA%\USIGenerator\cache
```

Principais chaves em `DEFAULT_CONFIG`:

- `theme`: `dark` ou `light`;
- `spreadsheet_source`: atualmente normalizado para `local`;
- `default_spreadsheet_path`: caminho da planilha local original;
- `default_spreadsheet_name`: nome do arquivo da base;
- `default_spreadsheet_mtime`: timestamp de modificacao da base original;
- `default_spreadsheet_size`: tamanho da base original;
- `default_base_cache_path`: caminho da copia em cache;
- `default_base_row_count`: quantidade de linhas validas;
- `default_base_status`: estado da base (`not_configured`, `ready`, `modified`, `missing`, `invalid`, `updated`);
- `default_output_dir`: pasta de saida calculada;
- `default_grouping`: valor legado/default para agrupamento;
- `default_carom_columns`: valor legado/default;
- `cache_enabled`: habilita cache;
- `cache_ttl_hours`: TTL padrao do cache, 24 horas;
- `refresh_strategy`: estrategia descritiva de refresh;
- `last_cache_sync`: data da ultima sincronizacao;
- `last_generations`: historico recente.

`settings._apply_runtime_defaults()` força alguns defaults em runtime:

- `default_output_dir` sempre vira `~/Documents/Usi Generator`;
- `spreadsheet_source` vira `local`;
- `default_onedrive_url` e removido;
- se houver `PlanilhaTeste.xlsx` na raiz e nenhum caminho padrao configurado, esse arquivo pode virar default.

## Diretorios de saida

A pasta base de saida e:

```text
~/Documents/Usi Generator
```

As fichas sao salvas em:

```text
~/Documents/Usi Generator/fichas
```

Os carometros sao salvos em:

```text
~/Documents/Usi Generator/carometros
```

Atualmente a UI exibe essa pasta padrao, mas nao oferece um seletor livre de saida nos fluxos principais.

## Tema visual

O visual e todo definido em `app/config/theme.py` por QSS.

Temas:

- `dark`
- `light`

Cada tema define:

- fundo geral;
- fundo da sidebar;
- superficies/cards;
- bordas;
- texto principal/muted/dim;
- verde de destaque;
- cores de sucesso/aviso/erro/info;
- estado de inputs;
- botoes;
- badges;
- tabelas;
- listas;
- progress bar.

Cores importantes:

- Verde Usiminas/UI: `#84BD00`
- Verde de slide/titulo de ficha: `#92D050` em documentos antigos, mas o gerador atual usa `#257226` como `VERDE_TITULO`.
- Aviso: `#F59E0B`
- Erro: `#EF4444`

## Fonte de dados e cache

### Leitura de planilha

`reader.read_spreadsheet(path)`:

1. valida existencia do arquivo;
2. abre workbook com `openpyxl.load_workbook(..., data_only=True)`;
3. usa a aba ativa;
4. interpreta a primeira linha como cabecalho;
5. ignora cabecalhos vazios;
6. transforma cada linha preenchida em `dict[str, str]`;
7. descarta linhas sem nenhum valor.

### Deteccao de colunas

`reader.detect_columns(headers)` normaliza acentos, caixa e espacos para comparar cabecalhos com aliases.

Campos reconhecidos incluem:

- `matricula`
- `nome`
- `idade`
- `cargo`
- `antiguidade`
- `formacao`
- `resumo_perfil`
- `trajetoria`
- `nota_2025`
- `nota_2024`
- `nota_2023`
- `performance`
- `area`
- `potencial`
- `nota`
- `foto`
- `localizacao`
- `unidade_gestao`
- `ceo1`
- `ceo2`
- `ceo3`
- `ceo4`

Para avaliacoes anuais, ha logica especifica para:

- `avaliacao_2025`, `avaliacao 2025`
- `score_2025`, `score 2025`
- `nota_2025`, `nota 2025`
- `potencial_2025`, `potencial 2025`

O mesmo padrao existe para 2024 e 2023 no fluxo da ficha.

### Campos obrigatorios

Ficha:

- `matricula`
- `nome`
- `cargo`

Carometro:

- `matricula`
- `nome`
- `cargo`

Os templates de carometro podem exigir campos adicionais.

### Remapeamento da ficha

`reader.remap_ficha_row()` cria um `FichaEmployee` com:

- dados basicos;
- campos de avaliacao anuais;
- `nota_<ano>` calculada de forma amigavel.

Regra de exibicao da nota anual:

1. se existir valor consolidado em `avaliacao_<ano>`, usa esse valor;
2. senao, se houver `score_<ano>` e `potencial_<ano>`, exibe `score / potencial`;
3. senao, usa apenas `score`;
4. senao, usa apenas `potencial`;
5. senao, usa `nota_<ano>` direta.

Valores vazios, `#N/A` e `N/A` sao tratados como vazio.

### Remapeamento do carometro

`reader.remap_carom_row()` cria um `CaromEmployee` com os campos necessarios para templates:

- identidade: matricula, nome, idade, cargo;
- conteudo: formacao, resumo, trajetoria;
- organizacao: area, localizacao, unidade_gestao, ceo1, ceo2, ceo3, ceo4;
- avaliacao 2025: `nota_2025`, `avaliacao_2025`, `score_2025`, `potencial_2025`;
- `foto`, embora o fluxo atual substitua imagens por placeholder.

### Busca de ficha

`reader.lookup_ficha_employees()`:

- exige nome ou matricula;
- carrega linhas padronizadas;
- se matricula for informada, busca correspondencia exata normalizada;
- se nome for informado, faz busca por substring normalizada;
- limita buscas por nome a `MAX_FICHA_NAME_MATCHES = 25`;
- se uma matricula corresponder a mais de um colaborador, lança erro.

### Busca de carometro

`reader.filter_carom_employees()`:

- se query vazia, retorna todos;
- no modo `matricula`, tenta primeiro match exato e depois substring;
- no modo `nome`, usa substring normalizada.

### Fonte remota/OneDrive

`reader.resolve_spreadsheet_source(entry, cache_enabled=True, cache_ttl_hours=24, force_refresh=False)`:

- se `entry` nao começa com `https://`, trata como caminho local;
- se começa com `https://`, converte o link para download direto com `download=1`;
- usa hash MD5 da URL para criar caminho de cache `.xlsx`;
- se cache esta fresco e nao ha `force_refresh`, usa o cache;
- senao tenta baixar com `requests.get(..., timeout=15)`;
- se baixar e cache estiver habilitado, salva no cache;
- se falhar mas existir cache, usa o cache como fallback;
- se falhar sem cache, lança erro com mensagem orientada ao usuario.

Observacao importante: a UI atual de Ficha e Carometro mostra apenas a opcao "Arquivo local". O suporte remoto existe no core e nos workers, mas nao esta exposto como modo separado na interface atual.

## Base padrao e cache local

`app/core/base_cache.py` implementa o fluxo de base padrao usado pelas telas.

### Atualizar base a partir de arquivo

`update_default_base_from_file(path)`:

1. valida se o arquivo existe;
2. valida se e `.xlsx`;
3. le a planilha;
4. valida schemas de ficha e carometro;
5. copia o arquivo para `%APPDATA%\USIGenerator\cache\default_base.xlsx`;
6. salva metadados no config:
   - caminho original;
   - nome;
   - mtime;
   - tamanho;
   - caminho do cache;
   - contagem de linhas;
   - status `ready`;
   - data da sincronizacao.

### Refresh de base

`refresh_default_base(config)`:

- se nao ha base configurada, status `not_configured`;
- se original sumiu, status `missing`;
- se cache esta atualizado em relacao a mtime/tamanho, status `unchanged`;
- se original mudou, revalida e recopia.

### Caminho efetivo da base

`get_effective_base_path(config)` prioriza:

1. `default_base_cache_path`, se existir;
2. `default_spreadsheet_path`, se existir;
3. vazio.

As telas de Ficha e Carometro usam esse caminho efetivo ao carregar configuracao.

## Geracao de ficha

Arquivo: `app/core/generator_ficha.py`

### Saida

`generate_ficha_pptx(employee, output_dir, callback=None)`:

- cria pasta `output_dir/fichas`;
- cria um PowerPoint novo;
- adiciona um slide com layout em branco;
- desenha todos os elementos diretamente por `python-pptx`;
- salva `Nome_Normalizado.pptx`;
- emite callback de log/progresso.

No estado atual, a ficha gera **um arquivo por colaborador selecionado**, acionado de forma individual pela tela de Ficha.

### Dimensoes do slide

O gerador atual usa:

```python
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.500)
```

Documentos antigos citam `13.271`, mas o codigo atual usa `13.333`.

### Layout e conteudo

A ficha e montada por coordenadas fixas:

- acento verde lateral esquerdo;
- barra verde no rodape;
- bloco de marca `USIMINAS`;
- placeholder circular de foto;
- nome em caixa alta;
- metadados:
  - cargo;
  - idade;
  - tempo de Usiminas;
- secao `Formacao`, se houver conteudo;
- secao `Resumo`, se houver conteudo;
- secao `Trajetoria Profissional`, se houver conteudo;
- secao `Performance e Potencial`, se houver notas anuais.

### Placeholder de foto

A ficha nao busca nem insere foto real.

`_add_photo_placeholder()` usa `add_circular_picture_placeholder()` de `pptx_template_utils.py`, que cria uma imagem PNG solida 1x1 e aplica geometria eliptica/circular. O placeholder tem borda verde (`VERDE_PLACEHOLDER = "#7CAF3D"`) com 2pt.

### Tratamento de texto

- Campos vazios nao geram secao.
- `parse_multiline_field()` quebra valores por `;` e por quebras de linha.
- Trajetoria e renderizada como linhas simples; se uma linha terminar com `:`, fica em negrito/italico.
- Performance e Potencial usa anos 2025, 2024 e 2023, cada item como bullet com ano em negrito.

### Nome de arquivo

`normalize_filename()` remove acentos e troca espacos por `_`. O gerador usa `Colaborador.pptx` como fallback.

## Geracao de carometro

Arquivos:

- `app/core/generator_carom.py`
- `app/core/carom_templates.py`
- templates em `carometros/*.pptx`

### Ideia geral

O carometro nao e desenhado do zero. O sistema abre um template PPTX existente, localiza shapes por indices/caminhos e troca textos/imagens nos slots.

O primeiro slide do template serve como base. Se o numero de selecionados exceder a capacidade do template, o slide e clonado por `clone_slide()`.

### Presets/templates disponiveis

#### `mini`

- Label: `Mini`
- Arquivo: `Carometro-mini.pptx`
- Capacidade: 18 pessoas
- Titulo editavel: sim
- Campos obrigatorios: `nome`, `cargo`
- Requer score/potencial exibivel: nao
- Grade: 6 linhas x 3 colunas
- Ordem: `column_major`
- Linhas por pessoa:
  - nome;
  - cargo + idade;
  - `ceo3`.

#### `big`

- Label: `Big`
- Arquivo: `Carometro-big.pptx`
- Capacidade: 8 pessoas
- Titulo editavel: sim
- Campos obrigatorios: `nome`, `cargo`, `idade`, `formacao`, `ceo3`
- Requer score/potencial exibivel: sim
- Grade: 4 linhas x 2 colunas
- Ordem: `column_major`
- Linhas por pessoa:
  - nome + idade + nota/potencial;
  - formacao;
  - cargo;
  - `ceo3`.

#### `projeto_trainee`

- Label: `Projeto Trainee`
- Arquivo: `CarometroProjetoTrainee.pptx`
- Capacidade: 2 pessoas
- Titulo editavel: nao
- Campos obrigatorios: `nome`, `cargo`, `idade`, `formacao`, `ceo4`
- Requer score/potencial exibivel: sim
- Linhas de identidade:
  - nome + idade + nota/potencial;
  - cargo;
  - formacao;
  - `ceo4`.
- Corpo recebe texto fixo: `insira projeto trainee aqui`.

#### `talent_review`

- Label: `Talent Review`
- Arquivo: `CarometroTalentReview.pptx`
- Capacidade: 12 pessoas
- Titulo editavel: nao
- Campos obrigatorios: `nome`, `cargo`, `idade`
- Requer score/potencial exibivel: sim
- Grade: 4 linhas x 3 colunas
- Ordem: `column_major`
- Linhas por pessoa:
  - nome + idade + nota/potencial;
  - cargo;
  - `Sucessor Imediato`;
  - `NomeCadeira`;
  - `Em desenvolvimento`;
  - `NomeCadeira`.

### Validacao por preset

Antes de gerar, `validate_carom_schema_for_preset()` e `validate_carom_employee_for_preset()` garantem que:

- as colunas exigidas existem no schema da planilha;
- cada colaborador selecionado possui os campos obrigatorios;
- templates que precisam de score/potencial tem algum campo valido para compor a exibicao.

### Nome de arquivo

`build_carom_output_filename()` gera:

```text
<basename>_<ddMMyyyy_HHMMSS>.pptx
```

O basename vem do titulo normalizado da tela. Se houver colisao no mesmo segundo, o codigo espera mudar o timestamp.

### Placeholder de foto no carometro

Cada slot troca a imagem existente do template por um placeholder circular gerado em memoria. O codigo ajusta a imagem para ficar quadrada/circular com base no menor lado do shape.

### Clonagem de slides

`pptx_template_utils.clone_slide()`:

- cria slide em branco;
- copia todos os elementos XML do slide de template;
- remapeia relacionamentos internos e externos;
- permite que imagens e formas funcionem no slide clonado.

## Workers e execucao assíncrona

Arquivo: `app/core/worker.py`

O projeto usa `QThread` para nao travar a interface durante validacoes, buscas e geracoes.

### `FichaLookupWorker`

Usado pela tela de Ficha para:

1. resolver fonte de planilha;
2. ler linhas;
3. validar schema padronizado da ficha;
4. opcionalmente buscar colaboradores por nome/matricula;
5. emitir `succeeded(dict)` com schema, matches, source_result, row_count e headers;
6. emitir `error(str)` em falhas;
7. limpar fonte temporaria, se houver.

### `CaromLookupWorker`

Usado pela tela de Carometro para:

1. resolver fonte;
2. ler linhas;
3. validar schema padronizado do carometro;
4. remapear colaboradores;
5. emitir lista carregada e metadados.

### `GenerationWorker`

Usado para gerar ficha ou carometro.

Sinais:

- `progress(int current, int total, str name)`
- `log(str message, str level)`
- `finished(dict result)`
- `error(str message)`

Fluxo da ficha:

1. recebe `selected_employee`;
2. valida campos obrigatorios;
3. chama `generate_ficha_pptx()`;
4. retorna lista com o arquivo gerado.

Fluxo do carometro:

1. recebe `selected_employees`;
2. valida selecao;
3. valida preset/schema/campos obrigatorios;
4. monta `CaromConfig`;
5. chama `generate_carom_pptx()`;
6. retorna lista com arquivo(s) gerado(s).

## Interface principal

Arquivo: `app/ui/app_window.py`

`AppWindow` e uma `QMainWindow` com:

- sidebar lateral;
- topbar;
- `QStackedWidget`;
- telas Home, Ficha, Carometro, Geracao e Configuracoes.

### Sidebar

- Largura expandida: 248px.
- Largura recolhida: 88px.
- Animacao: 180ms com `QPropertyAnimation`.
- Itens:
  - Inicio;
  - Ficha;
  - Carometro;
  - Geracao;
  - Configuracoes.

### Topbar

- Botao para recolher/expandir sidebar.
- Titulo da tela atual.
- Botao de tema, que alterna claro/escuro em tempo real.

### Estado de geracao

`AppWindow` garante que apenas um worker de geracao rode por vez. Durante geracao:

- botoes de gerar das telas sao desabilitados;
- settings ficam desabilitadas;
- o usuario e levado para a tela de progresso.

### Historico e metricas

A janela mantem:

- `_stats`: contadores em memoria de fichas e carometros gerados na sessao;
- `_history`: historico carregado/salvo em `last_generations`, limitado a 10 entradas.

Ao finalizar um job, o historico e salvo no config.

## Tela Home

Arquivo: `app/ui/screen_home.py`

Funcoes:

- dashboard inicial;
- cards de atalho para Ficha e Carometro;
- historico recente;
- metricas:
  - fichas geradas;
  - carometros gerados;
  - operacoes registradas.

Emite sinais:

- `ficha_requested`
- `carom_requested`
- `settings_requested`

## Tela de Ficha

Arquivo: `app/ui/screen_ficha.py`

### Fluxo da tela

1. carrega configuracao;
2. pega base efetiva por `base_cache.get_effective_base_path(config)`;
3. se houver base local/cache valida, inicia validacao do schema;
4. usuario escolhe tipo de busca:
   - Nome;
   - Matricula;
5. usuario pesquisa;
6. resultados aparecem em tabela com:
   - Matricula;
   - Nome;
   - Cargo;
7. usuario seleciona uma linha e clica em `Validar colaborador`;
8. o botao `Gerar ficha` e liberado;
9. a tela emite `generate_requested` com colaborador selecionado.

### Fonte de dados na UI

O combo mostra apenas:

```text
Arquivo local
```

A entrada e um caminho de `.xlsx`.

### Status de schema

A tela valida automaticamente a base ao finalizar edicao do caminho. A validacao chama `FichaLookupWorker(validate_only=True)`.

### Payload de geracao

Inclui:

- `spreadsheet_source`;
- `source_kind`;
- `output_dir`;
- `selected_employee`;
- `source_result`.

## Tela de Carometro

Arquivo: `app/ui/screen_carom.py`

### Fluxo da tela

1. carrega base efetiva;
2. valida planilha com `CaromLookupWorker`;
3. carrega todos os colaboradores remapeados;
4. usuario escolhe modelo:
   - Mini;
   - Big;
   - Projeto Trainee;
   - Talent Review;
5. modelos incompatíveis com o schema ficam desabilitados;
6. usuario pesquisa por nome ou matricula;
7. resultados aparecem em lista paginada;
8. usuario adiciona/remover pessoas da selecao;
9. tela mostra:
   - total selecionado;
   - capacidade por slide;
   - slides previstos;
   - status do slide atual;
10. botao `GERAR CAROMETRO` e liberado quando ha schema valido, preset compativel, titulo valido e ao menos uma pessoa selecionada.

### Paginacao

- Tamanho de pagina: 50 colaboradores.
- Botoes: Anterior/Proximo.

### Titulo

- `mini` e `big`: titulo editavel.
- `projeto_trainee` e `talent_review`: titulo fixo do preset e campo fica desabilitado.

### Payload de geracao

Inclui:

- `output_dir`;
- `selected_employees`;
- `source_result`;
- `schema_fields`;
- `preset_id`;
- `titulo`;
- `file_basename`.

## Tela de Progresso

Arquivo: `app/ui/screen_progress.py`

Mostra:

- badge de estado;
- subtitulo do job;
- percentual;
- contagem processada;
- status;
- barra de progresso;
- contador textual;
- log HTML colorido.

Estados:

- em execucao;
- concluido;
- falha.

Acoes:

- `Abrir pasta de saida`;
- `Nova geracao`.

O log usa prefixos:

- `[OK]`
- `[WARN]`
- `[ERRO]`
- `[INFO]`

## Tela de Configuracoes

Arquivo: `app/ui/screen_settings.py`

Permite:

- visualizar planilha local padrao;
- visualizar pasta de saida padrao;
- configurar TTL do cache entre 1 e 168 horas;
- procurar arquivo `.xlsx` para definir base padrao;
- atualizar base agora;
- salvar configuracoes;
- restaurar padroes.

Esta tela nao altera regras de geracao. Ela existe principalmente para controlar base/cache.

## Componentes reutilizaveis

Arquivo: `app/ui/components.py`

Componentes:

- `SectionCard`: card com titulo/subtitulo e layout de corpo.
- `MetricCard`: card de metrica.
- `StatusBadge`: label com propriedade `tone`.
- `NavButton`: botao de navegacao da sidebar com modo compacto.
- `PreviewListItem`: item visual com iniciais, titulo, meta e acento.

Helpers:

- `repolish(widget)`: reaplica QSS apos mudar propriedades dinamicas.
- `clear_layout(layout)`: limpa widgets de um layout.
- `build_badge_row(badges)`: monta linha de badges.

## Utilitarios de PowerPoint

Arquivo: `app/core/pptx_template_utils.py`

Funcoes principais:

- `clone_slide(prs, template_slide)`: clona slide remapeando relacionamentos.
- `resolve_shape_path(container, path)`: navega em shapes por indices.
- `replace_text(shape, paragraphs)`: troca textos preservando estilo basico do primeiro run.
- `replace_text_prefix(shape, paragraphs)`: troca somente prefixo de paragrafos.
- `clear_text(shape)`: limpa texto.
- `replace_picture(slide, picture_shape, image_bytes)`: substitui imagem.
- `add_circular_picture_placeholder(...)`: adiciona placeholder circular.
- `reset_picture_to_circular_placeholder(...)`: converte imagem existente para placeholder circular.
- `placeholder_picture_bytes()`: gera PNG 1x1 em memoria.

Essas funcoes sao essenciais porque os templates de carometro dependem de indices de shapes. Alterar templates PPTX pode quebrar caminhos como `(17,)`, `(4, 0)` etc.

## Recursos empacotados

Arquivo: `app/core/resource_paths.py`

`get_runtime_root()` retorna:

- `sys._MEIPASS`, quando rodando empacotado;
- raiz do repositorio, quando em desenvolvimento.

`resolve_existing_resource_path()` lança erro amigavel quando um template/recurso nao foi empacotado.

## PDF

Arquivo: `app/core/pdf_exporter.py`

Funcoes:

- `find_libreoffice_path()`
- `is_libreoffice_available()`
- `try_comtypes_export(pptx_path, output_dir)`
- `export_to_pdf(pptx_path, output_dir)`

Limites:

- procura LibreOffice apenas em caminhos padrao de Windows;
- COM depende de PowerPoint instalado;
- retorna `False` em falhas em vez de propagar excecoes;
- nao esta ligado como etapa obrigatoria do fluxo principal atual.

## Testes

`pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=app --cov-report=term-missing --basetemp=pytest_tmp_root
```

`tests/conftest.py`:

- adiciona a raiz no `sys.path`;
- define `QT_QPA_PLATFORM=offscreen` para testes headless;
- redefine fixture `tmp_path` para usar `.tmp-test-ui`.

Cobertura por area:

- `tests/unit/config`: settings e theme;
- `tests/unit/core`: cache, templates, geradores, PDF, reader, workers;
- `tests/unit/ui`: telas e janela;
- `tests/integration`: fluxos de ficha, carometro e animacao da sidebar.

## Guardrails de arquitetura

`scripts/check_architecture.py` verifica:

- ausencia de imports legados:
  - `customtkinter`;
  - `PIL`;
  - `app.core.image_utils`;
- `app/core` nao importa `app/ui`;
- `app/core/worker.py` preserva contrato com `QThread` e `Signal`.

Esses guardrails indicam que a arquitetura atual deve permanecer separada em config/core/ui.

## Como rodar localmente

Criar ambiente:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Rodar app:

```powershell
python main.py
```

Rodar testes:

```powershell
python -m pytest
```

Rodar check completo:

```powershell
scripts\delivery_check.bat
```

Gerar executavel:

```powershell
build.bat
```

## Observacoes importantes para manutencao

1. A UI atual e PySide6; nao tratar o projeto como CustomTkinter.
2. O core nao deve depender da UI.
3. Os templates de carometro sao sensiveis a ordem/estrutura de shapes dentro dos arquivos PPTX.
4. Se um template PPTX for editado manualmente, revisar `carom_templates.py`.
5. A ficha e desenhada por coordenadas fixas em `generator_ficha.py`.
6. Documentos antigos podem citar dimensoes, dependencias ou fluxos que nao batem 100% com o codigo atual.
7. A UI atual expoe arquivo local/base padrao; suporte remoto HTTPS/OneDrive existe no core.
8. O fluxo principal gera PPTX; PDF e utilitario separado.
9. O diretorio de saida e fixado em `~/Documents/Usi Generator`.
10. O historico recente e limitado a 10 entradas e salvo em config.
11. O estado de metricas da Home e principalmente de sessao, enquanto o historico vem do config.
12. `settings.load_config()` e tolerante a config quebrada e volta aos defaults em excecoes.
13. `settings.save_config()` remove chaves antigas como `default_output_mode` e `default_onedrive_url`.
14. O cache da base padrao copia o arquivo selecionado para `%APPDATA%`, preservando uma versao validada.
15. A validacao minima de ficha/carometro exige matricula, nome e cargo, mas presets de carometro podem exigir mais campos.

## Estado funcional atual

Implementado:

- app desktop PySide6;
- tema claro/escuro;
- sidebar recolhivel;
- dashboard Home;
- configuracao de base padrao;
- cache local de base;
- validacao de planilha padronizada;
- busca de colaborador para ficha por nome ou matricula;
- geracao individual de ficha `.pptx`;
- carga de colaboradores para carometro;
- busca/paginacao de colaboradores no carometro;
- selecao manual de pessoas para carometro;
- templates Mini, Big, Projeto Trainee e Talent Review;
- geracao de carometro `.pptx`;
- tela de progresso com log;
- historico recente;
- build com PyInstaller;
- suite de testes unitarios/integracao.

Implementado no core, mas nao central na UI atual:

- resolucao de fonte HTTPS/OneDrive;
- cache por URL remota com TTL;
- exportacao PPTX para PDF.

Nao implementado ou nao exposto como fluxo principal:

- selecao livre de pasta de saida por usuario;
- upload/edicao dinamica de templates;
- insercao automatica de fotos reais;
- exportacao PDF como opcao visivel principal;
- autenticacao OAuth para SharePoint/OneDrive privado.

## Vocabulário do projeto

- **Ficha**: slide individual de curriculo/perfil de um colaborador.
- **Carometro**: deck ou slide com varios colaboradores em formato visual de cards.
- **Base padrao**: planilha `.xlsx` configurada na tela de Configuracoes.
- **Cache da base**: copia validada da base em `%APPDATA%\USIGenerator\cache`.
- **Preset de carometro**: metadados de um template PPTX, incluindo capacidade, slots, campos obrigatorios e titulo.
- **Slot**: conjunto de shapes em um template de carometro onde entram foto/placeholder e texto de um colaborador.
- **Source result**: metadados de resolucao da origem da planilha.

## Principais arquivos e responsabilidades

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Bootstrap do QApplication e AppWindow |
| `app/config/settings.py` | Config persistida, caminhos e defaults |
| `app/config/theme.py` | Paletas e stylesheet QSS |
| `app/core/reader.py` | Planilhas, schemas, remapeamento, busca, OneDrive/cache |
| `app/core/base_cache.py` | Base padrao local e cache validado |
| `app/core/generator_ficha.py` | Ficha PPTX individual |
| `app/core/generator_carom.py` | Carometro PPTX por template |
| `app/core/carom_templates.py` | Presets, templates, slots e validacoes por modelo |
| `app/core/pptx_template_utils.py` | Manipulacao baixa de slides/shapes/imagens |
| `app/core/pdf_exporter.py` | Conversao PPTX para PDF |
| `app/core/resource_paths.py` | Resolucao de recursos em dev/build |
| `app/core/worker.py` | QThreads de validacao, busca e geracao |
| `app/ui/app_window.py` | Janela principal e orquestracao |
| `app/ui/components.py` | Componentes visuais compartilhados |
| `app/ui/screen_home.py` | Dashboard inicial |
| `app/ui/screen_ficha.py` | Fluxo de ficha |
| `app/ui/screen_carom.py` | Fluxo de carometro |
| `app/ui/screen_progress.py` | Progresso/log |
| `app/ui/screen_settings.py` | Configuracoes/base/cache |
| `scripts/check_architecture.py` | Regras de arquitetura |
| `scripts/delivery_check.bat` | Check completo de entrega |
| `usi_generator.spec` | Build PyInstaller |

## Recomendacoes para futuros agentes

Ao modificar este projeto:

1. Leia primeiro `app/core/reader.py`, `app/core/worker.py` e a tela envolvida.
2. Preserve a separacao `config/core/ui`.
3. Nao mude templates PPTX sem atualizar `carom_templates.py`.
4. Para novos campos de planilha, atualizar:
   - aliases em `reader.py`;
   - typed dicts;
   - schema/remapeamento;
   - validacoes;
   - testes.
5. Para novas opcoes de carometro, atualizar:
   - `CaromTemplate`;
   - tela `screen_carom.py`;
   - gerador;
   - testes unitarios e integracao.
6. Para comportamento de UI, criar/ajustar testes com `QT_QPA_PLATFORM=offscreen`.
7. Antes de considerar uma mudanca pronta, rodar `scripts\delivery_check.bat` quando possivel.
