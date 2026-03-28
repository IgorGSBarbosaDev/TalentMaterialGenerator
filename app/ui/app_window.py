from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import Qt, QUrl
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
        self.sidebar.setFixedWidth(self._sidebar_expanded_width)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(14)
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
        settings_button = NavButton("Configuracoes", icon_text="S", compact_label="Config")
        settings_button.clicked.connect(lambda _checked=False: self.navigate_to("settings"))
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
        topbar_layout.setContentsMargins(20, 14, 20, 14)
        topbar_layout.setSpacing(12)

        self.sidebar_toggle_button = QPushButton("\u2630")
        self.sidebar_toggle_button.setObjectName("sidebar_toggle")
        self.sidebar_toggle_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_toggle_button.setFixedSize(40, 36)
        self.sidebar_toggle_button.clicked.connect(self._toggle_sidebar)
        topbar_layout.addWidget(self.sidebar_toggle_button)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.topbar_title = QLabel("USI Generator")
        self.topbar_title.setObjectName("title")
        self.topbar_subtitle = QLabel("")
        self.topbar_subtitle.setObjectName("muted")
        self.topbar_subtitle.setWordWrap(True)
        title_col.addWidget(self.topbar_title)
        title_col.addWidget(self.topbar_subtitle)
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
        self.home_screen.settings_requested.connect(lambda: self.navigate_to("settings"))
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
        self.topbar_subtitle.setText(getattr(widget, "page_subtitle", ""))

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
            "Gerando fichas a partir da base."
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
        self._history.insert(0, f"{job_type}: {result['count']} arquivo(s)")
        self._history = self._history[:10]
        self.config = settings.update_config(
            {
                "last_generations": self._history,
                "last_cache_sync": result["source_result"].downloaded_at
                if result.get("source_result")
                else self.config.get("last_cache_sync", ""),
            }
        )
        self._refresh_home()

    def _handle_worker_error(self, message: str) -> None:
        self._set_generation_busy(False)
        self.current_worker = None
        self.progress_screen.on_error(message)
        QMessageBox.critical(self, "Erro", message)

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
        if app is not None:
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
        if app is not None:
            app.setStyleSheet(theme.build_stylesheet(new_mode))
        self.settings_screen.load_config(self.config)
        self._update_theme_toggle_button()

    def _toggle_sidebar(self) -> None:
        self._sidebar_collapsed = not self._sidebar_collapsed
        self._apply_sidebar_state()

    def _apply_sidebar_state(self) -> None:
        collapsed = self._sidebar_collapsed
        self.sidebar.setFixedWidth(
            self._sidebar_collapsed_width if collapsed else self._sidebar_expanded_width
        )
        self.sidebar.setProperty("collapsed", "true" if collapsed else "false")
        self.sidebar.setToolTip("Sidebar recolhida" if collapsed else "")
        self.brand_title.setVisible(not collapsed)
        self.brand_subtitle.setVisible(not collapsed)
        self.brand_name_widget.setVisible(not collapsed)
        self.brand_row.setAlignment(
            self.brand_mark,
            Qt.AlignHCenter if collapsed else Qt.AlignLeft | Qt.AlignVCenter,
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

        widget = self.screens.get(self._current_screen)
        if widget is not None and hasattr(widget, "set_sidebar_collapsed"):
            widget.set_sidebar_collapsed(collapsed)

    def _update_theme_toggle_button(self) -> None:
        current = str(self.config.get("theme", "dark")).lower()
        if current == "dark":
            self.theme_toggle_button.setText("\u2600")
            self.theme_toggle_button.setToolTip("Mudar para modo claro")
        else:
            self.theme_toggle_button.setText("\u263E")
            self.theme_toggle_button.setToolTip("Mudar para modo escuro")

    def _refresh_cache_now(self) -> None:
        url = str(self.config.get("default_onedrive_url", "")).strip()
        if url == "":
            QMessageBox.warning(self, "Cache", "Nenhum link padrao do OneDrive configurado.")
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
