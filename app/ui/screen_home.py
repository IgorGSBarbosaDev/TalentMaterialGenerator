from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.components import MetricCard, SectionCard


class HomeScreen(QWidget):
    ficha_requested = Signal()
    carom_requested = Signal()
    settings_requested = Signal()

    page_title = "Inicio"
    page_badge = "Dashboard"

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        self._root_layout = layout
        self._compact_labels: list[QLabel] = []
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        hero_card = SectionCard(
            "TALENT DEVELOPMENT",
            "",
            object_name="heroCard",
            compact=True,
        )
        self.hero_card = hero_card
        hero_card.title_label.setObjectName("heroTitle")
        hero_card.subtitle_label.setVisible(False)
        layout.addWidget(hero_card)

        actions_grid = QGridLayout()
        self.actions_grid = actions_grid
        actions_grid.setHorizontalSpacing(12)
        actions_grid.setVerticalSpacing(12)

        ficha_card = self._build_action_card(
            "Ficha de Curriculo",
            "Configure campos e gere arquivos individuais.",
            "Ir para ficha",
            self.ficha_requested.emit,
        )
        carom_card = self._build_action_card(
            "Carometro",
            "Defina agrupamento e layout do grid final.",
            "Ir para carometro",
            self.carom_requested.emit,
        )
        history_panel = SectionCard(
            "Historico recente",
            "Ultimas geracoes da sessao.",
        )

        self.history_label = QLabel("Historico vazio.")
        self.history_label.setObjectName("bodyMuted")
        self.history_label.setWordWrap(True)
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(160)
        history_panel.add_widget(self.history_label)
        history_panel.add_widget(self.history_list, 1)

        actions_grid.addWidget(ficha_card, 0, 0)
        actions_grid.addWidget(carom_card, 0, 1)
        actions_grid.addWidget(history_panel, 1, 0, 1, 2)
        actions_grid.setColumnStretch(0, 1)
        actions_grid.setColumnStretch(1, 1)
        layout.addLayout(actions_grid)

        metrics_row = QHBoxLayout()
        self.metrics_row = metrics_row
        metrics_row.setSpacing(12)
        self.ficha_metric = MetricCard("Fichas geradas", "0", "Base atual")
        self.carom_metric = MetricCard("Carometros gerados", "0", "Ciclos visuais")
        self.total_metric = MetricCard("Operacoes registradas", "0", "Ultimas execucoes")
        metrics_row.addWidget(self.ficha_metric)
        metrics_row.addWidget(self.carom_metric)
        metrics_row.addWidget(self.total_metric)
        layout.addLayout(metrics_row)

        self.stats_label = QLabel("Fichas geradas: 0 | Carometros gerados: 0")
        self.stats_label.setObjectName("muted")
        layout.addWidget(self.stats_label)
        layout.addStretch(1)
        self._compact_labels.append(self.stats_label)

    def _build_action_card(
        self, title: str, body: str, button_label: str, action
    ) -> SectionCard:
        card = SectionCard(title, body)
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        open_button = QPushButton(button_label)
        open_button.setObjectName("primary")
        open_button.clicked.connect(action)
        hint = QLabel("")
        hint.setObjectName("bodyMuted")

        action_row.addWidget(open_button)
        action_row.addWidget(hint)
        action_row.addStretch(1)
        card.add_layout(action_row)
        self._compact_labels.append(hint)
        return card

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        margin = 18 if collapsed else 24
        self._root_layout.setContentsMargins(margin, margin, margin, margin)
        self._root_layout.setSpacing(10 if collapsed else 14)
        self.actions_grid.setHorizontalSpacing(10 if collapsed else 12)
        self.actions_grid.setVerticalSpacing(10 if collapsed else 12)
        self.metrics_row.setSpacing(8 if collapsed else 12)
        for label in self._compact_labels:
            label.setVisible(not collapsed)

    def update_stats(self, fichas_count: int, carom_count: int) -> None:
        total = fichas_count + carom_count
        self.ficha_metric.set_value(str(fichas_count))
        self.carom_metric.set_value(str(carom_count))
        self.total_metric.set_value(str(total))
        self.total_metric.set_footnote("Somatorio das geracoes da sessao")
        self.stats_label.setText(
            f"Fichas geradas: {fichas_count} | Carometros gerados: {carom_count}"
        )

    def refresh_history(self, items: list[str]) -> None:
        self.history_label.setText(
            f"Ultimo registro: {items[0]}" if items else "Historico vazio."
        )
        self.history_list.clear()
        for item in items:
            self.history_list.addItem(item)
