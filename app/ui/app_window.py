from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QUrl,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import settings, theme
from app.core.reader import resolve_spreadsheet_source
from app.core.worker import GenerationWorker
from app.ui.components import NavButton
from app.ui.screen_carom import CaromScreen
from app.ui.screen_ficha import FichaScreen
from app.ui.screen_home import HomeScreen
from app.ui.screen_progress import ProgressScreen
from app.ui.screen_settings import SettingsScreen


class AppWindow(QMainWindow):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.current_worker: GenerationWorker | None = None
        self._stats = {"ficha": 0, "carom": 0}
        self._history: list[str] = list(config.get("last_generations", []))
        self._current_screen = "home"
        self._sidebar_collapsed = False
        self._sidebar_expanded_width = 248
        self._sidebar_collapsed_width = 88
        self._sidebar_animation_duration_ms = 180

        self.setWindowTitle("USI Generator")
        self.resize(1320, 820)
        self.setMinimumSize(1180, 760)

        root = QFrame()
        root.setObjectName("appShell")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(self._sidebar_expanded_width)
        self.sidebar.setMaximumWidth(self._sidebar_expanded_width)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)
        self.sidebar_layout = sidebar_layout

        brand_row = QHBoxLayout()
        self.brand_row = brand_row
        self.brand_mark = QLabel("U")
        self.brand_mark.setObjectName("brandMark")
        self.brand_mark.setFixedSize(48, 48)
        self.brand_name_widget = QWidget()
        brand_name_col = QVBoxLayout(self.brand_name_widget)
        brand_name_col.setContentsMargins(0, 0, 0, 0)
        brand_name_col.setSpacing(1)
        self.brand_title = QLabel("USIMINAS")
        self.brand_title.setObjectName("brandTitle")
        self.brand_subtitle = QLabel("Talent Development")
        self.brand_subtitle.setObjectName("brandSubtitle")
        brand_name_col.addWidget(self.brand_title)
        brand_name_col.addWidget(self.brand_subtitle)
        brand_row.addWidget(self.brand_mark)
        brand_row.addWidget(self.brand_name_widget, 1)
        sidebar_layout.addLayout(brand_row)

        self.nav_labels: list[QLabel] = []
        sidebar_layout.addWidget(self._build_nav_label("Menu"))
        self.menu_group = QButtonGroup(self)
        self.menu_group.setExclusive(True)
        self.menu_buttons: dict[str, NavButton] = {}
        for key, label, icon, compact_label in (
            ("home", "Inicio", "H", "Inicio"),
            ("ficha", "Ficha", "F", "Ficha"),
            ("carom", "Carometro", "C", "Carom"),
            ("progress", "Geracao", "G", "Gerar"),
        ):
            button = NavButton(label, icon_text=icon, compact_label=compact_label)
            button.clicked.connect(
                lambda _checked=False, target=key: self.navigate_to(target)
            )
            self.menu_group.addButton(button)
            self.menu_buttons[key] = button
            sidebar_layout.addWidget(button)

        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(self._build_nav_label("Sistema"))
        settings_button = NavButton(
            "Configuracoes", icon_text="S", compact_label="Config"
        )
        settings_button.clicked.connect(
            lambda _checked=False: self.navigate_to("settings")
        )
        self.menu_group.addButton(settings_button)
        self.menu_buttons["settings"] = settings_button
        sidebar_layout.addWidget(settings_button)
        sidebar_layout.addStretch(1)

        self.version_label = QLabel("v1.0.0")
        self.version_label.setObjectName("muted")
        sidebar_layout.addWidget(self.version_label)

        content_root = QWidget()
        content_root.setObjectName("contentRoot")
        content_layout = QVBoxLayout(content_root)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.topbar = QFrame()
        self.topbar.setObjectName("topbar")
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(16, 12, 16, 12)
        topbar_layout.setSpacing(10)

        self.sidebar_toggle_button = QPushButton("\u2630")
        self.sidebar_toggle_button.setObjectName("sidebar_toggle")
        self.sidebar_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_toggle_button.setFixedSize(40, 36)
        self.sidebar_toggle_button.clicked.connect(self._toggle_sidebar)
        topbar_layout.addWidget(self.sidebar_toggle_button)

        self._sidebar_animation = QPropertyAnimation(
            self.sidebar, b"minimumWidth", self
        )
        self._sidebar_animation.setDuration(self._sidebar_animation_duration_ms)
        self._sidebar_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._sidebar_animation.valueChanged.connect(
            self._on_sidebar_animation_value_changed
        )
        self._sidebar_animation.finished.connect(self._on_sidebar_animation_finished)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self.topbar_title = QLabel("USI Generator")
        self.topbar_title.setObjectName("title")
        title_col.addWidget(self.topbar_title)
        topbar_layout.addLayout(title_col, 1)

        topbar_layout.addStretch(1)

        self.theme_toggle_button = QPushButton("\u2600")
        self.theme_toggle_button.setObjectName("theme_toggle")
        self.theme_toggle_button.setFixedSize(56, 36)
        self.theme_toggle_button.clicked.connect(self._toggle_theme)
        topbar_layout.addWidget(self.theme_toggle_button)
        content_layout.addWidget(self.topbar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(content_root, 1)

        self.home_screen = HomeScreen()
        self.ficha_screen = FichaScreen(config)
        self.carom_screen = CaromScreen(config)
        self.progress_screen = ProgressScreen()
        self.settings_screen = SettingsScreen(config)

        self.screens = {
            "home": self.home_screen,
            "ficha": self.ficha_screen,
            "carom": self.carom_screen,
            "progress": self.progress_screen,
            "settings": self.settings_screen,
        }
        for screen in self.screens.values():
            self.stack.addWidget(screen)

        self.home_screen.ficha_requested.connect(lambda: self.navigate_to("ficha"))
        self.home_screen.carom_requested.connect(lambda: self.navigate_to("carom"))
        self.home_screen.settings_requested.connect(
            lambda: self.navigate_to("settings")
        )
        self.ficha_screen.generate_requested.connect(
            lambda payload: self._start_generation("ficha", payload)
        )
        self.carom_screen.generate_requested.connect(
            lambda payload: self._start_generation("carom", payload)
        )
        self.progress_screen.reset_requested.connect(lambda: self.navigate_to("home"))
        self.progress_screen.open_output_requested.connect(self._open_output_dir)
        self.progress_screen.chrome_changed.connect(self._sync_topbar)
        self.settings_screen.save_requested.connect(self._save_settings)
        self.settings_screen.reset_requested.connect(self._reset_settings)
        self.settings_screen.refresh_cache_requested.connect(self._refresh_cache_now)

        self._refresh_home()
        self.ficha_screen.load_config(config)
        self.carom_screen.load_config(config)
        self.settings_screen.load_config(config)
        self._update_theme_toggle_button()
        self._apply_sidebar_state()
        self.navigate_to("home")

    def _build_nav_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("navSectionLabel")
        self.nav_labels.append(label)
        return label

    def navigate_to(self, screen: str) -> None:
        widget = self.screens[screen]
        self._current_screen = screen
        self.stack.setCurrentWidget(widget)
        button = self.menu_buttons.get(screen)
        if button is not None:
            button.setChecked(True)
        self._apply_sidebar_state()
        self._sync_topbar()

    def _sync_topbar(self) -> None:
        widget = self.screens[self._current_screen]
        self.topbar_title.setText(getattr(widget, "page_title", "USI Generator"))

    def _has_running_worker(self) -> bool:
        return self.current_worker is not None and self.current_worker.isRunning()

    def _set_generation_busy(self, busy: bool) -> None:
        self.ficha_screen.btn_generate.setEnabled(not busy)
        self.carom_screen.btn_generate.setEnabled(not busy)
        self.settings_screen.setEnabled(not busy)

    def _start_generation(self, job_type: str, payload: dict[str, Any]) -> None:
        if self._has_running_worker():
            self.navigate_to("progress")
            QMessageBox.information(
                self,
                "Geracao em andamento",
                "Ja existe uma geracao em andamento. Aguarde a conclusao atual.",
            )
            return

        worker_payload = {
            **payload,
            "cache_enabled": self.config.get("cache_enabled", True),
            "cache_ttl_hours": self.config.get("cache_ttl_hours", 24),
            "force_refresh": False,
        }
        self.progress_screen.reset()
        subtitle = (
            "Gerando ficha do colaborador selecionado."
            if job_type == "ficha"
            else "Gerando carometro com o layout definido."
        )
        badge = "Ficha" if job_type == "ficha" else "Carometro"
        self.progress_screen.set_context("Geracao", subtitle, badge)
        self.navigate_to("progress")
        self._set_generation_busy(True)

        self.current_worker = GenerationWorker(job_type, worker_payload)
        self.current_worker.progress.connect(self.progress_screen.update_progress)
        self.current_worker.log.connect(self.progress_screen.append_log)
        self.current_worker.finished.connect(
            lambda result, jt=job_type: self._handle_worker_finished(jt, result)
        )
        self.current_worker.error.connect(self._handle_worker_error)
        self.current_worker.start()

    def _handle_worker_finished(self, job_type: str, result: dict[str, Any]) -> None:
        self._set_generation_busy(False)
        self.current_worker = None
        self.progress_screen.on_complete(
            result["output_dir"], int(result["count"]), str(result["elapsed"])
        )
        self._stats[job_type] += int(result["count"])
        self._history.insert(0, self._format_history_entry(job_type, result))
        self._history = self._history[:10]
        self.config = settings.update_config(
            {
                "last_generations": self._history,
                "last_cache_sync": (
                    result["source_result"].downloaded_at
                    if result.get("source_result")
                    else self.config.get("last_cache_sync", "")
                ),
            }
        )
        self._refresh_home()

    def _handle_worker_error(self, message: str) -> None:
        self._set_generation_busy(False)
        self.current_worker = None
        self.progress_screen.on_error(message)
        QMessageBox.critical(self, "Erro", message)

    def _format_history_entry(self, job_type: str, result: dict[str, Any]) -> str:
        files = result.get("files", [])
        valid_files = (
            [str(path) for path in files if str(path).strip()]
            if isinstance(files, (list, tuple))
            else []
        )
        if valid_files:
            first_name = Path(valid_files[0]).name
            extra_count = len(valid_files) - 1
            if extra_count > 0:
                return f"{job_type}: {first_name} (+{extra_count})"
            return f"{job_type}: {first_name}"

        return f"{job_type}: {int(result.get('count', 0))} arquivo(s)"

    def _refresh_home(self) -> None:
        self.home_screen.update_stats(self._stats["ficha"], self._stats["carom"])
        self.home_screen.refresh_history(self._history)

    def _save_settings(self, updates: dict[str, Any]) -> None:
        self.config = settings.update_config({**self.config, **updates})
        self.ficha_screen.load_config(self.config)
        self.carom_screen.load_config(self.config)
        self.settings_screen.load_config(self.config)
        QMessageBox.information(self, "Configuracoes", "Configuracoes salvas.")

    def _reset_settings(self) -> None:
        self.config = settings.reset_to_defaults()
        self._history = []
        self._stats = {"ficha": 0, "carom": 0}
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(theme.build_stylesheet(self.config.get("theme", "dark")))
        self.ficha_screen.load_config(self.config)
        self.carom_screen.load_config(self.config)
        self.settings_screen.load_config(self.config)
        self._update_theme_toggle_button()
        QMessageBox.information(self, "Configuracoes", "Padroes restaurados.")

    def _toggle_theme(self) -> None:
        current = str(self.config.get("theme", "dark")).lower()
        new_mode = "light" if current == "dark" else "dark"
        self.config = settings.update_config({**self.config, "theme": new_mode})
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(theme.build_stylesheet(new_mode))
        self.settings_screen.load_config(self.config)
        self._update_theme_toggle_button()

    def _toggle_sidebar(self) -> None:
        if self._sidebar_animation.state() == QAbstractAnimation.State.Running:
            return
        self._sidebar_collapsed = not self._sidebar_collapsed
        self._apply_sidebar_state(animate=True)

    def _on_sidebar_animation_value_changed(self, value: Any) -> None:
        self.sidebar.setMaximumWidth(int(value))

    def _on_sidebar_animation_finished(self) -> None:
        target_width = (
            self._sidebar_collapsed_width
            if self._sidebar_collapsed
            else self._sidebar_expanded_width
        )
        self.sidebar.setMinimumWidth(target_width)
        self.sidebar.setMaximumWidth(target_width)
        self.sidebar_toggle_button.setEnabled(True)

    def _animate_sidebar_width(self, target_width: int) -> None:
        self.sidebar_toggle_button.setEnabled(False)
        self._sidebar_animation.stop()
        self._sidebar_animation.setStartValue(self.sidebar.width())
        self._sidebar_animation.setEndValue(target_width)
        self._sidebar_animation.start()

    def _apply_sidebar_state(self, *, animate: bool = False) -> None:
        collapsed = self._sidebar_collapsed
        target_width = (
            self._sidebar_collapsed_width if collapsed else self._sidebar_expanded_width
        )
        self.sidebar.setProperty("collapsed", "true" if collapsed else "false")
        self.sidebar.setToolTip("Sidebar recolhida" if collapsed else "")
        self.brand_title.setVisible(not collapsed)
        self.brand_subtitle.setVisible(not collapsed)
        self.brand_name_widget.setVisible(not collapsed)
        self.brand_row.setAlignment(
            self.brand_mark,
            (
                Qt.AlignmentFlag.AlignHCenter
                if collapsed
                else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            ),
        )
        self.brand_mark.setProperty("compact", "true" if collapsed else "false")
        self.version_label.setVisible(not collapsed)
        for label in self.nav_labels:
            label.setVisible(not collapsed)
        for button in self.menu_buttons.values():
            button.set_compact(collapsed)
            button.setMinimumHeight(38)
            button.setProperty("sidebarCollapsed", "true" if collapsed else "false")
        self.sidebar_toggle_button.setText("\u25b6" if collapsed else "\u25c0")
        self.sidebar_toggle_button.setToolTip(
            "Expandir menu lateral" if collapsed else "Recolher menu lateral"
        )

        if animate:
            self._animate_sidebar_width(target_width)
        else:
            self._sidebar_animation.stop()
            self.sidebar.setMinimumWidth(target_width)
            self.sidebar.setMaximumWidth(target_width)
            self.sidebar_toggle_button.setEnabled(True)

        widget = self.screens.get(self._current_screen)
        if widget is not None and hasattr(widget, "set_sidebar_collapsed"):
            widget.set_sidebar_collapsed(collapsed)

    def _update_theme_toggle_button(self) -> None:
        current = str(self.config.get("theme", "dark")).lower()
        if current == "dark":
            self.theme_toggle_button.setText("\u2600")
            self.theme_toggle_button.setToolTip("Mudar para modo claro")
        else:
            self.theme_toggle_button.setText("\u263e")
            self.theme_toggle_button.setToolTip("Mudar para modo escuro")

    def _refresh_cache_now(self) -> None:
        url = str(self.config.get("default_onedrive_url", "")).strip()
        if url == "":
            QMessageBox.warning(
                self, "Cache", "Nenhum link padrao do OneDrive configurado."
            )
            return
        try:
            result = resolve_spreadsheet_source(
                url,
                cache_enabled=True,
                cache_ttl_hours=int(self.config.get("cache_ttl_hours", 24)),
                force_refresh=True,
            )
            self.config = settings.update_config(
                {**self.config, "last_cache_sync": result.downloaded_at}
            )
            QMessageBox.information(self, "Cache", result.message)
        except Exception as exc:
            QMessageBox.warning(self, "Cache", str(exc))

    def _open_output_dir(self, output_dir: str) -> None:
        path = os.path.abspath(output_dir)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
