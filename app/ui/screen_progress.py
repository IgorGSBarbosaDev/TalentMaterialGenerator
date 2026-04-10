from __future__ import annotations

from html import escape

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.components import MetricCard, SectionCard, StatusBadge


class ProgressScreen(QWidget):
    open_output_requested = Signal(str)
    reset_requested = Signal()
    chrome_changed = Signal()

    page_title = "Geracao"
    page_badge = "Em execucao"

    def __init__(self) -> None:
        super().__init__()
        self._output_dir = ""

        layout = QVBoxLayout(self)
        self._root_layout = layout
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        summary = SectionCard(
            "Processamento",
            "Progresso e status do job.",
            object_name="statusPanel",
        )
        self.summary_card = summary
        title_row = QHBoxLayout()
        self.state_badge = StatusBadge("Em execucao", "info")
        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("bodyMuted")
        self.subtitle_label.setWordWrap(True)
        title_row.addWidget(self.state_badge)
        title_row.addWidget(self.subtitle_label, 1)
        summary.add_layout(title_row)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.percent_metric = MetricCard("Percentual", "0%", "Execucao atual")
        self.count_metric = MetricCard("Processados", "0 de 0", "Fila atual")
        self.elapsed_metric = MetricCard("Status", "Preparando", "Aguardando callbacks")
        metrics.addWidget(self.percent_metric)
        metrics.addWidget(self.count_metric)
        metrics.addWidget(self.elapsed_metric)
        summary.add_layout(metrics)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        summary.add_widget(self.progress_bar)

        counter_row = QHBoxLayout()
        self.counter_label = QLabel("0 de 0")
        self.counter_label.setObjectName("muted")
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("metricTitle")
        counter_row.addWidget(self.counter_label)
        counter_row.addStretch(1)
        counter_row.addWidget(self.percent_label)
        summary.add_layout(counter_row)
        layout.addWidget(summary)

        log_panel = SectionCard(
            "Log de execucao",
            "Eventos em tempo real.",
            object_name="logPanel",
        )
        self.log_panel = log_panel
        self.log_box = QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 10))
        log_panel.add_widget(self.log_box, 1)

        button_row = QHBoxLayout()
        self.btn_open = QPushButton("Abrir pasta de saida")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._emit_open_output)
        self.btn_reset = QPushButton("Nova geracao")
        self.btn_reset.setObjectName("primary")
        self.btn_reset.clicked.connect(self.reset_requested.emit)
        button_row.addWidget(self.btn_open)
        button_row.addWidget(self.btn_reset)
        button_row.addStretch(1)
        log_panel.add_layout(button_row)
        layout.addWidget(log_panel, 1)

    def set_context(self, title: str, subtitle: str, badge: str = "Em execucao") -> None:
        self.page_title = title
        self.page_badge = badge
        self.state_badge.update_status(badge, "info")
        self.subtitle_label.setText(subtitle)
        self.elapsed_metric.set_value("Preparando")
        self.elapsed_metric.set_footnote("Aguardando callbacks")
        self.chrome_changed.emit()

    def update_progress(self, current: int, total: int, name: str = "") -> None:
        percent = 0 if total <= 0 else int((current / total) * 100)
        self.progress_bar.setValue(percent)
        label = f"{current} de {total}"
        if name:
            label = f"{label}  |  {name}"
        self.counter_label.setText(label)
        self.percent_label.setText(f"{percent}%")
        self.percent_metric.set_value(f"{percent}%")
        self.count_metric.set_value(f"{current} de {total}")
        self.elapsed_metric.set_value("Processando")
        self.elapsed_metric.set_footnote(name or "Sem item atual")

    def append_log(self, message: str, level: str = "info") -> None:
        prefixes = {
            "success": "OK",
            "warning": "WARN",
            "error": "ERRO",
            "info": "INFO",
        }
        colors = {
            "success": "#84BD00",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "info": "#A1A1AA",
        }
        prefix = prefixes.get(level, "INFO")
        color = colors.get(level, "#A1A1AA")
        safe_message = escape(message)
        self.log_box.append(
            f'<span style="color:{color}; font-weight:700;">[{prefix}]</span> {safe_message}'
        )

    def on_complete(self, output_dir: str, count: int, elapsed: str) -> None:
        self._output_dir = output_dir
        self.page_badge = "Concluido"
        self.state_badge.update_status("Concluido", "success")
        self.elapsed_metric.set_value(elapsed)
        self.elapsed_metric.set_footnote("Tempo total")
        self.btn_open.setEnabled(True)
        self.append_log(
            f"Concluido. {count} arquivo(s) gerado(s) em {elapsed}.", "success"
        )
        self.append_log("Abra a pasta de saida para revisar os arquivos gerados.", "info")
        self.chrome_changed.emit()

    def on_error(self, message: str) -> None:
        self.page_badge = "Falha"
        self.state_badge.update_status("Falha", "error")
        self.elapsed_metric.set_value("Interrompido")
        self.elapsed_metric.set_footnote("Verifique o log")
        self.append_log(message, "error")
        self.chrome_changed.emit()

    def reset(self) -> None:
        self._output_dir = ""
        self.page_title = "Geracao"
        self.page_badge = "Em execucao"
        self.progress_bar.setValue(0)
        self.counter_label.setText("0 de 0")
        self.percent_label.setText("0%")
        self.percent_metric.set_value("0%")
        self.count_metric.set_value("0 de 0")
        self.elapsed_metric.set_value("Preparando")
        self.elapsed_metric.set_footnote("Aguardando callbacks")
        self.state_badge.update_status("Em execucao", "info")
        self.subtitle_label.setText("")
        self.log_box.clear()
        self.btn_open.setEnabled(False)
        self.chrome_changed.emit()

    def _emit_open_output(self) -> None:
        if self._output_dir:
            self.open_output_requested.emit(self._output_dir)

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        margin = 18 if collapsed else 24
        self._root_layout.setContentsMargins(margin, margin, margin, margin)
        self._root_layout.setSpacing(10 if collapsed else 14)
        self.summary_card.subtitle_label.setVisible(not collapsed)
        self.log_panel.subtitle_label.setVisible(not collapsed)
