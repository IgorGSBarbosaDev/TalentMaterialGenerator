# UI Layer Instructions — USI Generator

> Instruções específicas para desenvolvimento em `app/ui/`

---

## Responsabilidade da Camada UI

A camada `app/ui/` é responsável por **coletar inputs do usuário, disparar operações e exibir resultados**. Toda lógica de negócio fica no `app/core/`.

**Regra absoluta:** a UI não processa dados, não lê arquivos, não monta slides. Ela apenas:
- Coleta configurações do usuário
- Valida que os campos obrigatórios foram preenchidos
- Dispara threads de geração
- Exibe progresso e resultados

---

## Framework: CustomTkinter

Usar sempre `customtkinter` (alias `ctk`). Nunca usar `tkinter` puro para novos widgets.

```python
import customtkinter as ctk
```

**Modo de aparência** configurado globalmente em `main.py`:

```python
ctk.set_appearance_mode("dark")   # ou "light"
ctk.set_default_color_theme("green")
```

---

## Estrutura da Janela Principal (`app_window.py`)

```
AppWindow (CTk, 900×600)
├── Sidebar (CTkFrame, 200px fixo)
│   ├── Logo Usiminas
│   ├── Menu (Home, Ficha, Carômetro, Configurações)
│   └── Versão do app (rodapé)
└── Content Area (CTkFrame, expansível)
    ├── Topbar (48px) — título da tela atual
    └── Screen Frame (troca entre telas)
```

**Navegação entre telas:**

```python
def navigate_to(self, screen: str) -> None:
    """
    Esconde a tela atual e exibe a nova.
    Atualiza o título na topbar.
    Marca item ativo na sidebar.
    """
```

Telas disponíveis: `"home"`, `"ficha"`, `"carometo"`, `"progress"`, `"settings"`

---

## Design System

### Cores da Interface

```python
# Importar sempre de app.config.theme
from app.config.theme import (
    VERDE_USIMINAS, VERDE_ESCURO,
    FUNDO, SUPERFICIE, SUPERFICIE_2,
    TEXTO_PRIMARIO, TEXTO_SECUNDARIO,
)
```

### Fontes

```python
FONTE_TITULO  = ("Segoe UI", 16, "bold")
FONTE_CORPO   = ("Segoe UI", 12)
FONTE_PEQUENA = ("Segoe UI", 10)
FONTE_LOG     = ("Consolas", 11)      # para log de progresso
```

### Tamanhos padrão

```python
SIDEBAR_WIDTH  = 200
TOPBAR_HEIGHT  = 48
PADDING        = 20
CARD_RADIUS    = 8
BORDER_WIDTH   = 1
```

### Botão Primário

```python
ctk.CTkButton(
    master=frame,
    text="GERAR FICHAS",
    fg_color=VERDE_USIMINAS,       # "#84BD00"
    hover_color=VERDE_ESCURO,      # "#4A6E00"
    text_color="#000000",
    font=("Segoe UI", 13, "bold"),
    height=44,
    corner_radius=6,
)
```

### Item de Menu Ativo (Sidebar)

```python
# Ativo: borda direita verde + texto em destaque
# Inativo: sem borda, texto secundário
```

---

## Padrão de Threading — Obrigatório

**Nunca** chamar funções de geração diretamente no event loop do Tkinter.

### Template de disparo de geração

```python
import threading
import queue

class ScreenFicha(ctk.CTkFrame):

    def _start_generation(self) -> None:
        if not self._validate_inputs():
            return

        self.btn_gerar.configure(state="disabled")
        self._queue: queue.Queue = queue.Queue()

        config = self._get_config()

        self._thread = threading.Thread(
            target=self._run_worker,
            args=(config, self._queue),
            daemon=True
        )
        self._thread.start()
        self.after(100, self._check_queue)

    def _run_worker(self, config: dict, q: queue.Queue) -> None:
        # Chama app.core — NUNCA toca em widgets aqui
        from app.core.generator_ficha import generate_ficha_pptx
        generate_ficha_pptx(
            employees=config["employees"],
            photos_dir=config["photos_dir"],
            output_dir=config["output_dir"],
            callback=lambda msg: q.put(msg)
        )

    def _check_queue(self) -> None:
        try:
            while True:
                msg = self._queue.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass

        if self._thread.is_alive():
            self.after(100, self._check_queue)
        else:
            self.btn_gerar.configure(state="normal")

    def _handle_message(self, msg: dict) -> None:
        match msg["type"]:
            case "progress":
                # atualizar screen_progress
                pass
            case "log":
                # adicionar linha ao log
                pass
            case "complete":
                # navegar para tela de resultado
                pass
            case "error":
                # exibir mensagem de erro
                pass
```

---

## Validação de Inputs

Cada tela de configuração deve implementar `_validate_inputs() -> bool`.

**Padrão de validação visual:**

```python
def _validate_file_field(self, path: str, label: ctk.CTkLabel) -> bool:
    """Atualiza ícone ✓/✗ ao lado do campo em tempo real."""
    if path and os.path.exists(path):
        label.configure(text="✓", text_color=VERDE_USIMINAS)
        return True
    else:
        label.configure(text="✗", text_color=ERRO)
        return False
```

Acionar validação no evento `<FocusOut>` e ao clicar em "Procurar".

---

## Telas — Contratos de Interface

### `screen_home.py`

```python
class HomeScreen(ctk.CTkFrame):
    on_ficha_click: callable   # chamado ao clicar no card Ficha
    on_carom_click: callable   # chamado ao clicar no card Carômetro

    def update_stats(self, fichas_count: int, carom_count: int) -> None: ...
    def refresh_history(self) -> None: ...   # lê config.json e atualiza lista
```

### `screen_ficha.py`

```python
class FichaScreen(ctk.CTkFrame):
    def _validate_inputs(self) -> bool: ...
    def _get_config(self) -> dict: ...      # retorna dict com todos os params
    def _auto_detect_columns(self) -> None: ...
    def _start_generation(self) -> None: ...
```

### `screen_carom.py`

```python
class CaromScreen(ctk.CTkFrame):
    def _validate_inputs(self) -> bool: ...
    def _get_config(self) -> dict: ...
    def _start_generation(self) -> None: ...
```

`_get_config()` de CaromScreen deve retornar:

```python
{
    "spreadsheet_path": str,
    "photos_dir": str,
    "output_dir": str,
    "column_mapping": dict,
    "colunas": int,          # 3, 4 ou 5
    "agrupamento": str | None,
    "titulo": str,
    "show_nota": bool,
    "show_potencial": bool,
    "show_cargo": bool,
    "cores_automaticas": bool,
    "gerar_pdf": bool,
}
```

### `screen_progress.py`

```python
class ProgressScreen(ctk.CTkFrame):
    def update_progress(self, current: int, total: int) -> None: ...
    def append_log(self, message: str, level: str = "info") -> None: ...
        # level: "success" → ✓, "warning" → ⚠, "error" → ✗, "info" → •
    def on_complete(self, output_dir: str, count: int, elapsed: str) -> None: ...
    def reset(self) -> None: ...   # limpa log e zera barra para nova geração
```

### `screen_settings.py`

```python
class SettingsScreen(ctk.CTkFrame):
    def toggle_theme(self) -> None: ...       # alterna dark/light imediatamente
    def save_settings(self) -> None: ...      # persiste em config.json
    def reset_settings(self) -> None: ...     # carrega DEFAULT_CONFIG
```

---

## Modo Claro e Escuro

A troca de tema deve ser **imediata**, sem reiniciar o app:

```python
def toggle_theme(self) -> None:
    current = ctk.get_appearance_mode()
    new_mode = "Light" if current == "Dark" else "Dark"
    ctk.set_appearance_mode(new_mode)
    settings.save_config({"theme": new_mode.lower()})
```

**Cores fixas em ambos os modos:**
- Verde Usiminas `#84BD00` — sempre igual
- Verde slide `#92D050` — apenas nos slides, não na UI

---

## TDD — Requisitos para UI

Testes de UI **não devem instanciar janelas Tkinter**. Use mocks e teste apenas a lógica de estado.

```python
# Exemplo de como testar sem abrir janela
from unittest.mock import MagicMock, patch

def test_validate_inputs_returns_false_without_spreadsheet():
    screen = FichaScreen.__new__(FichaScreen)  # cria sem chamar __init__
    screen.spreadsheet_path = ""
    screen.photos_dir = "/alguma/pasta"
    assert screen._validate_inputs() is False
```

**O que testar em telas:**
- `_validate_inputs()` retorna `False` para cada campo obrigatório ausente
- `_get_config()` retorna dict com todas as chaves e tipos corretos
- `_auto_detect_columns()` popula os dropdowns corretamente (mock do reader)
- `update_progress()` não lança exceção com valores extremos (0, 100, total=0)
- `toggle_theme()` chama `ctk.set_appearance_mode` com valor alternado

---

*USI Generator · UI Layer · Talent Development · Usiminas · 2026*