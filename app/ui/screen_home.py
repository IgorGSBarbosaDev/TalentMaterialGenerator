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
    page_subtitle = "Painel principal do USI Generator"
    page_badge = "Dashboard"

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        hero_card = SectionCard(
            "Fluxo de geracao com visual mais claro e rapido de operar",
            "Escolha o material, valide a base e acompanhe o progresso sem sair da mesma experiencia.",
            object_name="heroCard",
        )
        eyebrow = QLabel("Talent Development")
        eyebrow.setObjectName("pageEyebrow")
        hero_card.body_layout.insertWidget(0, eyebrow)
        hero_card.title_label.setObjectName("heroTitle")
        hero_card.subtitle_label.setObjectName("heroSubtitle")

        hero_actions = QHBoxLayout()
        hero_actions.setSpacing(10)
        btn_ficha = QPushButton("Abrir ficha de curriculo")
        btn_ficha.setObjectName("primary")
        btn_ficha.clicked.connect(self.ficha_requested.emit)
        btn_carom = QPushButton("Abrir carometro")
        btn_carom.clicked.connect(self.carom_requested.emit)
        btn_settings = QPushButton("Preferencias")
        btn_settings.setObjectName("secondaryGhost")
        btn_settings.clicked.connect(self.settings_requested.emit)
        hero_actions.addWidget(btn_ficha)
        hero_actions.addWidget(btn_carom)
        hero_actions.addWidget(btn_settings)
        hero_actions.addStretch(1)
        hero_card.add_layout(hero_actions)
        layout.addWidget(hero_card)

        actions_grid = QGridLayout()
        actions_grid.setHorizontalSpacing(16)
        actions_grid.setVerticalSpacing(16)

        ficha_card = self._build_action_card(
            "Ficha de Curriculo",
            "Monte fichas individuais com mapeamento de colunas, preview persistente e checklist visual.",
            "Ir para ficha",
            self.ficha_requested.emit,
        )
        carom_card = self._build_action_card(
            "Carometro",
            "Configure grupos, colunas e cards do grid com pre-visualizacao imediata do layout final.",
            "Ir para carometro",
            self.carom_requested.emit,
        )
        history_panel = SectionCard(
            "Historico recente",
            "As ultimas geracoes ficam resumidas aqui para voce retomar o contexto rapido.",
        )

        self.history_label = QLabel("Historico vazio.")
        self.history_label.setObjectName("bodyMuted")
        self.history_label.setWordWrap(True)
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(180)
        history_panel.add_widget(self.history_label)
        history_panel.add_widget(self.history_list, 1)

        actions_grid.addWidget(ficha_card, 0, 0)
        actions_grid.addWidget(carom_card, 0, 1)
        actions_grid.addWidget(history_panel, 1, 0, 1, 2)
        layout.addLayout(actions_grid)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(14)
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

    def _build_action_card(
        self, title: str, body: str, button_label: str, action
    ) -> SectionCard:
        card = SectionCard(title, body)
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        open_button = QPushButton(button_label)
        open_button.setObjectName("primary")
        open_button.clicked.connect(action)
        hint = QLabel("Fluxo guiado com preview")
        hint.setObjectName("bodyMuted")

        action_row.addWidget(open_button)
        action_row.addWidget(hint)
        action_row.addStretch(1)
        card.add_layout(action_row)
        return card

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
