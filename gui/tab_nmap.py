from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
                             QPushButton, QLineEdit, QLabel, QSplitter)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from core.tools_db import TOOLS_DATABASE
from gui.widgets.tool_card import ToolCardWidget
from gui.widgets.results_console import ResultsConsole
from gui.widgets.theme_manager import theme_manager

class NmapTab(QWidget):
    run_command_signal = pyqtSignal(list, str, object) # command_list, tool_name, target_console

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_cards = {}

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # Splitter between Console and Network Scanners
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 1. Left/Center: Dedicated ResultsConsole for Network Scanners
        self.console = ResultsConsole(self)
        splitter.addWidget(self.console)

        # 2. Right: Network Scanner Cards
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(8)

        lbl_head = QLabel("🌐 Сетевые Сканеры & Nmap", right_panel)
        lbl_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        right_layout.addWidget(lbl_head)

        master_box = QVBoxLayout()
        lbl_master = QLabel("🎯 Единый целевой IP / Подсеть / Домен:", right_panel)
        lbl_master.setStyleSheet("font-weight: bold; font-size: 11px;")
        master_box.addWidget(lbl_master)

        self.master_target_edit = QLineEdit(right_panel)
        self.master_target_edit.setPlaceholderText("127.0.0.1 / 192.168.1.0/24 / example.com")
        master_box.addWidget(self.master_target_edit)

        # Master Actions Row: [⚡ Запустить выбранные] + [☑️] + [☐]
        actions_row = QHBoxLayout()

        self.btn_run_all = QPushButton("⚡ Запустить выбранное", right_panel)
        self.btn_run_all.setObjectName("primary_btn")
        self.btn_run_all.setMinimumHeight(36)
        self.btn_run_all.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.btn_run_all.clicked.connect(self._run_selected_scanners)
        actions_row.addWidget(self.btn_run_all)

        self.btn_select_all = QPushButton("☑️", right_panel)
        self.btn_select_all.setToolTip("Выбрать все сканеры")
        self.btn_select_all.setFixedWidth(36)
        self.btn_select_all.clicked.connect(lambda: self._set_all_selected(True))
        actions_row.addWidget(self.btn_select_all)

        self.btn_unselect_all = QPushButton("☐", right_panel)
        self.btn_unselect_all.setToolTip("Снять выбор со всех")
        self.btn_unselect_all.setFixedWidth(36)
        self.btn_unselect_all.clicked.connect(lambda: self._set_all_selected(False))
        actions_row.addWidget(self.btn_unselect_all)

        master_box.addLayout(actions_row)
        right_layout.addLayout(master_box)

        # Scrollable list of network tool cards
        scroll = QScrollArea(right_panel)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(6)

        for tool_key, tool_data in TOOLS_DATABASE.items():
            if tool_data["category"] == "network":
                card = ToolCardWidget(tool_key, tool_data)
                card.run_tool_signal.connect(self._on_single_tool_run)
                self.tool_cards[tool_key] = card
                scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)

        splitter.addWidget(right_panel)
        splitter.setSizes([650, 450])
        main_layout.addWidget(splitter)

    def _set_all_selected(self, state: bool):
        for card in self.tool_cards.values():
            card.cb_enable.setChecked(state)

    def _on_single_tool_run(self, tool_key: str, opts: dict, target: str):
        tool_data = TOOLS_DATABASE.get(tool_key)
        if not tool_data:
            return
        
        if not target:
            target = self.master_target_edit.text().strip() or tool_data.get("default_target", "")

        cmd = tool_data["cmd_builder"](target, opts, True)
        self.run_command_signal.emit(cmd, tool_data["name"], self.console)

    def _run_selected_scanners(self):
        master_target = self.master_target_edit.text().strip()
        selected_cmds = []

        for tool_key, card in self.tool_cards.items():
            if card.is_selected():
                tool_data = TOOLS_DATABASE[tool_key]
                target = card.get_target() or master_target or tool_data.get("default_target", "")
                opts = card.get_options()
                cmd = tool_data["cmd_builder"](target, opts, True)
                selected_cmds.append((cmd, tool_data["name"]))

        if not selected_cmds:
            self.console.append_output("[!] Не выбрано ни одного сканера сети.\n")
            return

        for cmd, name in selected_cmds:
            self.run_command_signal.emit(cmd, name, self.console)
