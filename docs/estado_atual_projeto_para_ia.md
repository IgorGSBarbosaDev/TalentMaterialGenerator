# Contexto Atual do Projeto TalentMaterialGenerator / USI Generator

O projeto atualmente é um aplicativo desktop em Python com PySide6 voltado para geração de materiais em PowerPoint a partir de uma planilha Excel de colaboradores. O estado atual do repositório já não é mais a versão antiga em CustomTkinter: a base foi reconstruída para uma arquitetura nova em PySide6, com múltiplas telas, execução assíncrona em background e suporte a fonte de dados local ou remota via OneDrive com cache local.

## Objetivo funcional atual

O software hoje tem dois fluxos principais:

1. Geração de ficha individual
   - Gera slides de ficha de colaborador em `.pptx`.
   - Pode gerar:
     - um arquivo por colaborador;
     - ou um único deck com várias fichas.

2. Geração de carômetro
   - Gera slides com cards de colaboradores agrupados por critério.
   - Suporta múltiplas páginas quando um grupo excede a capacidade do layout.

O app também mantém configurações persistidas, histórico recente de gerações, tema claro/escuro e um mecanismo de atualização de base via OneDrive com cache local.

## Stack e arquitetura

### Stack principal

- Python
- PySide6 para UI desktop
- `python-pptx` para geração de PowerPoint
- `openpyxl` para leitura de planilhas Excel
- `requests` para download da planilha via link remoto/OneDrive

### Ponto de entrada

O app inicia em [main.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/main.py).

Fluxo de bootstrap:

1. carrega configurações persistidas;
2. cria `QApplication`;
3. aplica stylesheet QSS com base no tema salvo;
4. instancia a janela principal.

### Estrutura geral

A divisão principal está assim:

- [app/config](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/config)
  - configurações persistidas e tema/QSS
- [app/core](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core)
  - leitura da planilha, cache OneDrive, geração de PPTX, worker em background
- [app/ui](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui)
  - janela principal, telas e componentes visuais reutilizáveis
- [tests](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/tests)
  - testes unitários e de integração

## Funcionamento atual da configuração e persistência

O módulo principal de configuração está em [settings.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/config/settings.py).

### Onde a configuração é salva

A configuração é persistida em `%APPDATA%\USIGenerator\config.json`.

### Principais chaves de configuração

O sistema hoje trabalha com dados como:

- tema (`light` ou `dark`)
- tipo de fonte padrão da planilha
- caminho padrão de planilha local
- URL padrão do OneDrive
- diretório de saída padrão
- modo padrão de geração da ficha
- agrupamento padrão do carômetro
- quantidade padrão de colunas do carômetro
- TTL do cache
- estratégia de refresh
- data da última sincronização do cache
- histórico das últimas gerações

### Observação importante

Apesar de existir chave de configuração para diretório de saída, o comportamento atual força o uso de um diretório padrão calculado por código, que é algo como:

`~/Documents/Usi Generator`

Ou seja: hoje o app não trata o diretório de saída como algo totalmente livre/configurável na prática. Ele exibe esse caminho como diretório padrão e o usa como base para as saídas.

## Tema e aparência

A parte visual é controlada por [theme.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/config/theme.py).

### Como funciona

- O projeto usa QSS para estilização.
- Existem dois temas principais: claro e escuro.
- O stylesheet define visual de:
  - sidebar
  - topbar
  - cards
  - badges de status
  - botões
  - inputs
  - progress bar
  - lista de histórico
  - telas em geral

A UI não depende mais de CustomTkinter.

## Fonte de dados: planilha local + OneDrive com cache

O módulo responsável por isso é [reader.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core/reader.py).

### Fontes suportadas

Hoje o sistema suporta dois modos de entrada:

1. arquivo local `.xlsx`
2. link remoto do OneDrive

### Estratégia de OneDrive

O fluxo remoto funciona assim:

1. o usuário informa uma URL;
2. o sistema tenta transformá-la em link de download direto;
3. baixa a planilha com `requests`;
4. salva uma cópia em cache local;
5. usa TTL para decidir se o cache ainda está válido;
6. se o download remoto falhar, mas houver cache local, usa o cache com aviso.

### Cache local

O cache fica em `%APPDATA%\USIGenerator\cache`.

### Política atual

- existe suporte a TTL configurável;
- existe atualização manual;
- existe fallback para o último cache válido caso a rede falhe.

### Resultado da resolução da fonte

O sistema encapsula isso em um objeto com informações como:

- caminho final da planilha usada;
- se a origem foi local ou remota;
- se foi usado cache;
- caminho do cache;
- mensagem de status;
- timestamp do download.

## Leitura e normalização da planilha

Ainda em [reader.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core/reader.py), o sistema:

- lê a planilha Excel com `openpyxl`;
- detecta cabeçalhos e colunas;
- valida colunas obrigatórias;
- remapeia os dados para uma estrutura normalizada usada pelos geradores.

### Campos relevantes no estado atual

A modelagem atual já considera, entre outros:

- `matricula`
- `nome`
- `idade`
- `cargo`
- `antiguidade`
- `formacao`
- `resumo_perfil`
- `trajetoria`
- `performance`
- `area`
- `nota`
- `potencial`
- `nota_2025`
- `nota_2024`
- `nota_2023`
- `avaliacao_2025`
- `avaliacao_2024`
- `avaliacao_2023`
- `score_2025`
- `score_2024`
- `score_2023`
- `potencial_2025`
- `potencial_2024`
- `potencial_2023`

### Regra adicional importante

O módulo consegue montar o campo `performance` automaticamente a partir dos campos anuais exibidos na ficha (`nota_2025`, `nota_2024`, `nota_2023`), quando esses valores existem.

Isso significa que a ficha hoje pode usar:

- performance diretamente mapeada da planilha;
- ou performance derivada das notas anuais, seja por colunas consolidadas `Avaliação <ano>` ou por `Nota <ano>` + `Potencial <ano>`.

## Geração de ficha

O gerador de ficha está em [generator_ficha.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core/generator_ficha.py).

### Tecnologia

Usa `python-pptx`.

### Tamanho do slide

O slide da ficha usa proporção widescreen com dimensões fixas:

- `13.271 x 7.5`

### Estrutura visual da ficha

A ficha monta elementos como:

- título
- dados básicos do colaborador
- resumo de perfil
- formação
- trajetória
- performance

### Regra de imagem

O projeto não usa mais foto real nem avatar carregado de pasta.

No estado atual, a ficha usa um placeholder circular branco com borda verde. Isso substitui totalmente o conceito antigo de foto/avatar.

### Tratamento de trajetória

O campo `trajetoria` é tratado como conteúdo multi-linha.
O código suporta separação por:

- `;`
- quebra de linha

Além disso, quando uma linha tem o padrão `"data - descrição"`, a parte antes do `" - "` recebe destaque visual em negrito.

### Modos de saída da ficha

Hoje existem dois modos:

- `one_file_per_employee`
- `single_deck`

### Diretório de saída

A ficha gera arquivos dentro de uma subpasta:

- `fichas`

Essa pasta fica dentro do diretório base de saída do app.

### Retorno e logs

O gerador aceita callback de progresso/log para alimentar a tela de progresso.

## Geração de carômetro

O gerador de carômetro está em [generator_carom.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core/generator_carom.py).

### Tecnologia

Também usa `python-pptx`.

### Estrutura geral

O carômetro gera cards de colaboradores distribuídos em grade, com possibilidade de agrupamento e paginação automática.

### Configuração de layout

A configuração atual inclui:

- quantidade de colunas
- campo de agrupamento
- título
- exibir ou não nota
- exibir ou não potencial
- exibir ou não cargo
- aplicar ou não cores automáticas

### Placeholder visual

Assim como na ficha, o carômetro não usa foto real.
Cada card usa um placeholder circular branco com borda verde.

### Agrupamento

Os colaboradores podem ser agrupados por um campo configurado, como por exemplo área.
Cada grupo vira uma ou mais páginas.

### Ordenação

Dentro de cada grupo, o sistema ordena os colaboradores por nota, em ordem decrescente.

### Cores automáticas

Existe lógica de cor baseada em:

- nota
- potencial

As faixas de nota usam cortes como 4.0 e 3.0, e o potencial é tratado em níveis como alto/médio/baixo.

### Paginação

Se um grupo tiver mais colaboradores do que a grade suporta em um slide, o sistema cria slides adicionais para esse mesmo grupo.

### Diretório de saída

O carômetro gera dentro da subpasta:

- `carometros`

## Exportação para PDF

O módulo existe em [pdf_exporter.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core/pdf_exporter.py).

### Estado atual

Ele continua presente, mas não é o foco principal do produto atual.

### Estratégia

Tenta converter PPTX para PDF por:

1. LibreOffice em modo headless;
2. fallback via COM/`comtypes` no Windows.

### Importante

Apesar de o módulo existir, o fluxo principal do app hoje está centrado na geração de `.pptx`. O PDF está preservado como utilitário, mas não como parte prioritária da UX atual.

## Execução assíncrona e pipeline de geração

O controle de execução em background está em [worker.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/core/worker.py).

### Como funciona

O app usa `QThread` para evitar travar a interface.

### Sinais emitidos

O worker emite sinais como:

- progresso
- log
- conclusão
- erro

### Pipeline do worker

Quando uma geração começa, o worker:

1. resolve a fonte da planilha;
2. lê a planilha;
3. remapeia as linhas conforme o mapeamento definido na tela;
4. registra quantidade de registros encontrados;
5. executa o gerador correspondente:
   - ficha
   - ou carômetro
6. devolve um resultado estruturado com:
   - arquivos gerados
   - diretório de saída
   - quantidade processada
   - tempo gasto
   - metadados da fonte usada
7. faz limpeza de temporários quando necessário.

## Janela principal e navegação

A janela principal está em [app_window.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/app_window.py).

### Estrutura

A aplicação hoje é uma `QMainWindow` com:

- sidebar lateral
- topbar
- `QStackedWidget` para troca de telas

### Telas registradas

O app atualmente tem cinco telas:

1. Home
2. Ficha
3. Carômetro
4. Progresso
5. Configurações

### Recursos atuais da janela principal

- navegação entre telas
- botão de alternância de tema
- controle de estado ocupado/livre
- inicialização do worker
- atualização da tela de progresso
- gravação de histórico de operações
- abertura da pasta de saída
- refresh manual da base remota a partir da URL padrão do OneDrive

### Estado de sessão

A janela principal também mantém:

- estatísticas em memória do número de fichas e carômetros gerados;
- histórico recente carregado da configuração persistida.

## Componentes visuais reutilizáveis

A UI usa componentes compartilhados em [components.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/components.py).

Esse arquivo concentra peças reutilizáveis como:

- botão de navegação da sidebar
- cards de métrica
- cards de seção
- badge de status
- helpers de repolish/refresh visual

Ou seja, a UI não é só um conjunto de telas soltas; existe uma camada de componentes base para manter consistência visual.

## Tela Home

A home está em [screen_home.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/screen_home.py).

### O que mostra

- área principal com apresentação/atalhos
- cartões de ação para entrar em ficha e carômetro
- métricas resumidas
- histórico recente de operações

### O que emite

A tela dispara sinais para:

- abrir fluxo de ficha
- abrir fluxo de carômetro
- abrir configurações

### Papel dela

É a tela inicial do app e funciona como dashboard resumido.

## Tela de Ficha

A tela está em [screen_ficha.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/screen_ficha.py).

### O que o usuário configura

- fonte da planilha:
  - local
  - OneDrive
- caminho do arquivo local ou URL remota
- mapeamento de colunas
- modo de saída

### Mapeamentos disponíveis atualmente

A tela permite mapear campos como:

- matrícula
- nome
- idade
- cargo
- antiguidade
- formação
- resumo de perfil
- trajetória
- nota_2025
- nota_2024
- nota_2023
- avaliacao_2025
- avaliacao_2024
- avaliacao_2023
- score_2025
- score_2024
- score_2023
- potencial_2025
- potencial_2024
- potencial_2023
- performance

### Validação atual

A validação mínima da tela considera principalmente:

- `nome`
- `cargo`

### Saída

Ao iniciar a geração, a tela envia para o worker:

- origem da planilha
- tipo de fonte
- diretório de saída
- mapeamento de colunas
- modo de geração

### Observação importante

O diretório de saída é exibido, mas no estado atual ele está vinculado ao diretório padrão calculado pelo app, não a um seletor livre de pasta.

## Tela de Carômetro

A tela está em [screen_carom.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/screen_carom.py).

### O que o usuário configura

- fonte local ou OneDrive
- mapeamento de colunas
- agrupamento
- número de colunas da grade
- título
- opções visuais

### Mapeamentos disponíveis

A tela trabalha com campos como:

- matrícula
- nome
- cargo
- área
- nota
- potencial
- nota_2025
- nota_2024
- nota_2023

### Opções visuais

A tela permite escolher:

- mostrar ou não nota
- mostrar ou não potencial
- mostrar ou não cargo
- ativar ou não cores automáticas

### Saída

Ao gerar, envia ao worker um config com o necessário para montar os slides de carômetro.

## Tela de Progresso

A tela está em [screen_progress.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/screen_progress.py).

### Função

É a tela que acompanha uma geração em andamento.

### O que mostra

- barra de progresso
- percentual
- contagem de processados
- status
- tempo decorrido
- log textual com mensagens coloridas por nível

### Estados

Ela suporta:

- reset
- atualização incremental de progresso
- estado de sucesso
- estado de erro

### Ações disponíveis

Ao final do processo, a tela permite:

- abrir a pasta de saída
- iniciar nova geração

## Tela de Configurações

A tela está em [screen_settings.py](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/app/ui/screen_settings.py).

### O que permite configurar

- planilha local padrão
- URL padrão do OneDrive
- TTL do cache
- reset para defaults
- atualização manual da base remota

### Observação

Assim como nas demais telas, o diretório de saída exibido hoje é o diretório padrão calculado internamente, e não um caminho totalmente livre definido pelo usuário em runtime.

## Fluxo completo de uso no estado atual

### Fluxo da ficha

1. usuário abre a tela de ficha;
2. escolhe planilha local ou OneDrive;
3. informa caminho/URL;
4. carrega os cabeçalhos para mapear colunas;
5. define modo de saída;
6. clica para gerar;
7. o worker resolve a fonte, lê a planilha, remapeia dados e gera os PPTX;
8. a tela de progresso acompanha tudo;
9. ao final, o usuário pode abrir a pasta de saída.

### Fluxo do carômetro

1. usuário abre a tela de carômetro;
2. escolhe planilha local ou OneDrive;
3. informa caminho/URL;
4. mapeia colunas;
5. define agrupamento, colunas e opções visuais;
6. inicia a geração;
7. o worker monta os slides agrupados/paginados;
8. a tela de progresso mostra logs e finalização.

### Fluxo de OneDrive com cache

1. o app tenta baixar a planilha remota;
2. se conseguir, salva em cache e usa a versão nova;
3. se falhar, tenta usar a última cópia em cache;
4. a UI pode mostrar status/mensagem sobre uso de cache.

## Testes e cobertura

Existe uma suíte de testes relativamente ampla em [tests](/C:/Users/Igor/Documents/VSCode/TalentMaterialGenerator/tests), cobrindo:

- config
- core
- UI
- integração

Os testes incluem:

- leitura da planilha
- geração de ficha
- geração de carômetro
- exportador PDF
- telas PySide6
- fluxos integrados de geração

### Limite importante de contexto

No ambiente em que a revisão foi feita, o `pytest` não estava instalado, então o estado funcional foi entendido pela leitura do código e da estrutura dos testes, não por execução total da suíte nesse momento.

## Estado atual real do produto

### O que já está implementado

- migração da interface para PySide6
- arquitetura multitela
- tema claro/escuro
- fluxo de ficha
- fluxo de carômetro
- leitura de planilha local
- download via OneDrive
- cache local com TTL
- execução em background com `QThread`
- tela de progresso
- histórico básico
- persistência de configurações
- geração PPTX sem dependência de fotos reais

### O que foi removido do conceito antigo

- CustomTkinter
- uso de foto real/pasta de fotos como parte central do fluxo
- lógica antiga baseada em avatar/imagem real

### Como a imagem funciona agora

Tanto ficha quanto carômetro usam placeholder circular branco com borda verde, em vez de foto do colaborador.

## Limitações e observações importantes para outro modelo

1. O repositório atual representa um MVP reconstruído, não necessariamente uma versão final polida.
2. A UI já é PySide6 e não deve mais ser tratada como projeto em CustomTkinter.
3. O projeto já possui suporte real a OneDrive com cache local, não é apenas ideia.
4. O campo `foto` não faz mais parte do fluxo principal.
5. A geração principal é em `.pptx`; PDF existe, mas não é a prioridade do produto hoje.
6. O diretório de saída, no estado atual, está mais fixado por padrão do que realmente livre/configurável.
7. O modelo de dados atual já aceita campos adicionais como `matricula`, notas anuais exibidas (`nota_2025`, `nota_2024`, `nota_2023`) e os campos estruturados/consolidados de avaliação por ano, inclusive para compor performance.
8. O projeto já possui estrutura de testes para a nova arquitetura.
9. Existe uma camada de componentes visuais compartilhados em `app/ui/components.py`, então mudanças de UI devem considerar essa base comum.
10. A descrição correta do projeto deve sempre ser baseada no estado atual do código, e não no plano antigo da versão anterior.
