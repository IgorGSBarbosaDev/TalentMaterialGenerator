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
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import settings, theme
from app.core.reader import resolve_spreadsheet_source
from app.core.worker import GenerationWorker
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

        self.setWindowTitle("USI Generator")
        self.resize(1200, 760)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 18)
        sidebar_layout.setSpacing(8)
        sidebar_layout.addWidget(QLabel("USIMINAS"))
        subtitle = QLabel("Talent Development")
        subtitle.setObjectName("muted")
        sidebar_layout.addWidget(subtitle)

        self.menu_group = QButtonGroup(self)
        self.menu_group.setExclusive(True)
        self.menu_buttons: dict[str, QPushButton] = {}
        for key, label in (
            ("home", "Home"),
            ("ficha", "Ficha"),
            ("carom", "Carometro"),
            ("progress", "Progresso"),
            ("settings", "Configuracoes"),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setObjectName("menu_item")
            button.clicked.connect(
                lambda checked=False, target=key: self.navigate_to(target)
            )
            self.menu_group.addButton(button)
            self.menu_buttons[key] = button
            sidebar_layout.addWidget(button)
        sidebar_layout.addStretch(1)

        content_root = QWidget()
        content_root.setObjectName("contentRoot")
        content_layout = QVBoxLayout(content_root)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.topbar = QLabel("USI Generator")
        self.topbar.setObjectName("title")
        self.topbar.setMargin(20)
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
        self.settings_screen.save_requested.connect(self._save_settings)
        self.settings_screen.reset_requested.connect(self._reset_settings)
        self.settings_screen.theme_toggle_requested.connect(self._toggle_theme)
        self.settings_screen.refresh_cache_requested.connect(self._refresh_cache_now)

        self._refresh_home()
        self.ficha_screen.load_config(config)
        self.carom_screen.load_config(config)
        self.settings_screen.load_config(config)
        self.navigate_to("home")

    def _set_generation_busy(self, busy: bool) -> None:
        self.ficha_screen.btn_generate.setEnabled(not busy)
        self.carom_screen.btn_generate.setEnabled(not busy)

        for key in ("ficha", "carom"):
            button = self.menu_buttons.get(key)
            if button is not None:
                button.setEnabled(not busy)

    def _has_running_worker(self) -> bool:
        return self.current_worker is not None and self.current_worker.isRunning()

    def navigate_to(self, screen: str) -> None:
        widget = self.screens[screen]
        self.stack.setCurrentWidget(widget)
        self.topbar.setText(widget.__class__.__name__.replace("Screen", ""))
        button = self.menu_buttons.get(screen)
        if button is not None:
            button.setChecked(True)

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
            "Gerando fichas de curriculo..."
            if job_type == "ficha"
            else "Gerando carometro..."
        )
        self.progress_screen.set_context("Progresso", subtitle)
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
        self.progress_screen.append_log(message, "error")
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
        self._refresh_home()
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
