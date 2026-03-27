from __future__ import annotations

PALETTE: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#141414",
        "bg_alt": "#101010",
        "surface": "#1A1A1A",
        "surface_alt": "#202020",
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
    font-size: 12px;
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
QWidget#contentRoot {{
    background-color: {palette["bg"]};
}}
QFrame#topbar {{
    background-color: {palette["sidebar"]};
    border-bottom: 1px solid {palette["border"]};
}}
QLabel#topbarTitle {{
    font-size: 19px;
    font-weight: 700;
    color: {palette["text"]};
}}
QLabel#topbarSubtitle {{
    color: {palette["text_dim"]};
    font-size: 11px;
}}
QLabel#topbarBadge {{
    background-color: {palette["accent_soft"]};
    color: {palette["accent"]};
    border: 1px solid {palette["accent"]};
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
}}
QLabel#brandMark {{
    background-color: {VERDE_USIMINAS};
    color: #111111;
    border-radius: 10px;
    font-size: 20px;
    font-weight: 900;
    padding: 8px;
}}
QLabel#brandTitle {{
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.4px;
}}
QLabel#brandSubtitle {{
    color: {palette["accent"]};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QLabel#navSectionLabel {{
    color: {palette["text_dim"]};
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 6px 10px 2px 10px;
}}
QPushButton#navButton {{
    background-color: transparent;
    color: {palette["text_muted"]};
    text-align: left;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 11px 12px;
    font-weight: 600;
}}
QPushButton#navButton:hover {{
    background-color: {palette["surface_alt"]};
    color: {palette["text"]};
    border-color: {palette["border"]};
}}
QPushButton#navButton:checked {{
    background-color: {palette["accent_soft"]};
    color: {palette["accent"]};
    border-color: {palette["accent"]};
}}
QFrame#heroCard,
QFrame#sectionCard,
QFrame#previewCard,
QFrame#previewPanel,
QFrame#metricCard,
QFrame#panel,
QFrame#subpanel,
QFrame#slideCard,
QFrame#caromCanvas,
QFrame#logPanel,
QFrame#statusPanel,
QFrame#settingsPanel,
QFrame#previewListItem {{
    background-color: {palette["surface"]};
    border: 1px solid {palette["border"]};
    border-radius: 16px;
}}
QFrame#slideCard,
QFrame#caromCanvas {{
    background-color: {palette["bg_alt"]};
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
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 600;
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
    border: 1px solid {VERDE_USIMINAS};
    font-weight: 800;
}}
QPushButton#primary:hover {{
    background-color: {palette["accent_hover"]};
    border-color: {palette["accent_hover"]};
}}
QPushButton#secondaryGhost {{
    background-color: transparent;
    color: {palette["text_muted"]};
}}
QPushButton#chipButton {{
    min-width: 42px;
}}
QPushButton#chipButton:checked {{
    background-color: {palette["accent_soft"]};
    color: {palette["accent"]};
    border-color: {palette["accent"]};
}}
QCheckBox {{
    spacing: 10px;
    color: {palette["text"]};
    font-weight: 600;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid {palette["border_strong"]};
    background-color: {palette["surface_alt"]};
}}
QCheckBox::indicator:checked {{
    background-color: {palette["accent"]};
    border: 1px solid {palette["accent"]};
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
QTextEdit#logBox {{
    background-color: {palette["bg_alt"]};
    border: 1px solid {palette["border"]};
    border-radius: 14px;
    padding: 10px;
}}
QLabel#previewLabel {{
    color: {palette["text_dim"]};
    font-size: 11px;
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
"""
