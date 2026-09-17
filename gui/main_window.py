import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QPushButton, QMessageBox)
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QThread
from core.sudo_manager import SudoManager
from core.tool_runner import CommandWorker
from core.leakcheck_worker import LeakCheckWorker
from gui.widgets.theme_manager import theme_manager
from gui.widgets.kali_sudo_widget import KaliSudoWidget
from gui.widgets.results_console import ResultsConsole
from gui.tab_osint import OsintTab
from gui.tab_nmap import NmapTab
from gui.tab_lookup_base import LookUpBaseTab
from gui.tab_future import FutureTab
from gui.tab_settings import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RED Kali | RED ICE")
        self.resize(1420, 880)
        self.setMinimumSize(1024, 720)

        # Core Managers
        self.sudo_mgr = SudoManager()
        self.current_worker = None
        self.worker_thread = None
        self.active_console = None
        self.wallpaper_opacity = 0.85

        # Background Pixmap (red_ice.png)
        self.bg_pixmap = QPixmap("assets/red_ice.png")
        if self.bg_pixmap.isNull():
            self.bg_pixmap = QPixmap("red_ice.png")

        # Window Icon
        icon_pixmap = QPixmap("assets/kali.webp")
        if not icon_pixmap.isNull():
            self.setWindowIcon(QIcon(icon_pixmap))

        # Central Container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(6)

        # Top Bar Layout: [Kali Logo & Sudo Indicator] | Title | [Stop Button]
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(2, 2, 2, 2)
        top_bar.setSpacing(10)

        # 1. Top-Left Kali Logo & Sudo Status
        self.sudo_widget = KaliSudoWidget(self.sudo_mgr, self)
        top_bar.addWidget(self.sudo_widget)

        # 2. Application name and author
        lbl_app_title = QLabel("🛡️ RED Kali", self)
        lbl_app_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        top_bar.addWidget(lbl_app_title)

        lbl_author = QLabel("Автор: RED ICE", self)
        lbl_author.setFont(QFont("Segoe UI", 10))
        lbl_author.setStyleSheet("color: #b8c7d9;")
        top_bar.addWidget(lbl_author)

        top_bar.addStretch()

        # Stop Process Button
        self.btn_stop = QPushButton("🛑 Остановить Процесс", self)
        self.btn_stop.setObjectName("danger_btn")
        self.btn_stop.setStyleSheet("padding: 6px 14px; font-weight: bold;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_current_process)
        top_bar.addWidget(self.btn_stop)

        main_layout.addLayout(top_bar)

        # Main Navigation Tabs: [OSINT | Nmap | LookUp Base | __ | Настройки]
        self.tabs = QTabWidget(self)
        self.tabs.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        # Tab 1: OSINT
        self.tab_osint = OsintTab(self)
        self.tab_osint.run_command_signal.connect(self._execute_command)
        self.tabs.addTab(self.tab_osint, "🔍 OSINT")

        # Tab 2: Nmap
        self.tab_nmap = NmapTab(self)
        self.tab_nmap.run_command_signal.connect(self._execute_command)
        self.tabs.addTab(self.tab_nmap, "🌐 Nmap")

        # Tab 3: LookUp Base (NEW TAB as requested in base.txt)
        self.tab_lookup = LookUpBaseTab(self)
        self.tab_lookup.run_leakcheck_signal.connect(self._execute_leakcheck)
        self.tabs.addTab(self.tab_lookup, "🔍 LookUp Base")

        # Tab 4: __ (Future expansion)
        self.tab_future = FutureTab(self)
        self.tab_future.run_command_signal.connect(self._execute_command)
        self.tabs.addTab(self.tab_future, "   __   ")

        # Tab 5: Settings
        self.tab_settings = SettingsTab(self)
        self.tab_settings.wallpaper_opacity_changed.connect(self._on_opacity_changed)
        self.tabs.addTab(self.tab_settings, "⚙️ Настройки")

        main_layout.addWidget(self.tabs)

        # Apply Global Theme Stylesheet
        self._apply_global_stylesheet()
        theme_manager.theme_changed.connect(self._apply_global_stylesheet)

        # Log initial welcome status
        init_console = self.tab_osint.console
        init_console.append_output("========================================================\n")
        init_console.append_output("🛡️ RED Kali готов к работе. Автор: RED ICE.\n")
        init_console.append_output("📍 Подключена вкладка 'LookUp Base' (LeakCheck Public API).\n")
        init_console.append_output("⚡ Нажмите значок Kali слева вверху для авторизации Root/Sudo.\n")
        init_console.append_output("========================================================\n\n")

    def _apply_global_stylesheet(self):
        self.setStyleSheet(theme_manager.get_stylesheet())

    def paintEvent(self, event):
        """Draw red_ice.png background wallpaper with dark overlay."""
        painter = QPainter(self)
        t = theme_manager.current_theme
        bg_color = QColor(t['bg_dark'])

        if not self.bg_pixmap.isNull():
            scaled_bg = self.bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_bg)

            dark_alpha = int(self.wallpaper_opacity * 255)
            tint = QColor(bg_color.red(), bg_color.green(), bg_color.blue(), dark_alpha)
            painter.fillRect(self.rect(), tint)
        else:
            painter.fillRect(self.rect(), bg_color)

    def _on_opacity_changed(self, val: float):
        self.wallpaper_opacity = val
        self.update()

    def _execute_command(self, cmd_list: list, tool_name: str, target_console: ResultsConsole):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Выполнение", "Уже запущен другой процесс. Дождитесь завершения или остановите его.")
            return

        self.active_console = target_console or self.tab_osint.console
        final_cmd = self.sudo_mgr.wrap_command(cmd_list)

        self.btn_stop.setEnabled(True)
        self.active_console.set_status(f"Выполняется: {tool_name}", is_running=True)

        self.worker_thread = QThread(self)
        self.current_worker = CommandWorker(final_cmd, self.sudo_mgr.password)
        self.current_worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.current_worker.run)
        self.current_worker.output_signal.connect(self.active_console.append_output)
        self.current_worker.finished_signal.connect(self._on_worker_finished)

        self.worker_thread.start()

    def _execute_leakcheck(self, query: str, target_console: ResultsConsole):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Выполнение", "Уже запущен другой процесс. Дождитесь завершения или остановите его.")
            return

        self.active_console = target_console or self.tab_lookup.console
        self.btn_stop.setEnabled(True)
        self.active_console.set_status(f"Поиск утечек: {query}", is_running=True)

        self.worker_thread = QThread(self)
        self.current_worker = LeakCheckWorker(query)
        self.current_worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.current_worker.run)
        self.current_worker.output_signal.connect(self.active_console.append_output)
        self.current_worker.finished_signal.connect(self._on_worker_finished)

        self.worker_thread.start()

    def _on_worker_finished(self, exit_code: int, duration: float):
        self.btn_stop.setEnabled(False)
        if self.active_console:
            self.active_console.set_status(f"Завершено ({duration:.2f}с)", is_running=False)

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
            self.current_worker = None
            self.active_console = None

    def _stop_current_process(self):
        if self.current_worker:
            if hasattr(self.current_worker, "cancel"):
                self.current_worker.cancel()
            if self.active_console:
                self.active_console.append_output("\n[!] Отправка сигнала остановки...\n")
