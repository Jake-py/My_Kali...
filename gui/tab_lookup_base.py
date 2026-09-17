from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
                             QPushButton, QLineEdit, QLabel, QSplitter, QGroupBox, QFrame)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from gui.widgets.results_console import ResultsConsole
from gui.widgets.theme_manager import theme_manager
from core.leakcheck_adapter import leakcheck_adapter

class LookUpBaseTab(QWidget):
    run_leakcheck_signal = pyqtSignal(str, object) # query, target_console

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 1. Left/Center: Dedicated Console for LookUp Base
        self.console = ResultsConsole(self)
        splitter.addWidget(self.console)

        # 2. Right: Search Panel
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(10)

        # Header bar
        header_row = QHBoxLayout()
        lbl_head = QLabel("🔍 LookUp Base — Проверка Утечек Данных", right_panel)
        lbl_head.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header_row.addWidget(lbl_head)

        lbl_status_badge = QLabel("[Online] LeakCheck API", right_panel)
        t = theme_manager.current_theme
        lbl_status_badge.setStyleSheet(f"color: {t['success']}; font-weight: bold; font-size: 10px; background-color: rgba(46, 204, 113, 0.15); padding: 3px 8px; border-radius: 4px;")
        header_row.addWidget(lbl_status_badge)

        right_layout.addLayout(header_row)

        # Main Query Box
        query_box = QGroupBox("🎯 Быстрая проверка идентификатора на компрометацию", right_panel)
        box_layout = QVBoxLayout(query_box)
        box_layout.setSpacing(10)

        lbl_hint = QLabel("Поддерживается: Email (user@domain.com), Юзернейм (от 3 симв.), SHA256 хеш (24+ симв.)", query_box)
        lbl_hint.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        box_layout.addWidget(lbl_hint)

        input_row = QHBoxLayout()
        self.target_edit = QLineEdit(query_box)
        self.target_edit.setPlaceholderText("например: test@example.com или target_user")
        self.target_edit.setText("test@example.com")
        self.target_edit.returnPressed.connect(self._run_lookup)
        input_row.addWidget(self.target_edit)

        self.btn_search = QPushButton("🚀 Поиск", query_box)
        self.btn_search.setObjectName("primary_btn")
        self.btn_search.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.btn_search.clicked.connect(self._run_lookup)
        input_row.addWidget(self.btn_search)

        box_layout.addLayout(input_row)

        # Quick Test Presets
        lbl_preset = QLabel("Быстрые тесты сценариев:", query_box)
        lbl_preset.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        box_layout.addWidget(lbl_preset)

        preset_row = QHBoxLayout()
        
        btn_preset_dirty = QPushButton("⚠️ Тест: Утечки найдена", query_box)
        btn_preset_dirty.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        btn_preset_dirty.clicked.connect(lambda: self._set_and_run("test@example.com"))
        preset_row.addWidget(btn_preset_dirty)

        btn_preset_clean = QPushButton("✅ Тест: Чистый Email", query_box)
        btn_preset_clean.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        btn_preset_clean.clicked.connect(lambda: self._set_and_run("clean_user_nonexistent_999@domain.com"))
        preset_row.addWidget(btn_preset_clean)

        box_layout.addLayout(preset_row)
        right_layout.addWidget(query_box)

        # Intelligence Info Card
        info_card = QFrame(right_panel)
        info_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(32, 32, 44, 0.90);
                border: 1px solid {t['card_border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(6)

        lbl_info_title = QLabel("ℹ️ О сервисе LeakCheck Public API:", info_card)
        lbl_info_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_info_title.setStyleSheet(f"color: {t['primary']};")
        info_layout.addWidget(lbl_info_title)

        info_text = (
            "• **Без ключей и регистрации**: Открытый API для проверки факта утечки.\n"
            "• **Приватность**: Можно передавать SHA256-хеш email (обрезанный до 24 симв.), не раскрывая открытый адрес.\n"
            "• **Rate-Limit**: Запросы автоматически лимитируются до 1 req/sec для соблюдения условий сервиса.\n"
            "• **Подсветка рисков**: Пароли, скомпрометированные в базах, автоматически выделяются красным сигнализатором."
        )
        lbl_info_body = QLabel(info_text, info_card)
        lbl_info_body.setWordWrap(True)
        lbl_info_body.setStyleSheet(f"color: {t['text_main']}; font-size: 11px;")
        info_layout.addWidget(lbl_info_body)

        right_layout.addWidget(info_card)
        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([650, 450])
        main_layout.addWidget(splitter)

    def _set_and_run(self, query: str):
        self.target_edit.setText(query)
        self._run_lookup()

    def _run_lookup(self):
        query = self.target_edit.text().strip()
        if not query:
            return
        self.run_leakcheck_signal.emit(query, self.console)
