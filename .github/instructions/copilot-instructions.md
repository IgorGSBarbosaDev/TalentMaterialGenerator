# Copilot Instructions — USI Generator

## Visão Geral do Projeto

**USI Generator** é um aplicativo desktop Windows desenvolvido para a equipe de **Talent Development da Usiminas**. Ele automatiza a geração em lote de dois tipos de materiais de RH a partir de planilhas Excel:

1. **Fichas de Currículo** — slides individuais por colaborador (`.pptx` + `.pdf`)
2. **Carômetros** — grids visuais de colaboradores por área/gerência (`.pptx` + `.pdf`)

O app roda 100% localmente, sem internet, sem login, distribuído como `.exe` portátil via PyInstaller.

---

## Stack Tecnológica

| Camada | Tecnologia | Versão mínima |
|---|---|---|
| Linguagem | Python | 3.11+ |
| Interface Gráfica | CustomTkinter | 5.2.0 |
| Geração PPTX | python-pptx | 0.6.23 |
| Leitura de planilha | openpyxl + pandas | 3.1.2 / 2.0.0 |
| Processamento de imagem | Pillow | 10.0.0 |
| Exportação PDF | LibreOffice (headless via subprocess) | qualquer |
| Empacotamento | PyInstaller | 6.0.0 |
| Persistência | json (stdlib) | — |
| Testes | pytest + pytest-cov + pytest-mock | 8.0.0 |
| CI/CD | GitHub Actions | — |

---

## Arquitetura do Projeto

```
USI_Generator/
├── .github/
│   ├── workflows/
│   │   └── ci.yml                  ← Pipeline CI completo (trunk-based)
│   └── instructions/
│       ├── copilot-instructions.md ← este arquivo
│       ├── core.instructions.md
│       ├── ui.instructions.md
│       └── tests.instructions.md
├── scripts/
│   ├── check_architecture.py       ← validador de regras arquiteturais
│   └── delivery_check.bat          ← CI local para Windows (rodar antes de push)
├── main.py                         ← ponto de entrada
├── app/
│   ├── ui/
│   │   ├── app_window.py
│   │   ├── screen_home.py
│   │   ├── screen_ficha.py
│   │   ├── screen_carom.py
│   │   ├── screen_progress.py
│   │   └── screen_settings.py
│   ├── core/
│   │   ├── reader.py
│   │   ├── generator_ficha.py
│   │   ├── generator_carom.py
│   │   ├── pdf_exporter.py
│   │   └── image_utils.py
│   └── config/
│       ├── settings.py
│       └── theme.py
├── assets/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── requirements-dev.txt
├── build.bat
└── README.md
```

### Princípios de Arquitetura

- **Core é independente da UI.** Nenhum módulo em `app/core/` importa nada de `app/ui/`.
- **UI é burra.** Toda lógica de negócio fica no core. A UI apenas coleta inputs, dispara threads e exibe resultados.
- **Threading obrigatório.** Geração de slides SEMPRE em `threading.Thread`. Comunicação com a UI exclusivamente via `queue.Queue`. Nunca atualizar widgets direto de uma thread.
- **Configuração centralizada.** Constantes de cor, fonte e layout ficam em `theme.py`. Preferências do usuário em `settings.py`.

---

## Fluxo de Desenvolvimento — Trunk-Based

> Este projeto usa **Trunk-Based Development**. Não existe git-flow, develop, release/branches ou hotfix branches.

### Regras do trunk-based

```
main  ←──── única branch de longa duração (trunk)
  │
  ├─ feat/reader-column-detection   ← branch de vida curta (max 2 dias)
  │   └─ 1 a 3 commits → PR → merge → delete
  │
  ├─ fix/avatar-determinism         ← branch de vida curta (max 1 dia)
  │   └─ 1 commit → PR → merge → delete
  │
  └─ (push direto no main para mudanças triviais e documentação)
```

| Regra | Detalhe |
|---|---|
| Branch máxima | 2 dias. Branches antigas são deletadas sem misericórdia. |
| Commits em main | Apenas via PR (para mudanças em `app/`) ou push direto (docs, config). |
| PR review | Lightweight — foco em arquitetura e testes, não em estilo (CI já garante). |
| Feature flags | Para funcionalidades incompletas que precisam ir ao trunk, use flag em `config.json`. |
| Sem merge commits | Usar squash merge ou rebase. Histórico linear. |

### Convenção de commits (Conventional Commits)

```
feat:     nova funcionalidade
fix:      correção de bug
test:     adiciona/modifica testes
refactor: refatoração sem mudança de comportamento
docs:     apenas documentação
chore:    configuração, CI, dependências
perf:     melhoria de performance
```

**Exemplos:**
```
feat: implement reader.detect_columns with accent-insensitive matching
fix: replace hash() with hashlib.md5 in generate_avatar for determinism
test: add boundary-value tests for get_score_color thresholds
refactor: extract slide position literals to named constants in generator_ficha
chore: add delivery_check.bat and ci.yml for trunk-based flow
```

---

## Padrão TDD — Regra Absoluta

> **Toda funcionalidade nova ou modificação existente DEVE ser precedida por testes.**

### Fluxo obrigatório

```
1. Escreva o teste (vermelho — falha esperada)
2. Implemente o mínimo para o teste passar (verde)
3. Refatore mantendo os testes verdes (refactor)
```

### Cobertura mínima exigida

- **80% de cobertura global** (configurado no `pytest.ini` e no CI)
- Funções públicas do core: **100% cobertura** (hard gate no CI)
- Testes de UI: focam em lógica de estado, não em renderização Tkinter

---

## ✅ Definition of Done — Codex Delivery Checklist

> **Esta seção define o que significa "tarefa concluída" para o Codex.**  
> Nenhuma entrega está completa até que TODOS os itens abaixo tenham passado.  
> O Codex DEVE executar `scripts\delivery_check.bat` ao final de cada tarefa.

### Comando obrigatório ao final de toda entrega

```bat
scripts\delivery_check.bat
```

Este script executa, nesta ordem:

| # | Check | Falha bloqueia push? |
|---|---|---|
| 1 | `python scripts/check_architecture.py` | ✅ Sim |
| 2 | `black --check app/ tests/` | ✅ Sim |
| 3 | `flake8 app/ tests/` | ✅ Sim |
| 4 | `mypy app/` | ✅ Sim |
| 5 | `pytest tests/unit/ --cov=app --cov-fail-under=80` | ✅ Sim |
| 6 | `pytest tests/integration/` | ✅ Sim |

### Critérios individuais

```
[ ] Testes escritos ANTES da implementação (TDD — arquivo de teste existia antes)
[ ] Todos os testes unitários passando (pytest tests/unit/)
[ ] Todos os testes de integração passando (pytest tests/integration/)
[ ] Cobertura global >= 80%
[ ] Cobertura de app/core/ = 100% para funções públicas
[ ] black sem diferenças (black --check app/ tests/)
[ ] flake8 sem violações
[ ] mypy sem erros de tipo
[ ] check_architecture.py sem violations CRITICAL ou HIGH
[ ] Nenhuma importação de app.ui dentro de app/core/
[ ] Nenhum Inches(10) em generator_ficha.py
[ ] Nenhum hash() (builtin) em image_utils.py
[ ] Commits seguem Conventional Commits (feat:/fix:/test:/refactor:/etc.)
[ ] Branch deletada após merge (se era feature branch)
```

### O Codex NÃO deve fazer merge/push se:

- `delivery_check.bat` retorna exit code 1
- Qualquer item da checklist acima não foi verificado
- A cobertura de `app/core/` caiu abaixo de 100%
- Existe alguma violação CRITICAL ou HIGH no `check_architecture.py`

### Modo rápido (desenvolvimento iterativo)

Durante o desenvolvimento iterativo (antes do commit final), use:

```bat
scripts\delivery_check.bat --fast
```

O modo `--fast` pula os testes de integração para ciclos mais rápidos.  
**Nunca faça push com `--fast` — sempre rode o check completo antes do commit.**

---

## Convenções de Código

### Nomenclatura

- **Módulos e arquivos:** `snake_case` (ex: `generator_ficha.py`)
- **Classes:** `PascalCase` (ex: `FichaGenerator`, `AppWindow`)
- **Funções e variáveis:** `snake_case` (ex: `build_slide`, `photos_dir`)
- **Constantes:** `UPPER_SNAKE_CASE` (ex: `VERDE_USIMINAS`, `FONTE_TITULO`)
- **Arquivos de teste:** prefixo `test_` (ex: `test_reader.py`)
- **Classes de teste:** prefixo `Test` (ex: `TestReader`)
- **Funções de teste:** `test_{função}_{cenário}_{resultado_esperado}`

### Type Hints

Todas as funções públicas devem ter anotações de tipo:

```python
def generate_ficha_pptx(
    employees: list[dict],
    photos_dir: str,
    output_dir: str,
    callback: callable | None = None
) -> list[str]:
    ...
```

### Docstrings

Funções públicas do core devem ter docstring mínima:

```python
def make_circular_image(path: str) -> Image | None:
    """
    Carrega uma imagem e aplica máscara circular (RGBA).
    Retorna None se o arquivo não existir ou não for uma imagem válida.
    """
```

### Tratamento de erros

- **Nunca silenciar exceções genéricas** com `except Exception: pass`
- Erros esperados (foto não encontrada, coluna ausente) → log + continuar
- Erros inesperados → propagar com mensagem clara
- Funções do core que podem falhar retornam `None` ou `False`

---

## Paleta de Cores — Referência Rápida

```python
# Identidade Usiminas
VERDE_USIMINAS  = "#84BD00"   # botões, badges, destaques
VERDE_SLIDE     = "#92D050"   # título da ficha (NÃO confundir com VERDE_USIMINAS)
VERDE_ESCURO    = "#4A6E00"   # hover, bordas ativas

# Semânticas
SUCESSO   = "#84BD00"
AVISO     = "#F59E0B"
ERRO      = "#EF4444"
```

> ⚠️ `#92D050` e `#84BD00` são verdes distintos. `#92D050` é exclusivo do template da ficha.

---

## Regras de Negócio Críticas

1. **Slide da ficha usa formato WIDE:** `13.271" × 7.5"`. Nunca usar o padrão `10" × 7.5"`.
2. **Foto circular:** `python-pptx` não suporta crop circular nativo. Usar Pillow + PNG com canal alpha.
3. **Threading obrigatório:** geração em thread separada. UI lê `queue.Queue` a cada 100ms.
4. **Foto não encontrada:** log `⚠` + usar avatar. Nunca interromper a geração do lote.
5. **Erro em um colaborador:** log `✗` + continuar. Nunca travar o lote inteiro.
6. **Campos vazios:** seção omitida no slide.
7. **Nome de arquivo:** sem acentos, espaços → underline (`Ana_Martins.pptx`).
8. **Configuração persistida:** `%APPDATA%\USIGenerator\config.json`.
9. **hash() proibido para determinismo:** usar `hashlib.md5()` — Python's hash() varia com PYTHONHASHSEED.
10. **CI obrigatório:** todo push para main passa pelo pipeline `.github/workflows/ci.yml`.

---

## Geração do Executável

```bat
pyinstaller ^
  --onedir ^
  --windowed ^
  --icon=assets/icon.ico ^
  --add-data "assets;assets" ^
  --collect-all customtkinter ^
  --name="USI Generator" ^
  main.py
```

> `--collect-all customtkinter` é obrigatório. Sem ele, assets do CustomTkinter ficam faltando no `.exe`.

---

## O que NÃO fazer

- ❌ Importar `app.ui` em qualquer módulo de `app.core`
- ❌ Atualizar widgets Tkinter diretamente dentro de uma `threading.Thread`
- ❌ Usar `except Exception: pass` — sempre logar ou propagar
- ❌ Hardcodar caminhos de arquivo — usar `pathlib.Path` e `os.environ`
- ❌ Criar funcionalidade sem teste correspondente (TDD obrigatório)
- ❌ Usar `#84BD00` onde o template exige `#92D050` (e vice-versa)
- ❌ Usar o slide no formato padrão `10"` — sempre `13.271"` para fichas
- ❌ Usar `hash()` builtin para operações determinísticas — usar `hashlib.md5()`
- ❌ Fazer push para main sem rodar `scripts\delivery_check.bat`
- ❌ Manter branches de feature abertas por mais de 2 dias
- ❌ Criar merge commits — usar squash merge ou rebase

---

*USI Generator · Talent Development · Usiminas · 2026*