from __future__ import annotations

PALETTE: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#141414",
        "surface": "#1a1a1a",
        "surface_2": "#222222",
        "sidebar": "#111111",
        "border": "#2a2a2a",
        "border_hover": "#444444",
        "text": "#eeeeee",
        "text_muted": "#888888",
        "text_dim": "#555555",
    },
    "light": {
        "bg": "#f0f0f0",
        "surface": "#ffffff",
        "surface_2": "#f5f5f5",
        "sidebar": "#e8e8e8",
        "border": "#dddddd",
        "border_hover": "#bbbbbb",
        "text": "#1a1a1a",
        "text_muted": "#666666",
        "text_dim": "#999999",
    },
}

VERDE_USIMINAS = "#84BD00"
VERDE_SLIDE = "#92D050"
VERDE_ESCURO = "#4A6E00"
COR_AVISO = "#F59E0B"
COR_ERRO = "#EF4444"


def get_palette(mode: str) -> dict[str, str]:
    normalized = str(mode).strip().lower()
    return PALETTE["light"] if normalized == "light" else PALETTE["dark"]


def build_stylesheet(mode: str) -> str:
    palette = get_palette(mode)
    return f"""
QWidget {{
    background-color: {palette["bg"]};
    color: {palette["text"]};
    font-family: "Segoe UI";
    font-size: 12px;
}}
QMainWindow {{
    background-color: {palette["bg"]};
}}
QWidget#sidebar {{
    background-color: {palette["sidebar"]};
    border-right: 1px solid {palette["border"]};
}}
QWidget#contentRoot {{
    background-color: {palette["bg"]};
}}
QFrame#card, QFrame#panel {{
    background-color: {palette["surface"]};
    border: 1px solid {palette["border"]};
    border-radius: 10px;
}}
QFrame#subpanel {{
    background-color: {palette["surface_2"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
}}
QPushButton {{
    background-color: {palette["surface_2"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    padding: 8px 12px;
}}
QPushButton:hover {{
    border-color: {palette["border_hover"]};
}}
QPushButton#primary {{
    background-color: {VERDE_USIMINAS};
    color: #111111;
    border-color: {VERDE_USIMINAS};
    font-weight: 700;
}}
QPushButton#menu_item {{
    background: transparent;
    color: {palette["text_muted"]};
    text-align: left;
    border: none;
    border-right: 2px solid transparent;
    border-radius: 0px;
    padding: 9px 16px;
}}
QPushButton#menu_item:checked {{
    background-color: {palette["surface_2"]};
    color: {VERDE_USIMINAS};
    border-right: 2px solid {VERDE_USIMINAS};
    font-weight: 700;
}}
QLineEdit, QComboBox, QTextEdit, QListWidget, QSpinBox {{
    background-color: {palette["surface"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    padding: 6px;
    color: {palette["text"]};
}}
QProgressBar {{
    background-color: {palette["surface"]};
    border: 1px solid {palette["border"]};
    border-radius: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {VERDE_USIMINAS};
    border-radius: 5px;
}}
QLabel#title {{
    font-size: 20px;
    font-weight: 700;
}}
QLabel#muted {{
    color: {palette["text_muted"]};
}}
QLabel#dim {{
    color: {palette["text_dim"]};
}}
"""
