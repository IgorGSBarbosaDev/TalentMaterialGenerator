from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def repolish(widget: QWidget) -> None:
    style = widget.style()
    if style is None:
        return
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class SectionCard(QFrame):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        *,
        object_name: str = "sectionCard",
        compact: bool = False,
    ) -> None:
        super().__init__()
        self.setObjectName(object_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10 if compact else 12)

        header = QVBoxLayout()
        header.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        header.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("sectionSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(bool(subtitle))
        header.addWidget(self.subtitle_label)

        layout.addLayout(header)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(10)
        layout.addLayout(self.body_layout)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self.body_layout.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        self.body_layout.addLayout(layout)


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, footnote: str = "") -> None:
        super().__init__()
        self.setObjectName("metricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        self.title_label.setWordWrap(True)

        self.footnote_label = QLabel(footnote)
        self.footnote_label.setObjectName("metricFootnote")
        self.footnote_label.setVisible(bool(footnote))
        self.footnote_label.setWordWrap(True)

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.footnote_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_footnote(self, footnote: str) -> None:
        self.footnote_label.setText(footnote)
        self.footnote_label.setVisible(bool(footnote))


class StatusBadge(QLabel):
    def __init__(self, text: str = "", tone: str = "neutral") -> None:
        super().__init__(text)
        self.setObjectName("statusBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(26)
        self.set_marginless_size_policy()
        self.set_tone(tone)

    def set_marginless_size_policy(self) -> None:
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def set_tone(self, tone: str) -> None:
        self.setProperty("tone", tone)
        repolish(self)

    def update_status(self, text: str, tone: str) -> None:
        self.setText(text)
        self.set_tone(tone)


class NavButton(QPushButton):
    def __init__(
        self,
        label: str,
        icon_text: str | None = None,
        compact_label: str | None = None,
    ) -> None:
        super().__init__(label)
        self._full_label = label
        self._icon_text = icon_text or (label[:1].upper() if label else "?")
        self._compact_label = compact_label or label
        self.setCheckable(True)
        self.setObjectName("navButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(label)

    def set_compact(self, compact: bool) -> None:
        if compact:
            self.setText(self._compact_label)
            self.setProperty("compact", "true")
        else:
            self.setText(self._full_label)
            self.setProperty("compact", "false")
        repolish(self)


class PreviewListItem(QFrame):
    def __init__(self, title: str, meta: str, accent: str = "") -> None:
        super().__init__()
        self.setObjectName("previewListItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        initials = "".join(part[:1] for part in title.split()[:2]).upper() or "?"
        self.avatar = QLabel(initials)
        self.avatar.setObjectName("avatarBadge")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setMinimumSize(30, 30)
        self.avatar.setMaximumSize(30, 30)
        layout.addWidget(self.avatar)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("previewItemTitle")
        self.meta_label = QLabel(meta)
        self.meta_label.setObjectName("previewItemMeta")
        self.meta_label.setWordWrap(True)
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.meta_label)
        layout.addLayout(text_col, 1)

        self.accent_label = QLabel(accent)
        self.accent_label.setObjectName("previewItemAccent")
        self.accent_label.setVisible(bool(accent))
        layout.addWidget(self.accent_label)

    def update_content(self, title: str, meta: str, accent: str = "") -> None:
        initials = "".join(part[:1] for part in title.split()[:2]).upper() or "?"
        self.avatar.setText(initials)
        self.title_label.setText(title)
        self.meta_label.setText(meta)
        self.accent_label.setText(accent)
        self.accent_label.setVisible(bool(accent))


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        elif child_layout is not None:
            clear_layout(child_layout)


def build_badge_row(badges: Iterable[QWidget]) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for badge in badges:
        layout.addWidget(badge)
    layout.addStretch(1)
    return row
