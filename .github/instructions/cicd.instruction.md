# CI/CD Instructions — USI Generator

> Instruções específicas para o pipeline de CI e o fluxo trunk-based do projeto.  
> Leia este arquivo antes de qualquer operação de commit, push, merge ou entrega.

---

## Pipeline CI — Visão Geral

O CI é definido em `.github/workflows/ci.yml` e executa automaticamente em:
- Todo `push` para `main`
- Todo `pull_request` com destino `main`

### Jobs e ordem de execução

```
① Lint & Format      → black --check + flake8 + mypy
        │
        ├── ② Tests & Coverage  → pytest unit + integration + coverage gates
        │
        └── ③ Architecture      → check_architecture.py + grep patterns
                    │
                    └── ④ Import Smoke  → import all core modules + circular import check
                                │
                                ⑤ Security Audit  → pip-audit (informational on main)
```

### Gates de bloqueio (falha = bloqueia merge)

| Gate | Threshold | Job |
|---|---|---|
| Cobertura global | >= 80% | ② Tests |
| Cobertura app/core/ | = 100% | ② Tests |
| Violations CRITICAL/HIGH | = 0 | ③ Architecture |
| Importações circulares | = 0 | ④ Smoke |
| Módulos core importáveis | 100% | ④ Smoke |

---

## Trunk-Based Development — Regras Operacionais

### Branch naming

```
feat/{kebab-case-description}    → nova funcionalidade
fix/{kebab-case-description}     → correção de bug
test/{kebab-case-description}    → apenas testes
refactor/{kebab-case-description}
chore/{kebab-case-description}   → configuração, CI, docs
```

**Exemplos válidos:**
```
feat/reader-column-detection
fix/avatar-hash-determinism
test/generator-ficha-boundary-values
refactor/extract-slide-positions-constants
chore/add-ci-pipeline
```

### Ciclo de vida de uma feature branch

```
1. git checkout main && git pull
2. git checkout -b feat/nome-da-feature
3. [desenvolver com TDD — máximo 2 dias]
4. scripts\delivery_check.bat   ← OBRIGATÓRIO antes de qualquer push
5. git push origin feat/nome-da-feature
6. Abrir PR → review rápido → squash merge
7. git branch -d feat/nome-da-feature
8. git push origin --delete feat/nome-da-feature
```

### Quando fazer push direto em main (sem PR)

Apenas para:
- Correções de documentação (`.md` files)
- Mudanças em `requirements-dev.txt`
- Ajustes em arquivos de configuração CI (`.github/`)
- Correções triviais de uma única linha em arquivos non-core

**Nunca** push direto em main para:
- Qualquer mudança em `app/`
- Qualquer mudança em `tests/`
- Qualquer mudança em `scripts/`

---

## Delivery Check — Protocolo Local

O Codex DEVE executar `scripts\delivery_check.bat` ao final de toda entrega.

### Fluxo esperado do Codex ao final de qualquer tarefa

```
[Codex implementa funcionalidade seguindo TDD]
         │
         ▼
scripts\delivery_check.bat
         │
    ┌────┴────┐
    │         │
  PASS       FAIL
    │         │
    ▼         ▼
  Commit    Fix issues
  & Push    & re-run
            check
```

### O que fazer se o check falhar

| Falha | Ação |
|---|---|
| black | Rodar `black app/ tests/` e commitar as mudanças de formatação |
| flake8 | Corrigir cada violação reportada |
| mypy | Adicionar type hints faltantes ou corrigir tipos inconsistentes |
| Architecture CRITICAL | Corrigir a violação imediatamente — não negociável |
| Coverage < 80% | Escrever testes para as linhas não cobertas |
| Core coverage < 100% | Escrever testes para funções públicas do core não cobertas |
| Integration tests | Investigar — geralmente indica regressão real |

---

## Variáveis de Ambiente para CI Determinístico

```python
PYTHONHASHSEED = "0"   # Sempre fixar para testes determinísticos
```

Este valor é setado:
- No `ci.yml` como `env` global
- No `delivery_check.bat` antes de rodar pytest
- Nos testes que dependem de comportamento determinístico

**Por quê:** Python's `hash()` é randomizado por padrão para segurança. Funções como `generate_avatar()` que precisam de cor determinística por nome DEVEM usar `hashlib.md5()` — não `hash()`. O `PYTHONHASHSEED=0` no CI apenas elimina falsos negativos nos testes.

---

## Configuração da Branch Protection (GitHub)

Configure em: Settings → Branches → Add rule → `main`

```yaml
# Branch protection rule para main
branch: main
require_pull_request_reviews:
  required_approving_review_count: 1   # ou 0 para solo dev
require_status_checks_to_pass:
  - "① Lint & Format"
  - "② Tests & Coverage"
  - "③ Architecture Rules"
  - "④ Import Smoke Test"
  - "✅ CI Complete"
require_branches_to_be_up_to_date: true
restrict_pushes: false   # permite push direto para docs/config
```

---

## Adicionando Novos Checks ao CI

Para adicionar um novo check ao pipeline:

1. Implemente o check em `scripts/check_architecture.py` (se for validação de código)
   ou crie um novo script em `scripts/`.
2. Adicione um step ao job apropriado em `.github/workflows/ci.yml`.
3. Adicione o mesmo step a `scripts/delivery_check.bat` (espelhar CI local).
4. Documente o novo check neste arquivo.
5. Escreva um teste para o próprio script de check (em `tests/unit/`).

**Regra:** CI e delivery_check.bat devem ser sempre equivalentes.  
Se o CI passa mas o delivery_check falha (ou vice-versa), é um bug de configuração.

---

## Interpretando Falhas de CI no GitHub Actions

### Como abrir o log de um job específico

```
GitHub PR → Checks tab → click no job com ✗ → expand o step com falha
```

### Erros comuns e soluções

| Erro no CI | Causa provável | Solução local |
|---|---|---|
| `black would reformat` | Código formatado diferentemente | `black app/ tests/` |
| `E501 line too long` | Linha > 100 chars | Quebrar a linha |
| `F401 imported but unused` | Import sobrando | Remover o import |
| `error: Missing return type annotation` | Função sem `-> tipo` | Adicionar return type |
| `Coverage.py warning: No data was collected` | pytest não encontrou tests/ | Verificar pytest.ini |
| `Architecture CRITICAL: app/core imports app.ui` | Violação de camada | Remover o import |
| `ModuleNotFoundError` no smoke | Módulo com erro de sintaxe | Rodar `python -m py_compile {arquivo}` |

---

*USI Generator · CI/CD Instructions · Talent Development · Usiminas · 2026*