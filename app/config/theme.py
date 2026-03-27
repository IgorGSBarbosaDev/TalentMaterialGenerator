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
    font-size: 13px;
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
QFrame#topbar {{
    background-color: {palette["surface"]};
    border-bottom: 1px solid {palette["border"]};
}}
QFrame#card, QFrame#panel {{
    background-color: {palette["surface"]};
    border: 1px solid {palette["border"]};
    border-radius: 12px;
}}
QFrame#panelAction {{
    background-color: {palette["surface_2"]};
    border: 1px solid {palette["border_hover"]};
    border-radius: 12px;
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
    padding: 9px 14px;
}}
QPushButton:hover {{
    border-color: {palette["border_hover"]};
}}
QPushButton#primary {{
    background-color: {VERDE_USIMINAS};
    color: #111111;
    border-color: {VERDE_USIMINAS};
    font-weight: 700;
    min-height: 38px;
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
QPushButton#theme_toggle {{
    background-color: {palette["surface_2"]};
    border: 1px solid {palette["border"]};
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    padding: 0px;
}}
QPushButton#theme_toggle:hover {{
    border-color: {VERDE_USIMINAS};
    color: {VERDE_USIMINAS};
}}
QPushButton#theme_toggle:focus {{
    border-color: {VERDE_USIMINAS};
}}
QLineEdit, QComboBox, QTextEdit, QListWidget, QSpinBox {{
    background-color: transparent;
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    padding: 8px;
    color: {palette["text"]};
    min-height: 22px;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QListWidget:focus, QSpinBox:focus {{
    border-color: {VERDE_USIMINAS};
}}
QFrame#panel QLineEdit,
QFrame#panel QComboBox,
QFrame#panel QTextEdit,
QFrame#panel QListWidget,
QFrame#panel QSpinBox {{
    background-color: {palette["surface"]};
}}
QFrame#panelAction QLineEdit,
QFrame#panelAction QComboBox,
QFrame#panelAction QTextEdit,
QFrame#panelAction QListWidget,
QFrame#panelAction QSpinBox {{
    background-color: {palette["surface_2"]};
}}
QFrame#card QLineEdit,
QFrame#card QComboBox,
QFrame#card QTextEdit,
QFrame#card QListWidget,
QFrame#card QSpinBox {{
    background-color: {palette["surface"]};
}}
QFrame#subpanel QLineEdit,
QFrame#subpanel QComboBox,
QFrame#subpanel QTextEdit,
QFrame#subpanel QListWidget,
QFrame#subpanel QSpinBox {{
    background-color: {palette["surface_2"]};
}}
QComboBox QAbstractItemView {{
    background-color: {palette["surface"]};
    color: {palette["text"]};
    border: 1px solid {palette["border"]};
    selection-background-color: {palette["surface_2"]};
    selection-color: {palette["text"]};
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
    font-size: 22px;
    font-weight: 700;
}}
QLabel#muted {{
    color: {palette["text_muted"]};
}}
QLabel#dim {{
    color: {palette["text_dim"]};
}}
QLabel#panelTitle {{
    font-size: 16px;
    font-weight: 700;
}}
QLabel#panelHint {{
    color: {palette["text_dim"]};
    font-size: 12px;
}}
QLabel#statusLabel {{
    border-radius: 8px;
    padding: 8px 10px;
    border: 1px solid {palette["border"]};
    background-color: {palette["surface"]};
}}
QLabel#statusLabel[state="info"] {{
    border-color: {palette["border_hover"]};
    color: {palette["text_muted"]};
}}
QLabel#statusLabel[state="warning"] {{
    border-color: {COR_AVISO};
    color: {COR_AVISO};
}}
QLabel#statusLabel[state="error"] {{
    border-color: {COR_ERRO};
    color: {COR_ERRO};
}}
QLabel#statusLabel[state="success"] {{
    border-color: {VERDE_USIMINAS};
    color: {VERDE_USIMINAS};
}}
"""
