# Tests Instructions — USI Generator

> Instruções específicas para escrita de testes no projeto USI Generator

---

## Filosofia: TDD é Obrigatório

> **Nenhuma funcionalidade nova ou modificação existente pode ser implementada sem que um teste correspondente seja escrito primeiro.**

### O ciclo TDD

```
🔴 RED   → Escreva o teste. Ele deve FALHAR (a implementação ainda não existe).
🟢 GREEN → Escreva o MÍNIMO de código para o teste passar.
🔵 BLUE  → Refatore com confiança. Testes garantem que nada quebrou.
```

Se você está escrevendo código sem um teste falhando antes, está violando o fluxo TDD.

---

## Stack de Testes

| Ferramenta | Uso |
|---|---|
| `pytest` | Runner principal e framework de asserções |
| `pytest-cov` | Cobertura de código |
| `pytest-mock` | Mocking via `mocker` fixture |
| `unittest.mock` | `MagicMock`, `patch`, `call` |

### Instalação

```bash
pip install -r requirements-dev.txt
```

### Executar todos os testes

```bash
pytest
```

### Com cobertura detalhada

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Apenas uma área

```bash
pytest tests/unit/core/
pytest tests/unit/core/test_reader.py
pytest tests/unit/core/test_reader.py::TestReader::test_detect_columns_maps_nome_field
```

---

## Configuração (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Cobertura mínima global:** 80%  
**Cobertura obrigatória para `app/core/`:** 100% das funções públicas

---

## Estrutura de Testes

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_reader.py
│   │   ├── test_image_utils.py
│   │   ├── test_generator_ficha.py
│   │   ├── test_generator_carom.py
│   │   └── test_pdf_exporter.py
│   ├── config/
│   │   ├── test_settings.py
│   │   └── test_theme.py
│   └── ui/
│       ├── test_screen_ficha.py
│       ├── test_screen_carom.py
│       ├── test_screen_progress.py
│       └── test_screen_settings.py
├── integration/
│   ├── test_ficha_flow.py
│   └── test_carom_flow.py
└── fixtures/
    ├── colaboradores_sample.xlsx    ← planilha com 3–5 colaboradores fictícios
    ├── colaboradores_empty.xlsx     ← planilha sem linhas de dados
    ├── colaboradores_missing_cols.xlsx  ← planilha sem coluna obrigatória
    └── fotos/
        └── avatar_test.jpg
```

---

## Convenções de Nomenclatura

### Arquivos

```
test_{módulo_testado}.py
```

### Classes

```python
class Test{Classe}:           # para testar uma classe específica
class Test{Funcionalidade}:   # para testar um comportamento
```

### Funções

```
test_{função}_{cenário}_{resultado_esperado}
```

**Exemplos bons:**

```python
def test_read_spreadsheet_returns_list_of_dicts()
def test_read_spreadsheet_raises_file_not_found_for_invalid_path()
def test_detect_columns_maps_nome_completo_to_nome_field()
def test_detect_columns_returns_none_for_unmapped_field()
def test_generate_avatar_always_returns_same_color_for_same_name()
def test_get_score_color_returns_green_for_score_above_4()
def test_export_to_pdf_returns_false_when_libreoffice_unavailable()
```

**Exemplos ruins:**

```python
def test_reader()              # muito vago
def test_1()                   # sem significado
def test_works_correctly()     # não descreve o comportamento
```

---

## Padrão de Testes por Tipo

### Testes Unitários — Core

Cada função pública do core deve ser testada de forma isolada, mockando dependências externas.

```python
# tests/unit/core/test_reader.py

import pytest
from unittest.mock import patch, MagicMock
from app.core.reader import (
    read_spreadsheet,
    detect_columns,
    parse_multiline_field,
    normalize_filename,
)


class TestReadSpreadsheet:

    def test_returns_list_of_dicts_for_valid_file(self, tmp_path):
        # Arrange
        xlsx = tmp_path / "test.xlsx"
        # criar xlsx com openpyxl na fixture
        ...
        # Act
        result = read_spreadsheet(str(xlsx))
        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)

    def test_raises_file_not_found_for_invalid_path(self):
        with pytest.raises(FileNotFoundError):
            read_spreadsheet("/caminho/que/nao/existe.xlsx")

    def test_empty_cells_return_empty_string_not_none(self, xlsx_with_empty_cells):
        result = read_spreadsheet(str(xlsx_with_empty_cells))
        for row in result:
            for value in row.values():
                assert value is not None


class TestDetectColumns:

    @pytest.mark.parametrize("header,expected_field", [
        ("nome", "nome"),
        ("Nome Completo", "nome"),
        ("COLABORADOR", "nome"),
        ("funcionario", "nome"),
        ("cargo", "cargo"),
        ("FUNÇÃO", "cargo"),
        ("potencial", "potencial"),
        ("NOTA", "nota"),
    ])
    def test_maps_known_variations(self, header, expected_field):
        mapping = detect_columns([header])
        assert mapping.get(expected_field) == header

    def test_returns_none_for_unknown_column(self):
        mapping = detect_columns(["coluna_desconhecida_xyz"])
        # todos os campos devem ser None
        assert all(v is None for v in mapping.values())


class TestParseMultilineField:

    def test_splits_by_semicolon(self):
        result = parse_multiline_field("2024-2025 - Cargo A; 2022-2024 - Cargo B")
        assert len(result) == 2
        assert result[0] == "2024-2025 - Cargo A"

    def test_splits_by_newline(self):
        result = parse_multiline_field("2024-2025 - Cargo A\n2022-2024 - Cargo B")
        assert len(result) == 2

    def test_removes_empty_items(self):
        result = parse_multiline_field("Cargo A;; Cargo B;")
        assert "" not in result

    def test_empty_string_returns_empty_list(self):
        assert parse_multiline_field("") == []


class TestNormalizeFilename:

    @pytest.mark.parametrize("name,expected", [
        ("Ana Martins", "Ana_Martins"),
        ("João Bárbara", "Joao_Barbara"),
        ("Léa  Costa", "Lea__Costa"),   # espaços duplos → underlines duplos (ou strip)
        ("", ""),
    ])
    def test_normalizes_correctly(self, name, expected):
        assert normalize_filename(name) == expected
```

---

### Testes Unitários — Config

```python
# tests/unit/config/test_settings.py

import json
import pytest
from unittest.mock import patch
from app.config.settings import load_config, save_config, reset_to_defaults, DEFAULT_CONFIG


class TestLoadConfig:

    def test_returns_defaults_when_file_not_exists(self, tmp_path):
        with patch("app.config.settings.get_config_path", return_value=tmp_path / "config.json"):
            config = load_config()
        assert config == DEFAULT_CONFIG

    def test_loads_existing_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"theme": "light"}))
        with patch("app.config.settings.get_config_path", return_value=config_file):
            config = load_config()
        assert config["theme"] == "light"


class TestSaveConfig:

    def test_creates_file_with_correct_content(self, tmp_path):
        config_file = tmp_path / "config.json"
        with patch("app.config.settings.get_config_path", return_value=config_file):
            save_config({"theme": "dark"})
        assert config_file.exists()
        saved = json.loads(config_file.read_text())
        assert saved["theme"] == "dark"


class TestThemeConstants:

    def test_verde_usiminas_is_correct_hex(self):
        from app.config.theme import VERDE_USIMINAS
        assert VERDE_USIMINAS == "#84BD00"

    def test_verde_slide_is_distinct_from_verde_usiminas(self):
        from app.config.theme import VERDE_USIMINAS, VERDE_SLIDE
        assert VERDE_SLIDE == "#92D050"
        assert VERDE_SLIDE != VERDE_USIMINAS

    def test_all_color_constants_are_valid_hex(self):
        import re
        import app.config.theme as theme
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        color_attrs = [attr for attr in dir(theme) if not attr.startswith("_")]
        for attr in color_attrs:
            value = getattr(theme, attr)
            if isinstance(value, str) and value.startswith("#"):
                assert hex_pattern.match(value), f"{attr}={value} não é HEX válido"
```

---

### Testes Unitários — UI (sem abrir janela)

```python
# tests/unit/ui/test_screen_ficha.py

import pytest
from unittest.mock import MagicMock, patch


class TestFichaScreenValidation:
    """Testa lógica de validação sem instanciar janela Tkinter."""

    def _make_screen(self, spreadsheet="", photos_dir=""):
        """Cria instância sem __init__ do CTk."""
        from app.ui.screen_ficha import FichaScreen
        screen = FichaScreen.__new__(FichaScreen)
        screen.spreadsheet_path = spreadsheet
        screen.photos_dir = photos_dir
        screen._status_labels = {}
        return screen

    def test_validate_inputs_returns_false_without_spreadsheet(self):
        screen = self._make_screen(spreadsheet="", photos_dir="/fotos")
        assert screen._validate_inputs() is False

    def test_validate_inputs_returns_false_without_photos_dir(self):
        screen = self._make_screen(spreadsheet="/planilha.xlsx", photos_dir="")
        assert screen._validate_inputs() is False

    def test_validate_inputs_returns_true_with_both_fields(self, tmp_path):
        xlsx = tmp_path / "plan.xlsx"
        xlsx.touch()
        screen = self._make_screen(str(xlsx), str(tmp_path))
        assert screen._validate_inputs() is True


class TestFichaScreenConfig:

    def test_get_config_returns_all_required_keys(self, ...):
        required_keys = [
            "spreadsheet_path", "photos_dir", "output_dir",
            "column_mapping", "include_photo", "gerar_pdf"
        ]
        config = screen._get_config()
        for key in required_keys:
            assert key in config, f"Chave '{key}' faltando em get_config()"
```

---

### Testes de Integração

```python
# tests/integration/test_ficha_flow.py

import pytest
from pathlib import Path
from app.core.reader import read_spreadsheet, detect_columns
from app.core.generator_ficha import generate_ficha_pptx
from pptx import Presentation
from pptx.util import Inches


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestFichaGenerationFlow:

    def test_full_flow_creates_pptx_file(self, tmp_path):
        # Arrange
        spreadsheet = FIXTURES / "colaboradores_sample.xlsx"
        photos_dir = str(FIXTURES / "fotos")
        output_dir = str(tmp_path)

        employees = read_spreadsheet(str(spreadsheet))
        assert len(employees) > 0

        # Act
        generated = generate_ficha_pptx(employees, photos_dir, output_dir)

        # Assert
        assert len(generated) == len(employees)
        for filepath in generated:
            assert Path(filepath).exists()
            assert filepath.endswith(".pptx")

    def test_generated_slide_has_correct_wide_dimensions(self, tmp_path):
        spreadsheet = FIXTURES / "colaboradores_sample.xlsx"
        employees = read_spreadsheet(str(spreadsheet))
        generated = generate_ficha_pptx(employees[:1], "", str(tmp_path))

        prs = Presentation(generated[0])
        assert abs(prs.slide_width - Inches(13.271)) < 1000   # tolerância em EMU
        assert abs(prs.slide_height - Inches(7.5)) < 1000

    def test_generated_file_name_has_no_accents(self, tmp_path):
        employees = [{"nome": "João Bárbara", "cargo": "Analista"}]
        generated = generate_ficha_pptx(employees, "", str(tmp_path))
        filename = Path(generated[0]).name
        assert "ã" not in filename
        assert "á" not in filename
        assert " " not in filename
```

---

## Fixtures Compartilhadas (`conftest.py`)

```python
# tests/conftest.py

import pytest
import openpyxl
from pathlib import Path


@pytest.fixture
def xlsx_sample(tmp_path) -> Path:
    """Planilha de amostra com 3 colaboradores fictícios."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["nome", "cargo", "idade", "area", "nota", "potencial"])
    ws.append(["Ana Martins", "Analista", 30, "TI", 4.5, "Alto"])
    ws.append(["Carlos Silva", "Coordenador", 45, "RH", 3.2, "Médio"])
    ws.append(["Beatriz Costa", "Técnica", 28, "TI", 2.8, "Baixo"])
    path = tmp_path / "sample.xlsx"
    wb.save(path)
    return path


@pytest.fixture
def xlsx_empty(tmp_path) -> Path:
    """Planilha com cabeçalho mas sem dados."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["nome", "cargo"])
    path = tmp_path / "empty.xlsx"
    wb.save(path)
    return path


@pytest.fixture
def mock_queue(mocker):
    """Fila mockada para testes de threading."""
    import queue
    q = queue.Queue()
    return q
```

---

## Mocking de Dependências Externas

### Mockar subprocess (LibreOffice)

```python
def test_export_calls_libreoffice_with_correct_args(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)

    from app.core.pdf_exporter import export_to_pdf
    result = export_to_pdf("/path/to/file.pptx", "/output/")

    assert result is True
    call_args = mock_run.call_args[0][0]
    assert "--headless" in call_args
    assert "--convert-to" in call_args
    assert "pdf" in call_args
```

### Mockar sistema de arquivos

```python
def test_read_spreadsheet_raises_when_file_missing(mocker):
    mocker.patch("os.path.exists", return_value=False)
    with pytest.raises(FileNotFoundError):
        read_spreadsheet("/nao/existe.xlsx")
```

---

## Checklist TDD por Feature

Antes de fazer commit de qualquer feature, verifique:

- [ ] Arquivo de teste existe e existia ANTES da implementação
- [ ] Todos os testes da feature estão passando (`pytest`)
- [ ] Cobertura não caiu abaixo de 80% (`pytest --cov`)
- [ ] Testes cobrem happy path, edge cases e error cases
- [ ] Funções públicas do core têm 100% das asserções cobertas
- [ ] Nenhum teste usa `time.sleep()` — use mocks para simular delays
- [ ] Nenhum teste abre janela Tkinter real

---

## Anti-padrões a Evitar

```python
# ❌ Teste que não testa nada
def test_generate_ficha():
    generate_ficha_pptx([], "", "")  # sem asserção

# ❌ Teste frágil dependente de caminho absoluto
def test_read_file():
    result = read_spreadsheet("C:\\Users\\fulano\\Desktop\\plan.xlsx")

# ❌ Teste que testa implementação, não comportamento
def test_uses_openpyxl():
    with patch("openpyxl.load_workbook") as mock:
        read_spreadsheet("file.xlsx")
    mock.assert_called_once()   # testa detalhe interno, não comportamento

# ✅ Testa comportamento observável
def test_read_spreadsheet_returns_employee_count_matching_rows(xlsx_sample):
    result = read_spreadsheet(str(xlsx_sample))
    assert len(result) == 3   # 3 linhas de dados na fixture
```

---

*USI Generator · Tests Layer · Talent Development · Usiminas · 2026*