from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QGroupBox, QSplitter)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from gui.widgets.results_console import ResultsConsole
from gui.widgets.theme_manager import theme_manager

class FutureTab(QWidget):
    run_command_signal = pyqtSignal(list, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 1. Dedicated Console
        self.console = ResultsConsole(self)
        splitter.addWidget(self.console)

        # 2. Right control panel
        right_panel = QWidget(self)
        layout = QVBoxLayout(right_panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        lbl_title = QLabel("🔮 Зарезервированная Вкладка: __ (Плагины)", self)
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        t = theme_manager.current_theme
        lbl_title.setStyleSheet(f"color: {t['primary']};")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Вкладка создан по спецификации about_gui.txt для выполнения производных команд или скриптов Kali Linux.",
            self
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {t['text_muted']}; font-size: 12px;")
        layout.addWidget(lbl_desc)

        # Custom command groupbox
        box = QGroupBox("💻 Произвольная команда Kali", self)
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(10)

        cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit(self)
        self.cmd_input.setPlaceholderText("Например: python3 --version или whois google.com")
        self.cmd_input.returnPressed.connect(self._run_custom_command)
        cmd_row.addWidget(self.cmd_input)

        self.btn_run = QPushButton("▶", self)
        self.btn_run.setObjectName("primary_btn")
        self.btn_run.setToolTip("Запустить команду")
        self.btn_run.setFixedSize(36, 32)
        self.btn_run.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_run.clicked.connect(self._run_custom_command)
        cmd_row.addWidget(self.btn_run)

        box_layout.addLayout(cmd_row)
        layout.addWidget(box)

        # Quick preset script buttons
        box_presets = QGroupBox("⚡ Проверки Kali OSINT", self)
        presets_layout = QVBoxLayout(box_presets)

        btn_chk_tools = QPushButton("🔍 Проверить установленные бинарники", self)
        btn_chk_tools.setStyleSheet("padding: 6px 12px;")
        btn_chk_tools.clicked.connect(lambda: self._run_preset(["which", "nmap", "theHarvester", "sherlock", "exiftool", "spiderfoot"], "Проверка бинарников"))
        presets_layout.addWidget(btn_chk_tools)

        btn_chk_ip = QPushButton("🌐 Проверить внешний IP", self)
        btn_chk_ip.setStyleSheet("padding: 6px 12px;")
        btn_chk_ip.clicked.connect(lambda: self._run_preset(["curl", "-s", "https://ifconfig.me"], "Проверка IP"))
        presets_layout.addWidget(btn_chk_ip)

        btn_chk_sys = QPushButton("ℹ️ Информация о системе Kali", self)
        btn_chk_sys.setStyleSheet("padding: 6px 12px;")
        btn_chk_sys.clicked.connect(lambda: self._run_preset(["uname", "-a"], "Информация о системе"))
        presets_layout.addWidget(btn_chk_sys)

        layout.addWidget(box_presets)
        layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([650, 450])
        main_layout.addWidget(splitter)

    def _run_custom_command(self):
        raw = self.cmd_input.text().strip()
        if not raw:
            return
        cmd = raw.split()
        self.run_command_signal.emit(cmd, f"Кастомная команда: {raw}", self.console)

    def _run_preset(self, cmd: list, name: str):
        self.run_command_signal.emit(cmd, name, self.console)
