from __future__ import annotations

PALETTE: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#141414",
        "bg_alt": "#101010",
        "surface": "#1A1A1A",
        "surface_alt": "#202020",
        "surface_2": "#202020",
        "surface_soft": "#242424",
        "sidebar": "#111111",
        "sidebar_alt": "#151515",
        "input": "#121212",
        "border": "#2A2A2A",
        "border_strong": "#363636",
        "border_hover": "#4B4B4B",
        "text": "#EEEEEE",
        "text_muted": "#A1A1AA",
        "text_dim": "#6B7280",
        "accent": "#84BD00",
        "accent_hover": "#9AD11D",
        "accent_soft": "#1E2A14",
        "accent_surface": "#101A08",
        "success": "#84BD00",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#60A5FA",
    },
    "light": {
        "bg": "#f0f0f0",
        "bg_alt": "#E7EBE2",
        "surface": "#FFFFFF",
        "surface_alt": "#F7F8F4",
        "surface_2": "#F7F8F4",
        "surface_soft": "#F4F6EF",
        "sidebar": "#E6EADF",
        "sidebar_alt": "#DCE2D4",
        "input": "#FFFFFF",
        "border": "#D4D8CF",
        "border_strong": "#BFC6B3",
        "border_hover": "#95A08A",
        "text": "#1A1A1A",
        "text_muted": "#58606B",
        "text_dim": "#7D8590",
        "accent": "#6F9E00",
        "accent_hover": "#5A8500",
        "accent_soft": "#E6F0CB",
        "accent_surface": "#F5F9E9",
        "success": "#6F9E00",
        "warning": "#C98B00",
        "error": "#C24141",
        "info": "#2563EB",
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
QFrame#appShell {{
    background-color: {palette["bg"]};
}}
QFrame#sidebar {{
    background-color: {palette["sidebar"]};
    border-right: 1px solid {palette["border"]};
}}
QFrame#sidebar[collapsed="true"] {{
    background-color: {palette["sidebar_alt"]};
}}
QLabel#brandMark {{
    background-color: {palette["accent_soft"]};
    color: {palette["accent"]};
    border-radius: 12px;
    font-size: 22px;
    font-weight: 800;
    qproperty-alignment: AlignCenter;
}}
QFrame#sidebar[collapsed="true"] QLabel#brandMark {{
    qproperty-alignment: AlignCenter;
}}
QLabel#brandTitle {{
    font-size: 14px;
    font-weight: 800;
}}
QLabel#brandSubtitle,
QLabel#navSectionLabel {{
    color: {palette["text_dim"]};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}}
QPushButton#navButton {{
    text-align: left;
    min-height: 38px;
    border-radius: 10px;
    font-weight: 600;
    background-color: transparent;
    line-height: 1.15;
}}
QPushButton#navButton:hover {{
    background-color: {palette["surface_alt"]};
}}
QPushButton#navButton:checked {{
    background-color: {palette["accent_soft"]};
    border-color: {palette["accent"]};
    color: {palette["accent"]};
}}
QFrame#sidebar[collapsed="true"] QPushButton#navButton {{
    text-align: center;
    padding-left: 0px;
    padding-right: 0px;
    padding-top: 6px;
    padding-bottom: 6px;
    font-size: 11px;
    font-weight: 700;
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
    background-color: {palette["surface_alt"]};
    border-radius: 12px;
}}
QFrame#metricCard {{
    background-color: {palette["accent_surface"]};
}}
QLabel#pageEyebrow,
QLabel#sectionEyebrow {{
    color: {palette["accent"]};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QLabel#heroTitle {{
    color: {palette["accent"]};
    font-size: 28px;
    font-weight: 800;
}}
QLabel#heroSubtitle,
QLabel#sectionSubtitle,
QLabel#bodyMuted,
QLabel#muted {{
    color: {palette["text_muted"]};
}}
QLabel#sectionTitle {{
    font-size: 16px;
    font-weight: 700;
}}
QLabel#windowTitle,
QLabel#title {{
    font-size: 20px;
    font-weight: 800;
}}
QLabel#metricValue {{
    color: {palette["accent"]};
    font-size: 24px;
    font-weight: 800;
}}
QLabel#metricTitle {{
    font-size: 12px;
    font-weight: 700;
}}
QLabel#metricFootnote,
QLabel#dim {{
    color: {palette["text_dim"]};
}}
QLabel#statusBadge {{
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
    min-width: 70px;
}}
QLabel#statusBadge[tone="neutral"] {{
    background-color: {palette["surface_alt"]};
    color: {palette["text_muted"]};
    border: 1px solid {palette["border"]};
}}
QLabel#statusBadge[tone="info"] {{
    background-color: rgba(96, 165, 250, 0.14);
    color: {palette["info"]};
    border: 1px solid rgba(96, 165, 250, 0.5);
}}
QLabel#statusBadge[tone="success"] {{
    background-color: {palette["accent_soft"]};
    color: {palette["success"]};
    border: 1px solid {palette["success"]};
}}
QLabel#statusBadge[tone="warning"] {{
    background-color: rgba(245, 158, 11, 0.14);
    color: {palette["warning"]};
    border: 1px solid rgba(245, 158, 11, 0.5);
}}
QLabel#statusBadge[tone="error"] {{
    background-color: rgba(239, 68, 68, 0.14);
    color: {palette["error"]};
    border: 1px solid rgba(239, 68, 68, 0.5);
}}
QLineEdit,
QComboBox,
QSpinBox,
QTextEdit,
QListWidget {{
    background-color: {palette["input"]};
    border: 1px solid {palette["border"]};
    border-radius: 10px;
    padding: 8px 10px;
    color: {palette["text"]};
    selection-background-color: {palette["accent"]};
    selection-color: #111111;
}}
QLineEdit:hover,
QComboBox:hover,
QSpinBox:hover,
QTextEdit:hover,
QListWidget:hover {{
    border-color: {palette["border_hover"]};
}}
QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QTextEdit:focus,
QListWidget:focus {{
    border: 1px solid {palette["accent"]};
}}
QLineEdit[invalid="true"],
QComboBox[invalid="true"] {{
    border: 1px solid {palette["error"]};
    background-color: {palette["surface_alt"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background-color: {palette["surface"]};
    border: 1px solid {palette["border_strong"]};
    selection-background-color: {palette["accent_soft"]};
    selection-color: {palette["accent"]};
}}
QPushButton {{
    background-color: {palette["surface_alt"]};
    color: {palette["text"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    padding: 9px 14px;
}}
QPushButton:hover {{
    border-color: {palette["border_hover"]};
    background-color: {palette["surface_soft"]};
}}
QPushButton:pressed {{
    background-color: {palette["surface"]};
}}
QPushButton:disabled {{
    color: {palette["text_dim"]};
    background-color: {palette["surface"]};
    border-color: {palette["border"]};
}}
QPushButton#primary {{
    background-color: {VERDE_USIMINAS};
    color: #111111;
    border-color: {VERDE_USIMINAS};
    font-weight: 700;
    min-height: 38px;
}}
QPushButton#primary:hover {{
    background-color: {palette["accent_hover"]};
    border-color: {palette["accent_hover"]};
}}
QPushButton#secondaryGhost {{
    background-color: transparent;
    color: {palette["text_muted"]};
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
QPushButton#sidebar_toggle {{
    background-color: {palette["surface_2"]};
    border: 1px solid {palette["border"]};
    border-radius: 10px;
    font-size: 14px;
    font-weight: 700;
    padding: 0px;
}}
QPushButton#sidebar_toggle:hover,
QPushButton#sidebar_toggle:focus {{
    border-color: {VERDE_USIMINAS};
    color: {VERDE_USIMINAS};
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
QFrame#sectionCard QLineEdit,
QFrame#sectionCard QComboBox,
QFrame#sectionCard QTextEdit,
QFrame#sectionCard QListWidget,
QFrame#sectionCard QSpinBox,
QFrame#heroCard QLineEdit,
QFrame#heroCard QComboBox,
QFrame#heroCard QTextEdit,
QFrame#heroCard QListWidget,
QFrame#heroCard QSpinBox,
QFrame#statusPanel QLineEdit,
QFrame#statusPanel QComboBox,
QFrame#statusPanel QTextEdit,
QFrame#statusPanel QListWidget,
QFrame#statusPanel QSpinBox,
QFrame#logPanel QLineEdit,
QFrame#logPanel QComboBox,
QFrame#logPanel QTextEdit,
QFrame#logPanel QListWidget,
QFrame#logPanel QSpinBox,
QFrame#settingsPanel QLineEdit,
QFrame#settingsPanel QComboBox,
QFrame#settingsPanel QTextEdit,
QFrame#settingsPanel QListWidget,
QFrame#settingsPanel QSpinBox {{
    background-color: {palette["surface"]};
}}
QFrame#metricCard QLineEdit,
QFrame#metricCard QComboBox,
QFrame#metricCard QTextEdit,
QFrame#metricCard QListWidget,
QFrame#metricCard QSpinBox {{
    background-color: {palette["accent_surface"]};
}}
QFrame#logPanel QTextEdit#logBox {{
    background-color: {palette["surface_alt"]};
}}
QComboBox QAbstractItemView {{
    background-color: {palette["surface"]};
    color: {palette["text"]};
    border: 1px solid {palette["border"]};
    selection-background-color: {palette["surface_2"]};
    selection-color: {palette["text"]};
}}
QProgressBar {{
    background-color: {palette["surface_alt"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    min-height: 14px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {VERDE_USIMINAS};
    border-radius: 7px;
}}
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#previewTitle {{
    font-size: 18px;
    font-weight: 700;
}}
QLabel#previewValue {{
    font-size: 22px;
    font-weight: 800;
}}
QLabel#previewMeta,
QLabel#previewItemMeta {{
    color: {palette["text_muted"]};
}}
QLabel#previewItemTitle {{
    font-weight: 700;
}}
QLabel#previewItemAccent {{
    color: {palette["accent"]};
    font-weight: 700;
}}
QLabel#avatarBadge {{
    background-color: {palette["accent_soft"]};
    color: {palette["accent"]};
    border-radius: 15px;
    font-weight: 800;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 4px;
}}
QScrollBar::handle:vertical {{
    background: {palette["border_hover"]};
    border-radius: 6px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
    border: none;
}}
QLabel#panelTitle {{
    font-size: 16px;
    font-weight: 700;
}}
QLabel#panelTitleStrong {{
    color: {palette["text"]};
    font-size: 17px;
    font-weight: 800;
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
