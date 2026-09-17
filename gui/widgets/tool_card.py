from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
                             QLabel, QLineEdit, QPushButton, QFrame, QSpinBox, QComboBox)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from core.tools_db import get_tool_path, is_tool_installed
from gui.widgets.theme_manager import theme_manager

class ToolCardWidget(QFrame):
    run_tool_signal = pyqtSignal(str, dict, str) # tool_key, options_dict, target_val

    def __init__(self, tool_key: str, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_key = tool_key
        self.tool_data = tool_data
        self.is_expanded = False
        self.option_widgets = {}

        t = theme_manager.current_theme
        self.setStyleSheet(f"""
            ToolCardWidget {{
                background-color: rgba(30, 30, 42, 0.90);
                border: 1px solid {t['card_border']};
                border-radius: 8px;
                margin-bottom: 6px;
            }}
            ToolCardWidget:hover {{
                border-color: {t['primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header bar
        header = QHBoxLayout()
        header.setSpacing(8)

        # Enable Checkbox
        self.cb_enable = QCheckBox(tool_data["name"], self)
        self.cb_enable.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.cb_enable.setChecked(True)
        header.addWidget(self.cb_enable)

        # Binary install badge
        installed = is_tool_installed(tool_data["binary"])
        self.lbl_badge = QLabel("[Kali OK]" if installed else "[Не установлен]", self)
        if installed:
            self.lbl_badge.setStyleSheet(f"color: {t['success']}; font-size: 10px; font-weight: bold;")
        else:
            self.lbl_badge.setStyleSheet(f"color: {t['danger']}; font-size: 10px; font-weight: bold;")
        header.addWidget(self.lbl_badge)

        header.addStretch()

        # Expand/Collapse details button - NO FIXED WIDTH to prevent Cyrillic truncation ("одробност")
        self.btn_expand = QPushButton("⚙️ Подробности ▼", self)
        self.btn_expand.setMinimumWidth(130)
        self.btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expand.setStyleSheet(f"padding: 5px 12px; color: {t['text_main']}; font-weight: 600;")
        self.btn_expand.clicked.connect(self._toggle_expand)
        header.addWidget(self.btn_expand)

        layout.addLayout(header)

        # Input field bar
        input_row = QHBoxLayout()
        lbl_target = QLabel(f"{tool_data.get('input_label', 'Цель')}:", self)
        lbl_target.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        lbl_target.setMinimumWidth(110)
        input_row.addWidget(lbl_target)

        self.target_edit = QLineEdit(self)
        self.target_edit.setText(tool_data.get("default_target", ""))
        self.target_edit.setPlaceholderText("Введите цель...")
        input_row.addWidget(self.target_edit)

        # Run single tool button: ICON-ONLY as requested ("кнопку запуск можешь указать иконкой, а не словами")
        self.btn_run_single = QPushButton("▶", self)
        self.btn_run_single.setObjectName("primary_btn")
        self.btn_run_single.setToolTip(f"Запустить только {tool_data['name']}")
        self.btn_run_single.setFixedSize(36, 32)
        self.btn_run_single.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_run_single.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_single.clicked.connect(self._on_run_clicked)
        input_row.addWidget(self.btn_run_single)

        layout.addLayout(input_row)

        # Collapsible details box
        self.details_box = QWidget(self)
        self.details_box.setVisible(False)
        details_layout = QVBoxLayout(self.details_box)
        details_layout.setContentsMargins(5, 5, 5, 5)
        details_layout.setSpacing(6)

        # Description
        lbl_desc = QLabel(f"📖 {tool_data['description']}", self)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {t['text_muted']}; font-style: italic; font-size: 11px;")
        details_layout.addWidget(lbl_desc)

        # Binary path info
        bin_path = get_tool_path(tool_data["binary"])
        lbl_path = QLabel(f"📍 Путь: {bin_path}", self)
        lbl_path.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        details_layout.addWidget(lbl_path)

        # Sudo requirement notice
        if tool_data.get("sudo_recommended"):
            lbl_sudo = QLabel("⚡ Для сканирования рекомендован Root/Sudo (кнопка слева вверху)", self)
            lbl_sudo.setStyleSheet(f"color: {t['primary']}; font-weight: bold; font-size: 10px;")
            details_layout.addWidget(lbl_sudo)

        # Options fields
        opts = tool_data.get("options", [])
        if opts:
            lbl_opts_head = QLabel("Параметры инструмента:", self)
            lbl_opts_head.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            details_layout.addWidget(lbl_opts_head)

            for opt in opts:
                opt_row = QHBoxLayout()
                flag = opt["flag"]
                opt_type = opt.get("type", "bool")
                label_text = opt.get("label", flag)

                if opt_type == "bool":
                    chk = QCheckBox(f"{flag} — {label_text}", self)
                    chk.setChecked(opt.get("default", True))
                    opt_row.addWidget(chk)
                    self.option_widgets[flag] = chk
                elif opt_type == "int":
                    lbl_opt = QLabel(f"{flag} ({label_text}):", self)
                    lbl_opt.setStyleSheet("font-size: 11px;")
                    spn = QSpinBox(self)
                    spn.setRange(1, 65535)
                    spn.setValue(opt.get("default", 10))
                    opt_row.addWidget(lbl_opt)
                    opt_row.addWidget(spn)
                    self.option_widgets[flag] = spn
                elif opt_type == "str":
                    lbl_opt = QLabel(f"{flag} ({label_text}):", self)
                    lbl_opt.setStyleSheet("font-size: 11px;")
                    edt = QLineEdit(self)
                    edt.setText(str(opt.get("default", "")))
                    opt_row.addWidget(lbl_opt)
                    opt_row.addWidget(edt)
                    self.option_widgets[flag] = edt

                details_layout.addLayout(opt_row)

        layout.addWidget(self.details_box)

    def _toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.details_box.setVisible(self.is_expanded)
        self.btn_expand.setText("⚙️ Свернуть ▲" if self.is_expanded else "⚙️ Подробности ▼")

    def is_selected(self) -> bool:
        return self.cb_enable.isChecked()

    def get_target(self) -> str:
        return self.target_edit.text().strip()

    def get_options(self) -> dict:
        result = {}
        for flag, widget in self.option_widgets.items():
            if isinstance(widget, QCheckBox):
                result[flag] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                result[flag] = widget.value()
            elif isinstance(widget, QLineEdit):
                result[flag] = widget.text().strip()
        return result

    def _on_run_clicked(self):
        opts = self.get_options()
        target = self.get_target()
        self.run_tool_signal.emit(self.tool_key, opts, target)
