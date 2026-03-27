from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
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

        self.setWindowTitle("USI Generator")
        self.resize(1320, 820)
        self.setMinimumSize(1180, 760)

        root = QFrame()
        root.setObjectName("appShell")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(248)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(14)

        brand_row = QHBoxLayout()
        brand_mark = QLabel("U")
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(48, 48)
        brand_name_col = QVBoxLayout()
        brand_name_col.setSpacing(1)
        brand_title = QLabel("USIMINAS")
        brand_title.setObjectName("brandTitle")
        brand_subtitle = QLabel("Talent Development")
        brand_subtitle.setObjectName("brandSubtitle")
        brand_name_col.addWidget(brand_title)
        brand_name_col.addWidget(brand_subtitle)
        brand_row.addWidget(brand_mark)
        brand_row.addLayout(brand_name_col, 1)
        sidebar_layout.addLayout(brand_row)

        intro = QLabel(
            "Geracao guiada de fichas e carometros com preview persistente e feedback visual."
        )
        intro.setObjectName("bodyMuted")
        intro.setWordWrap(True)
        sidebar_layout.addWidget(intro)

        sidebar_layout.addWidget(self._build_nav_label("Principal"))
        self.menu_group = QButtonGroup(self)
        self.menu_group.setExclusive(True)
        self.menu_buttons: dict[str, NavButton] = {}
        for key, label in (
            ("home", "Inicio"),
            ("ficha", "Ficha de curriculo"),
            ("carom", "Carometro"),
            ("progress", "Geracao"),
        ):
            button = NavButton(label)
            button.clicked.connect(
                lambda _checked=False, target=key: self.navigate_to(target)
            )
            self.menu_group.addButton(button)
            self.menu_buttons[key] = button
            sidebar_layout.addWidget(button)

        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(self._build_nav_label("Sistema"))
        settings_button = NavButton("Configuracoes")
        settings_button.clicked.connect(lambda _checked=False: self.navigate_to("settings"))
        self.menu_group.addButton(settings_button)
        self.menu_buttons["settings"] = settings_button
        sidebar_layout.addWidget(settings_button)
        sidebar_layout.addStretch(1)

        version = QLabel("v1.0.0  |  UI refresh PySide6")
        version.setObjectName("muted")
        version.setWordWrap(True)
        sidebar_layout.addWidget(version)

        content_root = QWidget()
        content_root.setObjectName("contentRoot")
        content_layout = QVBoxLayout(content_root)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.topbar = QFrame()
        self.topbar.setObjectName("topbar")
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(26, 18, 26, 18)
        topbar_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.topbar_title = QLabel("Inicio")
        self.topbar_title.setObjectName("topbarTitle")
        self.topbar_subtitle = QLabel("Painel principal do USI Generator")
        self.topbar_subtitle.setObjectName("topbarSubtitle")
        title_col.addWidget(self.topbar_title)
        title_col.addWidget(self.topbar_subtitle)
        topbar_layout.addLayout(title_col, 1)

        self.topbar_badge = QLabel("Dashboard")
        self.topbar_badge.setObjectName("topbarBadge")
        topbar_layout.addWidget(self.topbar_badge)
        content_layout.addWidget(self.topbar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(sidebar)
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
        self.settings_screen.theme_toggle_requested.connect(self._toggle_theme)
        self.settings_screen.refresh_cache_requested.connect(self._refresh_cache_now)

        self._refresh_home()
        self.ficha_screen.load_config(config)
        self.carom_screen.load_config(config)
        self.settings_screen.load_config(config)
        self.navigate_to("home")

    def _build_nav_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("navSectionLabel")
        return label

    def navigate_to(self, screen: str) -> None:
        widget = self.screens[screen]
        self._current_screen = screen
        self.stack.setCurrentWidget(widget)
        button = self.menu_buttons.get(screen)
        if button is not None:
            button.setChecked(True)
        self._sync_topbar()

    def _sync_topbar(self) -> None:
        widget = self.screens[self._current_screen]
        self.topbar_title.setText(getattr(widget, "page_title", "USI Generator"))
        self.topbar_subtitle.setText(getattr(widget, "page_subtitle", ""))
        badge = getattr(widget, "page_badge", "")
        self.topbar_badge.setText(badge)
        self.topbar_badge.setVisible(bool(badge))

    def _start_generation(self, job_type: str, payload: dict[str, Any]) -> None:
        worker_payload = {
            **payload,
            "cache_enabled": self.config.get("cache_enabled", True),
            "cache_ttl_hours": self.config.get("cache_ttl_hours", 24),
            "force_refresh": False,
        }
        self.progress_screen.reset()
        subtitle = (
            "Gerando fichas de curriculo a partir da base selecionada."
            if job_type == "ficha"
            else "Gerando carometro com agrupamento e layout configurados."
        )
        badge = "Ficha" if job_type == "ficha" else "Carometro"
        self.progress_screen.set_context("Geracao", subtitle, badge)
        self.navigate_to("progress")

        self.current_worker = GenerationWorker(job_type, worker_payload)
        self.current_worker.progress.connect(self.progress_screen.update_progress)
        self.current_worker.log.connect(self.progress_screen.append_log)
        self.current_worker.finished.connect(
            lambda result, jt=job_type: self._handle_worker_finished(jt, result)
        )
        self.current_worker.error.connect(self._handle_worker_error)
        self.current_worker.start()

    def _handle_worker_finished(self, job_type: str, result: dict[str, Any]) -> None:
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
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_stylesheet(self.config.get("theme", "dark")))
        self.ficha_screen.load_config(self.config)
        self.carom_screen.load_config(self.config)
        self.settings_screen.load_config(self.config)
        QMessageBox.information(self, "Configuracoes", "Padroes restaurados.")

    def _toggle_theme(self) -> None:
        current = str(self.config.get("theme", "dark")).lower()
        new_mode = "light" if current == "dark" else "dark"
        self.config = settings.update_config({**self.config, "theme": new_mode})
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_stylesheet(new_mode))
        self.settings_screen.load_config(self.config)

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
