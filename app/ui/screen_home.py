from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class HomeScreen(QWidget):
    ficha_requested = Signal()
    carom_requested = Signal()
    settings_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("USI Generator")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Talent Development")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(12)

        ficha_card = self._build_card(
            "Ficha de Currículo",
            "Gerar fichas no template oficial a partir da base atual.",
            "Abrir ficha",
            self.ficha_requested.emit,
        )
        carom_card = self._build_card(
            "Carômetro",
            "Gerar grids por grupo com placeholder circular e ordenação por nota.",
            "Abrir carômetro",
            self.carom_requested.emit,
        )
        settings_card = self._build_card(
            "Configurações",
            "Tema, defaults, cache do OneDrive e caminhos padrão.",
            "Abrir configurações",
            self.settings_requested.emit,
        )

        self.stats_label = QLabel("Sem gerações registradas.")
        self.stats_label.setObjectName("muted")
        self.history_label = QLabel("Histórico vazio.")
        self.history_label.setWordWrap(True)
        self.history_label.setObjectName("dim")

        grid.addWidget(ficha_card, 0, 0)
        grid.addWidget(carom_card, 0, 1)
        grid.addWidget(settings_card, 1, 0, 1, 2)
        layout.addLayout(grid)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.history_label)
        layout.addStretch(1)

    def _build_card(
        self, title: str, body: str, button_label: str, action
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("title")
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setObjectName("muted")
        button = QPushButton(button_label)
        button.setObjectName("primary")
        button.clicked.connect(action)

        layout.addWidget(title_label)
        layout.addWidget(body_label)
        layout.addStretch(1)
        layout.addWidget(button)
        return card

    def update_stats(self, fichas_count: int, carom_count: int) -> None:
        self.stats_label.setText(
            f"Fichas geradas: {fichas_count} | Carômetros gerados: {carom_count}"
        )

    def refresh_history(self, items: list[str]) -> None:
        self.history_label.setText("\n".join(items) if items else "Histórico vazio.")
