# USI Generator — Contexto Completo do Projeto
> Documento de referência para desenvolvimento — versão 2.0  
> Área: Talent Development · Usiminas · Atualizado: Março 2025

---

## 1. Contexto e Origem do Projeto

A equipe de **Talent Development da Usiminas** enfrenta um problema recorrente: a produção manual de materiais de RH consome horas de trabalho operacional que poderiam ser dedicadas a atividades estratégicas.

Os dois materiais mais custosos de produzir são:

1. **Fichas de Currículo** — slides individuais por colaborador contendo foto, dados pessoais, resumo de perfil, formação, trajetória profissional e histórico de performance
2. **Carômetros** — slides com grid visual de colaboradores mostrando nome, cargo, nota e potencial, organizados por área ou gerência

Hoje o processo é 100% manual: coletar dados em diferentes fontes, abrir o PowerPoint, montar cada slide individualmente, exportar para PDF. Para uma equipe de 50 colaboradores, isso representa horas de trabalho repetitivo.

**A solução:** um aplicativo desktop chamado **USI Generator**, que automatiza toda essa geração a partir de uma planilha Excel (local ou via link do OneDrive) e produz os arquivos finais prontos para uso.

---

## 2. Objetivo do App

- Gerar **Fichas de Currículo** em lote (`.pptx` + `.pdf`) seguindo o template oficial da Usiminas
- Gerar **Carômetros** em lote (`.pptx` + `.pdf`) com layout de grid configurável
- Aceitar planilha **local** (`.xlsx`) ou via **link do OneDrive** (download automático)
- Gerar slides com **placeholder circular** no lugar da foto (sem dependência de imagens externas)
- Rodar **localmente no Windows**, sem necessidade permanente de internet
- Ser distribuído como um **arquivo `.exe` portátil** que qualquer colaborador usa sem instalar Python

---

## 3. Decisões Técnicas Importantes

### 3.1 Fonte de Dados: Planilha Local ou OneDrive

O app suporta dois modos de entrada de planilha:

**Modo A — Arquivo local:**
- Usuário clica em "Procurar" e seleciona o `.xlsx` no computador
- Fluxo padrão, sem necessidade de internet

**Modo B — Link do OneDrive:**
- Usuário cola o link de compartilhamento do OneDrive no campo de texto
- O app detecta automaticamente se é um link (começa com `https://`) ou um caminho local
- Realiza o download do arquivo para um diretório temporário
- Processa normalmente e deleta o arquivo temporário ao finalizar

```python
# Lógica de detecção e download
import requests, tempfile, os

def carregar_planilha(entrada: str) -> str:
    if entrada.startswith("https://"):
        # É um link do OneDrive — fazer download
        url = converter_link_onedrive(entrada)
        resp = requests.get(url)
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    else:
        # É um caminho local
        return entrada

def converter_link_onedrive(share_url: str) -> str:
    # Converte link de compartilhamento em link de download direto
    return share_url.replace("?e=", "?download=1&e=")
```

**Requisito de rede para OneDrive:**
- O link deve ter permissão "Pessoas da organização com o link" (gerado pelo SharePoint/Teams)
- A máquina deve estar conectada à rede corporativa ou VPN ao clicar em "Gerar"
- Não é necessário estar conectado continuamente — apenas no momento do download da planilha

**Tratamento de erros de rede:**
- Link inválido → mensagem de erro no campo antes de iniciar a geração
- Falha no download → mensagem clara: "Não foi possível acessar o link. Verifique a conexão com a rede da organização."
- Timeout → tentativa única com timeout de 15 segundos

---

### 3.2 Fotos dos Colaboradores: Placeholder Circular

A equipe **não possui uma base local de fotos**. As imagens dos colaboradores existem em links acessíveis apenas dentro da rede corporativa, o que torna a busca automática instável e arriscada.

**Decisão de projeto:** o app gera um **placeholder circular em branco** no lugar de cada foto. O usuário abre o PPTX gerado no PowerPoint e insere/cola a imagem manualmente dentro do círculo.

Isso garante:
- Zero dependência de fotos no processo automatizado
- Geração 100% offline (exceto download da planilha se vier do OneDrive)
- Nenhum slide travado por foto não encontrada
- Fluxo simples e previsível para toda a equipe

**Implementação do placeholder com `python-pptx`:**

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE

def adicionar_placeholder_foto(slide, left, top, width, height):
    """Adiciona círculo branco com borda verde — usuário cola a foto depois."""
    oval = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.OVAL
        left=Inches(left),
        top=Inches(top),
        width=Inches(width),
        height=Inches(height)
    )
    oval.fill.solid()
    oval.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # branco
    oval.line.color.rgb = RGBColor(0x84, 0xBD, 0x00)       # borda verde #84BD00
    oval.line.width = Pt(2)
    return oval
```

**No template da ficha** (posição exata do círculo):
- `left=0.385"`, `top=1.000"`, `width=1.382"`, `height=1.344"`

**No carômetro**, cada card terá um círculo proporcional ao tamanho do card, centralizado.

> **Instrução ao usuário** (exibida no log ao finalizar):  
> "Os slides foram gerados com marcadores circulares para as fotos. Abra cada arquivo no PowerPoint, clique no círculo e insira a foto do colaborador."

---

### 3.3 Framework de Interface: PySide6

O framework de UI escolhido é **PySide6** (não CustomTkinter).

**Motivo:** PySide6 usa **QSS (Qt Style Sheets)**, que funciona como CSS — permite replicar com precisão o visual definido no mockup (sidebar escura, cards, toggles, barra de progresso animada, log monoespaçado, tema claro/escuro em tempo real). O CustomTkinter teria limitações visuais para atingir o mesmo resultado.

```python
# Exemplo de QSS — sidebar com item ativo em verde
SIDEBAR_STYLE = """
    QWidget#sidebar {
        background-color: #111111;
        border-right: 1px solid #222222;
    }
    QPushButton#menu_item {
        background: transparent;
        color: #999999;
        text-align: left;
        padding: 9px 16px;
        border: none;
        font-size: 13px;
    }
    QPushButton#menu_item:checked {
        background-color: #1e2a14;
        color: #84BD00;
        border-right: 2px solid #84BD00;
    }
    QPushButton#menu_item:hover {
        background-color: #1a1a1a;
        color: #cccccc;
    }
"""
```

---

## 4. Template Oficial da Ficha de Currículo

> ⚠️ Padrão obrigatório. O app deve replicar este layout com precisão pixel a pixel.  
> Arquivo de referência: `Ficha_Luana_Cristina.pptx`

### Dimensões do slide

| Dimensão | Valor |
|---|---|
| Largura | **13.271 inches** (formato WIDE — não é o padrão 10") |
| Altura | **7.500 inches** |
| Proporção | 16:9 estendido |

> ⚠️ Atenção: ao criar a apresentação com `python-pptx`, definir explicitamente:  
> `prs.slide_width = Inches(13.271)` e `prs.slide_height = Inches(7.5)`

### Estrutura visual

```
┌──────────────────────────────────────────────────────────────────────┐
│  NOME COMPLETO EM VERDE (#92D050)  ·  bold  ·  grande    [caixa ▮]  │
├───────────────────────────────────┬──────────────────────────────────┤
│  [○]   Nome Completo (Idade)      │  RESUMO PERFIL                   │
│        Cargo                      │  Texto corrido justificado,      │
│        Antiguidade: X anos        │  fonte 12pt, preto               │
│                                   │                                  │
│  FORMAÇÃO                         │  PERFORMANCE:                    │
│  Curso – Instituição              │  2023: 5PROM                     │
│                                   │  2024: 4AP                       │
│  TRAJETÓRIA                       │                                  │
│  USIMINAS                         │                                  │
│  2024-2025 - Coordenador Produção │                                  │
│  2022-2024 - Supervisor Produção  │                                  │
│  2018-2022 - Técnico Produção     │                                  │
│  ...                              │                                  │
└───────────────────────────────────┴──────────────────────────────────┘
│ ████████████ barra rodapé verde ████  │
```

### Posições exatas de cada elemento (em inches)

| Elemento | left | top | width | height | Estilo |
|---|---|---|---|---|---|
| Título (nome completo) | 0.397 | 0.251 | 11.833 | 0.477 | `#92D050`, bold, grande |
| Caixa verde (canto direito) | 12.358 | 0.364 | 0.778 | 0.477 | Fill sólido `#92D050` |
| Retângulo cinza grande (fundo corpo) | 0.149 | 2.427 | 11.214 | 4.921 | Fill cinza claro |
| Retângulo cinza menor (área foto+info) | 1.908 | 0.922 | 10.966 | 6.417 | Fill cinza claro |
| Retângulo acento esquerdo | 2.309 | 0.980 | 0.202 | 1.279 | Fill escuro |
| **Placeholder circular (foto)** | **0.385** | **1.000** | **1.382** | **1.344** | **Branco, borda #84BD00, 2pt** |
| Nome + Cargo + Antiguidade | 1.922 | 1.009 | 3.740 | 0.791 | Nome 15pt bold, cargo 12pt |
| Label "FORMAÇÃO" | 0.240 | 3.075 | 4.400 | 0.337 | `#92D050`, 14pt bold |
| Texto formação | 0.240 | 3.361 | 4.739 | 0.303 | Preto, 12pt |
| Label "TRAJETÓRIA" | 0.332 | 4.186 | 1.455 | 0.337 | `#92D050`, 14pt bold |
| Texto trajetória (USIMINAS + cargos) | 0.326 | 4.640 | 5.411 | 2.128 | `#666666`, 10.95pt |
| Linha divisória vertical | 5.719 | 1.009 | 0.000 | 6.220 | Linha fina |
| Label "RESUMO PERFIL" | 5.737 | 1.022 | 1.817 | 0.337 | `#92D050`, 14pt bold |
| Texto resumo perfil | 5.737 | 1.423 | 6.898 | 1.745 | Preto, 12pt, justificado |
| Label "PERFORMANCE:" | 5.775 | 3.341 | 1.860 | 0.337 | `#92D050`, 14pt bold |
| Texto performance | 5.867 | 3.694 | 1.835 | 0.505 | Preto, 12pt |
| Barra rodapé | 0.000 | 7.118 | 4.797 | 0.388 | Fill sólido verde |

### Cores exatas do template

| Elemento | HEX |
|---|---|
| Título (nome no topo) | `#92D050` |
| Labels de seção (FORMAÇÃO, TRAJETÓRIA, RESUMO PERFIL, PERFORMANCE) | `#92D050` |
| Nome no cartão esquerdo | `#000000` |
| Cargo e textos gerais | `#000000` |
| Texto da trajetória (datas e cargos) | `#666666` |
| Borda do placeholder circular | `#84BD00` |
| Fundo da barra de rodapé | `#84BD00` ou `#92D050` |

### Mapeamento planilha → slide

| Campo na planilha | Onde aparece no slide |
|---|---|
| `nome` | Título verde no topo + "Nome Completo (Idade)" no cartão |
| `idade` | Entre parênteses após o nome no cartão |
| `cargo` | Abaixo do nome no cartão esquerdo |
| `antiguidade` | "Antiguidade: X anos" no cartão esquerdo |
| `formacao` | Seção FORMAÇÃO |
| `resumo_perfil` | Seção RESUMO PERFIL (coluna direita) |
| `trajetoria` | Seção TRAJETÓRIA — lista com "USIMINAS" acima |
| `performance` | Seção PERFORMANCE |
| *(foto)* | **Placeholder circular — não há campo de foto** |

### Formato dos campos de trajetória e performance

**Trajetória** — separar entradas por `;` ou `\n` na célula da planilha:
```
2024-2025 - Coordenador Produção; 2022-2024 - Supervisor Produção; 2018-2022 - Técnico Produção
```
O app renderiza cada entrada em uma linha, com o período em **bold** e o cargo em normal.

**Performance** — separar entradas por `;` ou `\n`:
```
2023: 5PROM; 2024: 4AP
```

---

## 5. Template do Carômetro

Layout de grid com cards por colaborador. Cada grupo (área/gerência) gera 1 slide.

### Estrutura do slide

```
┌──────────────────────────────────────────────────────────────┐
│  Cabeçalho: fundo verde escuro · texto branco · título       │
├──────────────────────────────────────────────────────────────┤
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐     │
│  │  [○]  │  │  [○]  │  │  [○]  │  │  [○]  │  │  [○]  │     │
│  │ Nome  │  │ Nome  │  │ Nome  │  │ Nome  │  │ Nome  │     │
│  │ Cargo │  │ Cargo │  │ Cargo │  │ Cargo │  │ Cargo │     │
│  │  4.5  │  │  4.8  │  │  3.9  │  │  4.3  │  │  3.2  │     │
│  │[Alto] │  │[Alto] │  │[Méd.] │  │[Alto] │  │[Baixo]│     │
│  └───────┘  └───────┘  └───────┘  └───────┘  └───────┘     │
└──────────────────────────────────────────────────────────────┘
```

O `[○]` de cada card é também um **placeholder circular branco** (mesma lógica da ficha).

### Regras de cor por potencial

| Valor | Cor do badge |
|---|---|
| Alto | `#84BD00` (verde) |
| Médio | `#F59E0B` (âmbar) |
| Baixo | `#EF4444` (vermelho) |

### Regras de cor por nota numérica

| Faixa | Cor |
|---|---|
| ≥ 4.0 | `#84BD00` (verde) |
| 3.0 – 3.9 | `#F59E0B` (âmbar) |
| < 3.0 | `#EF4444` (vermelho) |

### Configurações disponíveis

- Colunas por linha: 3, 4 ou 5 (padrão: 5)
- Agrupamento: por área / por gerência / por nível / sem agrupamento
- Campos visíveis: nota (on/off), potencial (on/off), cargo (on/off)
- Título do slide: campo de texto livre personalizável
- Cabeçalho: fundo verde escuro (`#2D4200`) com texto branco bold

---

## 6. Features Completas do App

### 6.1 Tela Home

- Logo Usiminas (símbolo U verde + "USIMINAS" + "MINERAÇÃO") no topo da sidebar
- Nome do app: "USI Generator" com subtítulo "Talent Development"
- Dois cards grandes clicáveis: **Ficha de Currículo** e **Carômetro**
- Três cards de estatísticas: fichas geradas no mês / carômetros gerados / estimativa de tempo economizado
- Lista de histórico das últimas gerações: nome do arquivo, tipo, data/hora

---

### 6.2 Ficha de Currículo — Tela de Configuração

**Painel esquerdo — configurações:**

**Etapa 1 — Fonte de dados:**
- Campo de entrada com dois modos (detectado automaticamente):
  - Botão "Procurar arquivo" → abre file dialog para `.xlsx` local
  - Campo de texto + botão "Carregar link" → aceita URL do OneDrive
- Indicador de status ao lado do campo:
  - Ícone verde: arquivo/link válido e acessível
  - Ícone vermelho: arquivo não encontrado / link inacessível
  - Ícone amarelo: carregando (durante download do OneDrive)
- Campo: pasta de saída com botão "Procurar"

**Etapa 2 — Mapeamento de colunas:**
- Após carregar a planilha, exibe dropdowns com os cabeçalhos reais detectados
- Campos a mapear: Nome, Idade, Cargo, Antiguidade, Formação, Resumo de Perfil, Trajetória, Performance
- Botão "Auto-detectar" tenta mapear automaticamente por heurística de nomes
- Campos obrigatórios marcados com `*` (nome e cargo)

**Etapa 3 — Opções:**
- Toggle: Gerar PDF além do PPTX
- Toggle: Modo de saída — 1 arquivo por colaborador / todos em 1 arquivo

**Painel direito — preview e lista:**
- Preview thumbnail do slide que será gerado (atualizado conforme configurações mudam)
- Contador: "X colaboradores encontrados"
- Lista scrollável com os nomes detectados na planilha
- Botão primário: **GERAR FICHAS**

---

### 6.3 Carômetro — Tela de Configuração

**Painel esquerdo — configurações:**

**Etapa 1 — Fonte de dados:**
- Mesma lógica da ficha: arquivo local ou link OneDrive

**Etapa 2 — Mapeamento de colunas:**
- Campos: Nome, Cargo, Área/Grupo, Nota, Potencial

**Etapa 3 — Layout:**
- Seletor de colunas por linha: `3` / `4` / `5` (botões segmentados)
- Dropdown: Agrupar por área / por gerência / por nível / sem agrupamento
- Toggles: Mostrar nota / Mostrar potencial / Mostrar cargo / Código de cores automático
- Campo de texto: Título do slide (ex: "Carômetro — Diretoria Comercial")
- Toggle: Gerar PDF

**Painel direito:**
- Preview do grid de cards
- Contador: "X colaboradores · Y slides estimados"
- Lista dos colaboradores detectados
- Botão primário: **GERAR CARÔMETRO**

---

### 6.4 Tela de Progresso

Exibida ao clicar em Gerar (qualquer modo).

- Título: "Gerando fichas de currículo..." / "Gerando carômetro..."
- Subtítulo: "X colaboradores · PPTX + PDF"
- Barra de progresso animada (verde `#84BD00`)
- Contador: "X de Y concluídos · Z%"
- Caixa de log em tempo real (fonte monoespaçada `Consolas 11pt`):
  ```
  ✓ Lendo planilha colaboradores_2025.xlsx...
  ✓ 12 colaboradores encontrados
  ✓ Gerando ficha: Luana Cristina Gonçalves Almeida
  ✓ Gerando ficha: Carlos Ferreira
  ✓ Exportando PDFs...
  ✅ Concluído! 12 fichas geradas em 00:09
  ℹ  Abra os arquivos .pptx e insira as fotos nos círculos brancos.
  ```
- Botão: **Abrir pasta de saída** → `os.startfile(pasta_saida)`
- Botão: **Nova geração** → volta para a tela de configuração anterior

---

### 6.5 Tela de Configurações

- **Tema da interface:** toggle Claro / Escuro — aplicado imediatamente, sem reiniciar
- Caminho padrão para planilhas
- Caminho padrão para pasta de saída
- Formato padrão de saída: PPTX / PDF / Ambos
- Número padrão de colunas do carômetro
- Botão: Redefinir para padrões

---

### 6.6 Modo Claro e Escuro

- Toggle disponível na sidebar (ícone de sol/lua) e na tela de Configurações
- Troca aplicada **em tempo real** sem reiniciar o app (via `QApplication.setStyleSheet()`)
- Preferência salva em `config.json` e restaurada ao abrir

**Modo Escuro:**
```
Fundo principal:   #141414
Superfície:        #1a1a1a
Superfície 2:      #222222
Borda:             #2a2a2a
Texto primário:    #eeeeee
Texto secundário:  #888888
```

**Modo Claro:**
```
Fundo principal:   #f0f0f0
Superfície:        #ffffff
Superfície 2:      #f5f5f5
Borda:             #dddddd
Texto primário:    #1a1a1a
Texto secundário:  #666666
```

**Invariantes (ambos os modos):**
```
Verde Usiminas:    #84BD00  (botões, badges, destaques, borda do placeholder)
Verde slide:       #92D050  (usado apenas no PPTX gerado, não na UI)
Âmbar:             #F59E0B  (potencial médio, avisos)
Vermelho:          #EF4444  (potencial baixo, erros)
```

---

## 7. Stack Tecnológica

### Linguagem
- **Python 3.11+**

### Interface Gráfica
- **PySide6 ≥ 6.6.0**
  - Qt Style Sheets (QSS) para estilização completa (equivalente a CSS)
  - `QMainWindow` com `QStackedWidget` para troca de telas
  - `QThread` + `pyqtSignal` para geração em background sem travar a UI
  - `QProgressBar`, `QTextEdit` (log), `QFileDialog`, `QComboBox`
  - Troca de tema via `QApplication.setStyleSheet(novo_qss)`

### Geração de PowerPoint
- **python-pptx ≥ 0.6.23**
  - Slides no formato WIDE (13.271" × 7.5")
  - Posicionamento pixel a pixel via `Inches()` e `Emu()`
  - Placeholder circular: `add_shape(OVAL, ...)` com fill branco e borda verde

### Leitura de Planilhas
- **openpyxl ≥ 3.1.2** — leitura de `.xlsx`
- **pandas ≥ 2.0.0** — agrupamento e ordenação para o carômetro

### Download de Planilha via OneDrive
- **requests ≥ 2.31.0** — download HTTP do arquivo `.xlsx` a partir do link compartilhado
- **tempfile** (nativo Python) — armazenamento temporário durante o processamento

### Exportação PDF
- **LibreOffice (headless)** — converte `.pptx` → `.pdf` via `subprocess`
  - Instalação gratuita: libreoffice.org
  - Comando: `soffice --headless --convert-to pdf arquivo.pptx`
- **Fallback:** `comtypes` (automação COM do Windows) se Office estiver instalado

### Empacotamento
- **PyInstaller ≥ 6.0.0** — gera `.exe` portátil

### Persistência
- **json** (nativo Python) — salva `config.json` em `%APPDATA%\USIGenerator\`

---

## 8. Arquitetura do Projeto

```
USI_Generator/
│
├── main.py                        ← ponto de entrada, inicia QApplication
│
├── app/
│   ├── ui/
│   │   ├── app_window.py          ← QMainWindow, sidebar, QStackedWidget
│   │   ├── screen_home.py         ← tela inicial, cards, estatísticas
│   │   ├── screen_ficha.py        ← configuração de fichas, preview
│   │   ├── screen_carom.py        ← configuração de carômetros, preview
│   │   ├── screen_progress.py     ← barra de progresso, log em tempo real
│   │   └── screen_settings.py     ← tema, caminhos padrão, preferências
│   │
│   ├── core/
│   │   ├── reader.py              ← carrega planilha local ou OneDrive
│   │   ├── generator_ficha.py     ← monta slides de ficha com python-pptx
│   │   ├── generator_carom.py     ← monta slides de carômetro com python-pptx
│   │   ├── pdf_exporter.py        ← converte .pptx → .pdf via LibreOffice
│   │   └── worker.py              ← QThread para geração sem travar a UI
│   │
│   └── config/
│       ├── settings.py            ← load/save config.json
│       └── theme.py               ← QSS strings para modo claro e escuro
│
├── assets/
│   ├── logo_usiminas.png
│   └── icon.ico
│
├── requirements.txt
├── build.bat                      ← script para rodar PyInstaller no Windows
└── README.md
```

---

## 9. Paleta de Cores Completa

### Identidade Usiminas
```python
VERDE_USIMINAS   = "#84BD00"   # botões, badges, borda placeholder, destaques UI
VERDE_SLIDE      = "#92D050"   # exclusivo para o PPTX gerado (título da ficha)
VERDE_ESCURO     = "#4A6E00"   # hover states, bordas ativas
VERDE_PROFUNDO   = "#1e3a00"   # fundos de seção em modo escuro
```

### Modo Escuro (padrão ao abrir pela primeira vez)
```python
BG_PRINCIPAL     = "#141414"
BG_SUPERFICIE    = "#1a1a1a"
BG_SUPERFICIE_2  = "#222222"
BG_SIDEBAR       = "#111111"
BORDA            = "#2a2a2a"
BORDA_HOVER      = "#444444"
TEXTO_PRIMARIO   = "#eeeeee"
TEXTO_SECUNDARIO = "#888888"
TEXTO_TERCIARIO  = "#555555"
```

### Modo Claro
```python
BG_PRINCIPAL_L   = "#f0f0f0"
BG_SUPERFICIE_L  = "#ffffff"
BG_SUPERFICIE_2_L= "#f5f5f5"
BG_SIDEBAR_L     = "#e8e8e8"
BORDA_L          = "#dddddd"
BORDA_HOVER_L    = "#bbbbbb"
TEXTO_PRIMARIO_L = "#1a1a1a"
TEXTO_SECUNDARIO_L = "#666666"
TEXTO_TERCIARIO_L  = "#999999"
```

### Semânticas (ambos os modos)
```python
COR_SUCESSO  = "#84BD00"   # log ✓, badge Alto
COR_AVISO    = "#F59E0B"   # log ⚠, badge Médio
COR_ERRO     = "#EF4444"   # log ✗, badge Baixo
```

---

## 10. Design da Interface

### Fonte
- **Segoe UI** — nativa em todo Windows 10/11, sem dependência externa
- `Consolas` — fonte monoespaçada para a caixa de log

### Sidebar (200px de largura fixa)
- Fundo: `#111111` (escuro) / `#e8e8e8` (claro)
- Borda direita: `1px solid #222222`
- Logo: bloco U verde + "USIMINAS" bold + "MINERAÇÃO" verde pequeno
- Itens de menu: ícone SVG + label, padding 9px 16px
- Item ativo: fundo `#1e2a14`, texto `#84BD00`, borda direita `2px #84BD00`
- Rodapé: versão do app + ícone de sol/lua para troca de tema

### Área de conteúdo
- Topbar de 48px com título da tela e badge opcional
- Padding interno: 20px
- Cards: fundo superfície, borda `0.5px`, border-radius `10px`
- Botão primário: fundo `#84BD00`, texto `#111111` bold, largura total, altura 38px

### Componentes PySide6 utilizados

| Widget Qt | Uso no app |
|---|---|
| `QMainWindow` | Janela principal com layout dividido |
| `QStackedWidget` | Troca de telas (home / ficha / carômetro / progresso / settings) |
| `QWidget` + QSS | Sidebar estilizada |
| `QPushButton` | Botões de menu, botões de ação |
| `QLineEdit` | Campos de texto (caminho de arquivo, link OneDrive) |
| `QComboBox` | Dropdowns de mapeamento de colunas |
| `QProgressBar` | Barra de progresso animada |
| `QTextEdit` | Caixa de log em tempo real (somente leitura, fonte mono) |
| `QScrollArea` | Lista scrollável de colaboradores |
| `QFileDialog` | Seletor de arquivo e pasta |
| `QThread` + `Signal` | Geração em background sem travar a UI |
| `QLabel` | Textos, ícones de status |
| `QCheckBox` / `QRadioButton` | Toggles e seletores de opção |

---

## 11. Regras de Negócio

### Geração de Fichas
1. 1 arquivo `.pptx` por colaborador: `Ana_Martins.pptx`
2. 1 arquivo `.pdf` por colaborador se toggle ativado: `Ana_Martins.pdf`
3. Nome do arquivo: sem acentos, espaços → underline (`unicodedata.normalize`)
4. Slide no formato WIDE: `Inches(13.271)` × `Inches(7.5)`
5. Placeholder circular branco com borda `#84BD00` gerado em todas as fichas
6. Trajetória: separar por `;` ou `\n` → datas em bold, cargos em normal, cor `#666666`
7. Performance: separar por `;` ou `\n` → exibir em lista simples
8. Campo vazio: seção omitida (não exibe label sem conteúdo)
9. Resumo de perfil: texto corrido sem truncamento

### Geração de Carômetros
1. Agrupar por coluna selecionada → 1 slide por grupo
2. Sem agrupamento → preencher slides sequencialmente (N colaboradores por slide)
3. Ordenar por nota (decrescente) dentro de cada grupo
4. Placeholder circular em cada card do grid
5. Código de cores aplicado automaticamente em nota e potencial

### Carregamento de Planilha via OneDrive
1. Detectar se entrada começa com `https://` → modo OneDrive
2. Converter URL de compartilhamento para URL de download direto
3. Fazer download com `requests.get(url, timeout=15)`
4. Salvar em `tempfile.NamedTemporaryFile(suffix=".xlsx")`
5. Processar normalmente e deletar o temporário ao finalizar
6. Em caso de falha: exibir mensagem clara e não iniciar geração

### Threading (obrigatório)
- Toda geração roda em `QThread` separada
- Comunicação thread → UI exclusivamente via `Signal` (nunca atualizar widgets diretamente)
- Sinais usados: `progress_updated(int)`, `log_message(str)`, `finished()`, `error(str)`
- Botão GERAR desabilitado durante geração para evitar duplo clique

### Tratamento de Erros
| Situação | Comportamento |
|---|---|
| Planilha local não encontrada | Ícone vermelho no campo, mensagem abaixo |
| Link OneDrive inacessível | Mensagem: "Verifique a conexão com a rede corporativa" |
| Coluna obrigatória não mapeada | Alerta antes de iniciar, geração bloqueada |
| Erro em 1 colaborador | Log `✗` + continua para o próximo, não trava o lote |
| LibreOffice não instalado | Aviso em Settings + gera apenas PPTX silenciosamente |
| Download timeout (>15s) | Mensagem de erro com instrução de usar arquivo local |

### Persistência
- `config.json` salvo em `%APPDATA%\USIGenerator\config.json`
- Campos salvos: tema, caminho padrão planilha, caminho padrão saída, formato saída, colunas carômetro
- Restaurado automaticamente na próxima abertura

---

## 12. Distribuição como .exe

### Comando PyInstaller (build.bat)
```bash
pyinstaller ^
  --onedir ^
  --windowed ^
  --icon=assets/icon.ico ^
  --add-data "assets;assets" ^
  --collect-all PySide6 ^
  --name="USI Generator" ^
  main.py
```

> ⚠️ `--collect-all PySide6` é obrigatório para o `.exe` funcionar sem Python instalado.

### Estrutura do output
```
dist/
└── USI Generator/
    ├── USI Generator.exe     ← executar com duplo clique
    ├── assets/
    │   ├── logo_usiminas.png
    │   └── icon.ico
    └── _internal/            ← Python + PySide6 + libs (não mexer)
```

### Distribuição para a equipe
1. Compactar a pasta `USI Generator/` em `.zip`
2. Compartilhar via OneDrive / Teams / e-mail com a equipe
3. Usuário descompacta em qualquer pasta e executa o `.exe`
4. **Sem instalação de Python, sem dependências adicionais**
5. LibreOffice deve ser instalado separadamente (apenas se quiser PDF)

### Requisitos da máquina do usuário
| Item | Requisito |
|---|---|
| Sistema operacional | Windows 10 ou 11 (64-bit) |
| RAM | 4 GB mínimo |
| Espaço em disco | ~200 MB para o app |
| Rede corporativa | Necessária apenas para carregar planilha via OneDrive |
| LibreOffice | Necessário apenas para exportar PDF (gratuito, opcional) |
| Microsoft Office | Não necessário para rodar o app |

---

## 13. Planilha de Entrada

### Colunas recomendadas
```
nome | idade | cargo | antiguidade | formacao | resumo_perfil | trajetoria | performance | area | potencial | nota
```

> A coluna `foto` foi removida do projeto. Não há campo de foto — o placeholder circular é gerado automaticamente em todos os slides.

### Exemplo de linha completa
```
Luana Cristina Gonçalves Almeida | 40 | Coordenador Produção | 16 anos |
Engenharia Química – Pitágoras |
Formada em Engenharia Química, atua como Coordenadora de Carboquímico... |
2024-2025 - Coordenador Produção; 2022-2024 - Supervisor Produção; 2018-2022 - Técnico Produção |
2023: 5PROM; 2024: 4AP |
Carboquímico | Alto | 4.5
```

### Auto-detecção de colunas

| Campo | Variações aceitas |
|---|---|
| `nome` | `nome`, `name`, `nome_completo`, `colaborador`, `funcionario` |
| `idade` | `idade`, `age`, `anos` |
| `cargo` | `cargo`, `funcao`, `função`, `role`, `posicao`, `posição` |
| `antiguidade` | `antiguidade`, `tempo_empresa`, `anos_empresa`, `admissao` |
| `formacao` | `formacao`, `formação`, `graduacao`, `escolaridade`, `education` |
| `resumo_perfil` | `resumo`, `perfil`, `resumo_perfil`, `descricao`, `bio` |
| `trajetoria` | `trajetoria`, `trajetória`, `historico`, `histórico`, `carreira` |
| `performance` | `performance`, `avaliacao`, `avaliação`, `resultado`, `nota_historico` |
| `area` | `area`, `área`, `departamento`, `setor`, `gerencia` |
| `potencial` | `potencial`, `potential` |
| `nota` | `nota`, `score`, `avaliacao_atual`, `resultado_atual` |

---

## 14. Saída de Arquivos

```
pasta_saida/
├── fichas/
│   ├── Luana_Cristina_Goncalves_Almeida.pptx
│   ├── Luana_Cristina_Goncalves_Almeida.pdf
│   ├── Carlos_Ferreira.pptx
│   ├── Carlos_Ferreira.pdf
│   └── ...
├── carometros/
│   ├── Carometro_Talent_Development.pptx
│   ├── Carometro_Talent_Development.pdf
│   └── ...
└── log_geracao_2025-03-14_143022.txt
```

---

## 15. Dependências — requirements.txt

```
PySide6>=6.6.0
python-pptx>=0.6.23
openpyxl>=3.1.2
pandas>=2.0.0
requests>=2.31.0
pyinstaller>=6.0.0
```

> `Pillow` foi removido — não há processamento de imagens sem a feature de foto.

Instalar:
```bash
pip install -r requirements.txt
```

---

## 16. Roadmap de Versões

### v1.0 — MVP (foco atual)
- [x] Geração de Fichas de Currículo (template exato Ficha_Luana_Cristina.pptx)
- [x] Geração de Carômetros (grid 3/4/5 colunas, agrupamento por área)
- [x] Placeholder circular branco com borda verde no lugar de fotos
- [x] Export PPTX + PDF (LibreOffice)
- [x] Interface PySide6 com QSS — design Usiminas
- [x] Modo claro e escuro com troca em tempo real
- [x] Fonte de dados: arquivo local `.xlsx` ou link OneDrive
- [x] Mapeamento de colunas com auto-detecção
- [x] Log de progresso em tempo real (QThread + Signal)
- [x] Distribuição como `.exe` portátil (PyInstaller)
- [x] Configurações persistentes em `config.json`

### v1.1
- [ ] Preview ao vivo do slide com dados reais do primeiro colaborador
- [ ] Histórico de gerações com data, quantidade de arquivos e tempo gasto
- [ ] Suporte a autenticação OAuth para links privados do SharePoint

### v1.2
- [ ] Templates customizáveis (upload de `.pptx` base)
- [ ] Geração em lote de múltiplos grupos em sequência
- [ ] Exportação Word (.docx) além de PPTX

---

## 17. Segurança e Privacidade

- Dados de colaboradores (avaliações, dados pessoais) nunca saem da máquina
- A planilha do OneDrive é baixada localmente, processada e o temporário é deletado
- Nenhum dado é enviado para servidores externos em nenhum momento
- Ideal para conformidade com **LGPD**

---

## 18. Notas Críticas para o Desenvolvedor

1. **Formato WIDE obrigatório na ficha:** `prs.slide_width = Inches(13.271)` e `prs.slide_height = Inches(7.5)`. Se usar o padrão 10", todo o posicionamento ficará errado.

2. **Dois verdes distintos:** `#84BD00` é o verde da UI e da borda do placeholder. `#92D050` é exclusivo para o PPTX gerado (título do nome, labels de seção). Nunca misturar.

3. **Trajetória em cor cinza `#666666`:** datas (`2024-2025`) em bold, cargos em normal. Implementar com runs separados no `python-pptx`.

4. **Placeholder circular — não usar `ROUNDED_RECTANGLE`:** usar `add_shape` com tipo `OVAL` (código 9) para garantir círculo perfeito. Garantir `width == height` para não virar elipse.

5. **Threading com PySide6:** usar `QThread` subclassado com `pyqtSignal`. Nunca chamar métodos de widget diretamente da thread — apenas emitir sinais. Conectar sinais aos slots da UI no thread principal.

6. **PyInstaller + PySide6:** o flag `--collect-all PySide6` é obrigatório. Sem ele, o `.exe` abre e fecha imediatamente em máquinas sem Qt instalado.

7. **Download OneDrive:** links do tipo `https://usiminas.sharepoint.com/:x:/...` precisam ser convertidos para links de download. Testar com link real antes de implementar a conversão — o formato pode variar entre tenants do Microsoft 365.

8. **Fundo do slide da ficha:** há dois retângulos cinza claro sobrepostos (não é fundo branco puro). Replicar adicionando ambas as formas com `add_shape(RECTANGLE, ...)` antes de qualquer elemento de texto.

---

*Documento gerado por: Talent Development · Usiminas*  
*Versão 2.0 — Março 2025 · Assistido por Claude (Anthropic) — claude.ai*
