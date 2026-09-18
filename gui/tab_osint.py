from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
                             QPushButton, QLineEdit, QLabel, QSplitter, QTabWidget, QComboBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from core.tools_db import TOOLS_DATABASE
from core.tool_adapter import tool_registry
from core.target_engine import target_engine
from core.recon_profile import ReconLevel
from gui.widgets.tool_card import ToolCardWidget
from gui.widgets.results_console import ResultsConsole
from gui.widgets.theme_manager import theme_manager

class OsintTab(QWidget):
    run_command_signal = pyqtSignal(list, str, object) # command_list, tool_name, target_console

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_cards = {}

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # Splitter between Center (Console) and Right (Tools Sidebar)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 1. Left/Center: Dedicated ResultsConsole for OSINT
        self.console = ResultsConsole(self)
        splitter.addWidget(self.console)

        # 2. Right: OSINT Tools Selector Panel
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(8)

        # Title & Master Target bar
        lbl_head = QLabel("🔍 OSINT Инструменты Разведки", right_panel)
        lbl_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        right_layout.addWidget(lbl_head)

        master_box = QVBoxLayout()
        lbl_master = QLabel("🎯 Единая цель для нескольких инструментов:", right_panel)
        lbl_master.setStyleSheet("font-weight: bold; font-size: 11px;")
        master_box.addWidget(lbl_master)

        self.master_target_edit = QLineEdit(right_panel)
        self.master_target_edit.setPlaceholderText("Имя пользователя / Домен / Email / Файл...")
        self.master_target_edit.textChanged.connect(self._show_target_type)
        master_box.addWidget(self.master_target_edit)

        self.lbl_target_type = QLabel("Тип цели: —", right_panel)
        self.lbl_target_type.setStyleSheet("color: #b8c7d9; font-size: 10px;")
        master_box.addWidget(self.lbl_target_type)

        level_row = QHBoxLayout()
        level_row.addWidget(QLabel("Профиль разведки:", right_panel))
        self.level_combo = QComboBox(right_panel)
        for level in ReconLevel:
            self.level_combo.addItem(level.display_name, level)
        level_row.addWidget(self.level_combo)
        master_box.addLayout(level_row)

        # Master Actions Row: [🚀 Запустить выбранные] + [☑️ Все] + [☐ Снять]
        actions_row = QHBoxLayout()

        self.btn_run_all = QPushButton("🚀 Запустить выбранное", right_panel)
        self.btn_run_all.setObjectName("primary_btn")
        self.btn_run_all.setMinimumHeight(36)
        self.btn_run_all.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.btn_run_all.clicked.connect(self._run_selected_tools)
        actions_row.addWidget(self.btn_run_all)

        self.btn_select_all = QPushButton("☑️", right_panel)
        self.btn_select_all.setToolTip("Выбрать все инструменты")
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

        # Sub-category tabs: [📱 Соц сети, 👤 Аккаунты, 🛠️ Другие, 🌐 Все]
        self.sub_tabs = QTabWidget(right_panel)
        self.sub_categories = [
            ("social", "📱 Соц сети"),
            ("accounts", "👤 Аккаунты"),
            ("other", "🛠️ Другие"),
            ("all", "🌐 Все")
        ]

        for cat_key, cat_label in self.sub_categories:
            scroll = QScrollArea(self.sub_tabs)
            scroll.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setContentsMargins(4, 4, 4, 4)
            scroll_layout.setSpacing(6)

            for tool_key, tool_data in TOOLS_DATABASE.items():
                if tool_data["category"] == "network":
                    continue
                
                if cat_key == "all" or tool_data["category"] == cat_key:
                    if tool_key not in self.tool_cards:
                        card = ToolCardWidget(tool_key, tool_data)
                        card.run_tool_signal.connect(self._on_single_tool_run)
                        self.tool_cards[tool_key] = card
                    else:
                        card = ToolCardWidget(tool_key, tool_data)
                        card.run_tool_signal.connect(self._on_single_tool_run)

                    scroll_layout.addWidget(card)

            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            self.sub_tabs.addTab(scroll, cat_label)

        right_layout.addWidget(self.sub_tabs)
        splitter.addWidget(right_panel)

        # Give 60% space to ResultsConsole, 40% to Tools Panel
        splitter.setSizes([650, 450])
        main_layout.addWidget(splitter)

    def _set_all_selected(self, state: bool):
        for card in self.tool_cards.values():
            card.cb_enable.setChecked(state)

    def _show_target_type(self, value: str):
        target = target_engine.parse(value)
        label = target.target_type.value.upper() if target.is_valid else "НЕ ОПРЕДЕЛЁН"
        self.lbl_target_type.setText(f"Тип цели: {label}")

    def _build_command(self, tool_key: str, target_value: str, options: dict):
        target = target_engine.parse(target_value)
        adapter = tool_registry.get(tool_key)
        if not target.is_valid:
            self.console.append_output(f"[!] {target.errors[0]} Цель: {target_value}\n")
            return None
        if not adapter.supports(target):
            expected = ", ".join(adapter.supported_targets)
            self.console.append_output(
                f"[!] {adapter.name} не поддерживает цель типа {target.target_type.value}. "
                f"Ожидается: {expected}.\n"
            )
            return None
        return adapter.build_command(
            target.normalized_value, options, False, self.level_combo.currentData(),
        )

    def _on_single_tool_run(self, tool_key: str, opts: dict, target: str):
        tool_data = TOOLS_DATABASE.get(tool_key)
        if not tool_data:
            return
        
        if not target:
            target = self.master_target_edit.text().strip() or tool_data.get("default_target", "")

        cmd = self._build_command(tool_key, target, opts)
        if cmd:
            self.run_command_signal.emit(cmd, tool_data["name"], self.console)

    def _run_selected_tools(self):
        master_target = self.master_target_edit.text().strip()
        selected_cmds = []

        for tool_key, card in self.tool_cards.items():
            if card.is_selected():
                tool_data = TOOLS_DATABASE[tool_key]
                target = card.get_target() or master_target or tool_data.get("default_target", "")
                opts = card.get_options()
                cmd = self._build_command(tool_key, target, opts)
                if cmd:
                    selected_cmds.append((cmd, tool_data["name"]))

        if not selected_cmds:
            self.console.append_output("[!] Не выбрано ни одного инструмента для запуска.\n")
            return

        for cmd, name in selected_cmds:
            self.run_command_signal.emit(cmd, name, self.console)
