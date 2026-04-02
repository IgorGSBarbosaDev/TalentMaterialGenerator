---
name: interface-design-pyside6
description: This skill is for interface design in PySide6 — dashboards, admin panels, desktop apps, tools, and interactive products. NOT for web/HTML interfaces.
---

# Interface Design — PySide6

Build interface design with craft and consistency for desktop applications using PySide6 and Qt Style Sheets (QSS).

## Scope

**Use for:** Desktop dashboards, admin panels, SaaS desktop clients, tools, settings pages, data-heavy interfaces in PySide6.

**Not for:** Web interfaces, HTML/CSS products, marketing pages.

---

# The Problem

You will generate generic output. Your training has seen thousands of Qt dashboards — gray `QMainWindow`, blue `QPushButton`, flat `QTableWidget`. The patterns are strong.

You can follow the entire process below and still produce a Qt template. Default `QApplication` palette. System fonts. `QVBoxLayout` everything. That "default gray Qt app" look that screams unfinished tool.

This happens because Qt/PySide6 has strong visual defaults — and because QSS has quirks that punish laziness. The gap between intent and craft is where Qt defaults win.

The process below helps. But process alone doesn't guarantee craft. You have to catch yourself.

---

# Where Qt Defaults Hide

**The palette is the first trap.** By default, PySide6 inherits the OS theme — which on Windows is flat gray, on macOS is system-native, on Linux is whatever the distro chose. If you're not explicitly overriding `QPalette` AND setting QSS, you're designing nothing. You're inheriting accidents.

**`QVBoxLayout` / `QHBoxLayout` everywhere feels like structure.** But layout IS the design. Margins, spacing, stretch factors, alignment — these are not scaffolding, they are rhythm. A layout with `setContentsMargins(0, 0, 0, 0)` everywhere feels cramped. A layout with default margins everywhere feels unintentional. Breathing room is a design decision.

**`QLabel` + `QLineEdit` + `QPushButton` is not a form.** Native Qt widgets unstyled look like system dialogs. The moment you reach for an unstyled widget, you've stopped designing and started assembling.

**`QSS` feels like "just make it look better."** But QSS is your entire design language. It's not finishing — it's the work. `QWidget { background: #1e1e1e; }` and `QWidget#sidebar { background: #161616; border-right: 1px solid #2a2a2a; }` are completely different design decisions.

**Widget object names feel like implementation detail.** But `setObjectName()` is how you target specific widgets in QSS. `QPushButton` styles all buttons. `QPushButton#primaryAction` styles one with intent. If you're not using object names to build a targeted style system, you have no system.

---

# Qt/PySide6 Technical Foundations

## QSS vs CSS — Key Differences

QSS looks like CSS but behaves differently. Know the gaps:

```python
# ✅ QSS supports
QWidget { background-color: #1a1a2e; }
QPushButton:hover { background-color: #2a2a3e; }
QPushButton:pressed { background-color: #0f0f1e; }
QPushButton:disabled { color: #555; }
QWidget[active="true"] { border: 1px solid #4CAF50; }  # custom properties

# ❌ QSS does NOT support
# - CSS variables (--my-color)
# - calc()
# - CSS Grid / Flexbox
# - @media queries
# - CSS transitions/animations (use QPropertyAnimation instead)
# - ::before / ::after pseudo-elements
# - Most CSS4 features
```

## Replacing CSS Variables — Use Python Constants

Since QSS has no variables, define your token system in Python:

```python
# tokens.py — your design system lives here
class Tokens:
    # Surface elevation
    BG_BASE      = "#0d0d14"
    BG_SURFACE   = "#13131f"
    BG_RAISED    = "#1a1a2a"
    BG_OVERLAY   = "#212133"

    # Text hierarchy
    TEXT_PRIMARY   = "#e8e8f0"
    TEXT_SECONDARY = "#9898b0"
    TEXT_TERTIARY  = "#5a5a72"
    TEXT_MUTED     = "#3a3a50"

    # Borders
    BORDER_SUBTLE   = "#1e1e30"
    BORDER_DEFAULT  = "#2a2a40"
    BORDER_EMPHASIS = "#3d3d58"

    # Brand / accent
    ACCENT       = "#7c6af7"
    ACCENT_HOVER = "#9580ff"
    ACCENT_PRESS = "#6254d4"

    # Semantic
    SUCCESS = "#3ecf8e"
    WARNING = "#f5a623"
    ERROR   = "#f04438"

def build_stylesheet(t: Tokens = None) -> str:
    t = t or Tokens()
    return f"""
        QWidget {{
            background-color: {t.BG_BASE};
            color: {t.TEXT_PRIMARY};
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 13px;
        }}
        /* ... full QSS built from tokens */
    """
```

## QPalette — Set It or Lose It

Always set the palette explicitly. Never rely on OS defaults:

```python
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

def apply_palette(app: QApplication, t: Tokens):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(t.BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(t.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base,            QColor(t.BG_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(t.BG_RAISED))
    palette.setColor(QPalette.ColorRole.Text,            QColor(t.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button,          QColor(t.BG_RAISED))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(t.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(t.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(t.TEXT_MUTED))
    app.setPalette(palette)
```

## Layout Discipline

Layouts are design decisions. Treat margins and spacing as tokens:

```python
# Spacing scale — define as constants
SPACING_XS  = 4
SPACING_SM  = 8
SPACING_MD  = 12
SPACING_LG  = 16
SPACING_XL  = 24
SPACING_2XL = 32

# Apply with intent — never use bare integers
layout = QVBoxLayout()
layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
layout.setSpacing(SPACING_SM)
```

## Custom Widgets — When to Build Them

Some things can't be done in QSS. Know when to subclass:

| Need | Solution |
|---|---|
| Custom painting | Subclass `QWidget`, override `paintEvent()` |
| Smooth animations | `QPropertyAnimation` on `geometry`, `opacity`, custom properties |
| Progress rings | Custom `paintEvent` with `QPainter.drawArc()` |
| Custom toggle switch | Subclass `QCheckBox`, override `paintEvent` |
| Hover-aware widget | Override `enterEvent` / `leaveEvent` |
| Donut/arc chart | `paintEvent` + `QPainter` |

## QSS Selector Hierarchy — Use It

```python
# Target by class
QPushButton { ... }

# Target by object name (setObjectName)
QPushButton#primaryBtn { ... }

# Target by state
QPushButton:hover { ... }
QPushButton:pressed { ... }
QPushButton:checked { ... }
QPushButton:disabled { ... }

# Target by custom property (setProperty)
QPushButton[variant="danger"] { background-color: #f04438; }

# Child selectors
QWidget#sidebar QPushButton { ... }        # any depth
QWidget#sidebar > QPushButton { ... }      # direct child only
```

## Fonts — Load Them Properly

```python
from PySide6.QtGui import QFontDatabase

# Load custom font
QFontDatabase.addApplicationFont(":/fonts/Inter-Regular.ttf")
QFontDatabase.addApplicationFont(":/fonts/Inter-Medium.ttf")
QFontDatabase.addApplicationFont(":/fonts/JetBrainsMono-Regular.ttf")

# In QSS
"""
QLabel#heading {
    font-family: 'Inter';
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.3px;
}
QLabel#mono {
    font-family: 'JetBrains Mono';
    font-size: 12px;
}
"""
```

## Animations — QPropertyAnimation Over QSS

QSS has no transitions. Use Qt's animation system:

```python
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

def animate_opacity(widget, start=0.0, end=1.0, duration=200):
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setDuration(duration)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    return anim  # keep reference to prevent GC
```

---

# Intent First

Before touching code, answer these:

**Who is this human?**
Not "users." The actual person. Are they a data analyst? A developer? An operations manager? When do they open this? Stressed or focused? The answer shapes density, color, information hierarchy.

**What must they accomplish?**
Not "use the app." The verb. Monitor deployments. Process invoices. Analyze sensor data. The answer determines what leads, what hides, what the primary action is.

**What should this feel like?**
"Clean and modern" means nothing — especially in Qt where clean is just the OS default. Warm like a notebook? Cold like a terminal? Dense like a trading floor? Calm like a reading app? This shapes your token names, your font choices, your spacing density.

If you cannot answer these with specifics, stop. Ask the user. Do not default.

## Every Choice Must Be A Choice

For every decision, explain WHY — including Qt-specific decisions:

- Why this layout strategy and not another?
- Why `QSplitter` and not fixed widths?
- Why `QStackedWidget` and not tabs?
- Why this spacing scale?
- Why this border approach (QSS border vs QPainter)?

If your answer is "it's common Qt" — you've defaulted.

---

# Product Domain Exploration

**Required outputs before any code:**

**Domain:** Concepts, metaphors, vocabulary from this product's world. Minimum 5.

**Color world:** What colors exist naturally in this domain? Not "dark" or "light" — the actual world. 5+.

**Signature:** One element — visual, interaction, or structural — that could only exist for THIS product. In PySide6 this might be a custom `paintEvent`, a specific navigation pattern, a unique data visualization widget.

**Defaults:** 3 obvious Qt choices to reject. Both visual (default gray QPushButton) and structural (QTabWidget for navigation).

## Proposal Format

```
Domain: [5+ concepts]
Color world: [5+ specific colors/hues]
Signature: [one specific PySide6 element unique to this product]
Rejecting: [default 1] → [alternative], [default 2] → [alternative], [default 3] → [alternative]

Direction: [approach referencing all four]
```

---

# Craft Foundations

## Surface Elevation in QSS

```python
# Subtle elevation — shifts of 6-8% lightness only
"""
QWidget#base    { background-color: #111118; }
QWidget#surface { background-color: #17171f; }  /* +6% */
QWidget#raised  { background-color: #1e1e28; }  /* +7% more */
QWidget#overlay { background-color: #252533; }  /* +7% more */
"""
# Dark mode: higher elevation = slightly lighter
# Each jump: barely visible in isolation, creates clear hierarchy when stacked
```

## Border Strategy — Pick One

```python
# Option A: Borders only — dense tools, technical products
"""
QWidget#card {
    border: 1px solid #1e1e30;
    border-radius: 6px;
}
"""

# Option B: Subtle shadows — approachable products
# QSS shadow via QGraphicsDropShadowEffect:
shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(16)
shadow.setOffset(0, 2)
shadow.setColor(QColor(0, 0, 0, 60))
widget.setGraphicsEffect(shadow)

# Option C: Surface color shifts only — no borders, no shadows
# Hierarchy purely through background tone
```

**Do not mix.** If using borders, use borders throughout. If using shadows, use shadows throughout.

## Text Hierarchy — Four Levels

```python
"""
/* Primary — default text */
QLabel { color: #e8e8f0; font-size: 13px; font-weight: 400; }

/* Secondary — supporting text */
QLabel#secondary { color: #9898b0; font-size: 13px; }

/* Tertiary — metadata */
QLabel#tertiary { color: #5a5a72; font-size: 12px; }

/* Muted — disabled/placeholder */
QLabel#muted { color: #3a3a50; font-size: 12px; }
"""
# Use all four consistently. Only two levels = flat hierarchy.
```

## Navigation in PySide6

Avoid `QTabWidget` for primary navigation — it looks like a dialog. Build custom navigation:

```python
# Sidebar nav pattern — QListWidget or custom buttons
class NavItem(QPushButton):
    def __init__(self, label, icon=None):
        super().__init__(label)
        self.setObjectName("navItem")
        self.setCheckable(True)
        self.setFlat(True)
        # style via QSS: QPushButton#navItem:checked { ... }
```

## Controls — Never Use Unstyled Natives

Always style or replace:

```python
# QComboBox — always style the dropdown arrow
"""
QComboBox {
    background-color: #1a1a2a;
    border: 1px solid #2a2a40;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e8e8f0;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: url(:/icons/chevron-down.svg);
    width: 12px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a2a;
    border: 1px solid #2a2a40;
    selection-background-color: #7c6af7;
}
"""

# QLineEdit — always style focus ring
"""
QLineEdit {
    background-color: #13131f;
    border: 1px solid #2a2a40;
    border-radius: 6px;
    padding: 7px 10px;
    color: #e8e8f0;
}
QLineEdit:focus {
    border-color: #7c6af7;
    background-color: #16162a;
}
QLineEdit:disabled {
    color: #3a3a50;
    background-color: #0d0d14;
}
"""
```

## States — Every Interactive Element

```python
"""
/* Button states */
QPushButton#primary {
    background-color: #7c6af7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton#primary:hover   { background-color: #9580ff; }
QPushButton#primary:pressed { background-color: #6254d4; }
QPushButton#primary:disabled { background-color: #2a2a40; color: #3a3a50; }
"""
# Missing states feel broken. All four: default, hover, pressed/active, disabled.
```

## Data Display

Use `QTableWidget` or `QTreeWidget` with full styling:

```python
"""
QTableWidget {
    background-color: #13131f;
    gridline-color: #1e1e30;
    border: none;
    selection-background-color: #1e1e40;
}
QTableWidget QHeaderView::section {
    background-color: #0d0d14;
    color: #5a5a72;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #1e1e30;
}
QTableWidget::item:selected {
    background-color: #1e1e40;
    color: #e8e8f0;
}
"""
```

## Scrollbars — Always Style Them

Unstyled scrollbars break any dark theme:

```python
"""
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a2a40;
    border-radius: 4px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover { background: #3d3d58; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: transparent; }
"""
```

---

# Token Architecture in Python

```python
# Full token system — adapt to your domain's world
class DarkTheme:
    # Primitives — name them after your product's world
    # Generic: BG_BASE. Specific: FORGE_BASE, DECK_BASE, LEDGER_BASE
    BG_BASE    = "#0d0d14"
    BG_SURFACE = "#13131f"
    BG_RAISED  = "#1a1a2a"
    BG_OVERLAY = "#212133"

    TEXT_PRIMARY   = "#e8e8f0"
    TEXT_SECONDARY = "#9898b0"
    TEXT_TERTIARY  = "#5a5a72"
    TEXT_MUTED     = "#3a3a50"

    BORDER_SUBTLE   = "#1a1a28"
    BORDER_DEFAULT  = "#2a2a40"
    BORDER_EMPHASIS = "#3d3d58"

    ACCENT         = "#7c6af7"
    ACCENT_HOVER   = "#9580ff"
    ACCENT_SURFACE = "#1a1730"  # for selected rows, active nav

    SUCCESS         = "#3ecf8e"
    SUCCESS_SURFACE = "#0d2a1f"
    WARNING         = "#f5a623"
    WARNING_SURFACE = "#2a1e0d"
    ERROR           = "#f04438"
    ERROR_SURFACE   = "#2a0f0d"

    # Control-specific — tuned independently from layout
    INPUT_BG        = BG_SURFACE
    INPUT_BORDER    = BORDER_DEFAULT
    INPUT_FOCUS     = ACCENT
    INPUT_DISABLED  = BG_BASE
```

---

# The Mandate

**Before showing the user, look at what you made.**

Ask yourself: "If they said this looks like a default Qt app, what would they mean?"

That thing — fix it first.

## The Checks

- **The swap test:** If you replaced your QSS with no styling, would the layout still communicate hierarchy? If swapping typeface loses nothing, you defaulted.

- **The Qt native test:** Can you spot any widget that still looks like a bare Qt control? An unstyled `QComboBox`. A default `QScrollBar`. An untouched `QTabBar`. Find them. Style them.

- **The signature test:** Can you point to the specific Python/QSS code that is unique to THIS product? Not "dark theme" — any app can be dark. The thing that only makes sense for your product.

- **The token test:** Read your token names aloud. Do they sound like they belong to this product, or could they be any Qt app?

If any check fails, iterate before showing.

---

# Avoid

- **Unstyled scrollbars** — they always betray a dark theme
- **Default `QTabWidget`** for primary navigation — looks like a dialog
- **`setStyleSheet()` on individual widgets** scattered through code — centralize in one QSS string built from tokens
- **Mixed border weights** — pick one weight and use it consistently
- **Hard-coded hex values** outside the token file — everything traces back to primitives
- **`QSplitter` without styling** — the handle is ugly by default
- **Missing `:disabled` states** — always define them
- **`QMessageBox` unstyled** — it always pops out of the theme
- **Inconsistent `border-radius`** — define a scale (sm: 4px, md: 6px, lg: 10px) and use only those values
- **`setFixedSize()`** unless absolutely necessary — prefer minimum sizes + stretch
- **Mixing QPalette and QSS for the same role** — use QPalette for base, QSS for everything else

---

# Workflow

## Communication

Don't narrate the process. Jump into exploration.

## Suggest + Ask

```
Domain: [5+ concepts]
Color world: [5+ specific colors from the domain's physical world]
Signature: [one PySide6-specific element unique to this product]
Rejecting: [default Qt pattern 1] → [alternative], ...

Direction: [approach referencing all four above]

Does that direction feel right, or do you want to push it somewhere different?
```

## Build Order

1. **Token file first** — `tokens.py` with your full color/spacing system
2. **QPalette** — applied at `QApplication` level before any widget
3. **Base QSS string** — built from tokens, applied via `app.setStyleSheet()`
4. **Layout structure** — `QMainWindow`, sidebar, content area
5. **Navigation** — custom nav, not `QTabWidget`
6. **Primary widgets** — styled with object names
7. **States** — hover, pressed, disabled, focus for every interactive element
8. **Scrollbars** — always, at the end, they're always missed
9. **Evaluate** — run the mandate checks before showing

## If Project Has system.md

Read `.interface-design/system.md` and apply. Tokens and patterns are already decided.

## If No system.md

Follow the 9-step build order. Offer to save at the end.

---

# After Completing a Task

```
"Want me to save these patterns for future sessions?"
```

If yes, write to `.interface-design/system.md`:
- Token system (colors, spacing scale, border-radius scale)
- Depth strategy (borders / shadows / color shifts)
- QSS patterns for core widgets (button, input, table, nav)
- Custom widget implementations worth reusing

---

# PySide6-Specific Commands

- `/interface-design:status` — Current token and pattern state
- `/interface-design:audit` — Check code against system.md tokens and patterns
- `/interface-design:extract` — Extract reusable patterns from existing code
- `/interface-design:critique` — Critique the Qt interface for craft, then rebuild what defaulted
- `/interface-design:tokens` — Output the full token system as Python class
