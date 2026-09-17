import re
import html
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLineEdit, QLabel, QFileDialog, QMessageBox, QComboBox)
from PyQt6.QtGui import QFont, QTextCursor, QColor
from PyQt6.QtCore import Qt
from gui.widgets.theme_manager import theme_manager

class ResultsConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Header bar
        header = QHBoxLayout()
        header.setSpacing(8)

        lbl_title = QLabel("📊 Результаты & Логи Выполнения", self)
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header.addWidget(lbl_title)

        # Status badge
        self.lbl_status = QLabel("Статус: Готов", self)
        self.lbl_status.setStyleSheet("color: #9e9eb3; font-weight: bold; font-size: 11px;")
        header.addWidget(self.lbl_status)

        header.addStretch()

        # Search box
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("🔍 Поиск в результатах...")
        self.search_edit.setFixedWidth(180)
        self.search_edit.textChanged.connect(self._filter_text)
        header.addWidget(self.search_edit)

        # Action Buttons
        self.btn_copy = QPushButton("📋 Копировать", self)
        self.btn_copy.clicked.connect(self._copy_output)
        header.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Сохранить Отчет", self)
        self.btn_save.setObjectName("primary_btn")
        self.btn_save.clicked.connect(self._save_report)
        header.addWidget(self.btn_save)

        self.btn_clear = QPushButton("🗑️ Очистить", self)
        self.btn_clear.clicked.connect(self.clear_console)
        header.addWidget(self.btn_clear)

        layout.addLayout(header)

        # Main Text Console
        self.console = QTextEdit(self)
        self.console.setReadOnly(True)
        self.console.setFont(QFont("DejaVu Sans Mono", 10))
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Enable dark theme for console
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)

        layout.addWidget(self.console)

        # Footer statistics bar
        footer = QHBoxLayout()
        self.lbl_lines = QLabel("Строк: 0", self)
        self.lbl_lines.setStyleSheet("color: #9e9eb3; font-size: 11px;")
        footer.addWidget(self.lbl_lines)

        footer.addStretch()

        self.cb_autoscroll = QPushButton("⬇️ Автопрокрутка: ВКЛ", self)
        self.cb_autoscroll.setCheckable(True)
        self.cb_autoscroll.setChecked(True)
        self.cb_autoscroll.toggled.connect(self._toggle_autoscroll)
        footer.addWidget(self.cb_autoscroll)

        layout.addLayout(footer)

        self.raw_logs = []

    def _apply_theme(self):
        t = theme_manager.current_theme
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(14, 14, 20, 0.95);
                color: #00ff66;
                border: 1px solid {t['card_border']};
                border-radius: 6px;
                padding: 10px;
                selection-background-color: {t['primary']};
                selection-color: #000;
            }}
        """)

    def set_status(self, status_text: str, is_running: bool = False):
        t = theme_manager.current_theme
        if is_running:
            self.lbl_status.setText(f"⏳ {status_text}")
            self.lbl_status.setStyleSheet(f"color: {t['primary']}; font-weight: bold;")
        else:
            self.lbl_status.setText(f"✅ {status_text}")
            self.lbl_status.setStyleSheet(f"color: {t['success']}; font-weight: bold;")

    def append_output(self, text: str):
        self.raw_logs.append(text)
        
        # Color formatting for terminal lines
        formatted_html = self._format_terminal_line(text)
        
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(formatted_html)
        
        if self.cb_autoscroll.isChecked():
            self.console.ensureCursorVisible()

        lines_count = len(self.console.toPlainText().splitlines())
        self.lbl_lines.setText(f"Строк: {lines_count}")

    def _format_terminal_line(self, text: str) -> str:
        escaped = html.escape(text)
        
        # Highlighting common OSINT keywords
        escaped = re.sub(r'(\[\+\])', r'<span style="color:#00e676;font-weight:bold;">\1</span>', escaped)
        escaped = re.sub(r'(\[\*\])', r'<span style="color:#00d2ff;font-weight:bold;">\1</span>', escaped)
        escaped = re.sub(r'(\[\!\]|ERROR|CRITICAL|FAIL)', r'<span style="color:#ff4d4d;font-weight:bold;">\1</span>', escaped)
        escaped = re.sub(r'(FOUND|Found|Open|OPEN|SUCCESS|State: open)', r'<span style="color:#00ff66;font-weight:bold;">\1</span>', escaped)
        escaped = re.sub(r'(http[s]?://\S+)', r'<span style="color:#00d2ff;text-decoration:underline;">\1</span>', escaped)
        escaped = re.sub(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', r'<span style="color:#ffb74d;font-weight:bold;">\1</span>', escaped)
        
        # Replace newlines with <br>
        escaped = escaped.replace('\n', '<br>')
        return f'<span style="font-family:DejaVu Sans Mono, monospace; font-size:12px;">{escaped}</span>'

    def clear_console(self):
        self.console.clear()
        self.raw_logs.clear()
        self.lbl_lines.setText("Строк: 0")
        self.set_status("Очищено")

    def _copy_output(self):
        self.console.selectAll()
        self.console.copy()
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
        QMessageBox.information(self, "Скопировано", "Результаты скопированы в буфер обмена!")

    def _save_report(self):
        content = "".join(self.raw_logs)
        if not content.strip():
            QMessageBox.warning(self, "Пустой отчет", "Нет данных для сохранения.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет OSINT", "osint_report.html", "HTML Files (*.html);;Text Files (*.txt)"
        )
        if filepath:
            try:
                if filepath.endswith(".html"):
                    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OSINT & Network Recon Report</title>
    <style>
        body {{ background-color: #121216; color: #00ff66; font-family: monospace; padding: 20px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
        h1 {{ color: #00d2ff; border-bottom: 1px solid #333; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <h1>🛡️ OSINT Kali Framework Report</h1>
    <pre>{html.escape(content)}</pre>
</body>
</html>"""
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)
                else:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                QMessageBox.information(self, "Успешно", f"Отчет успешно сохранен в:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить отчет: {str(e)}")

    def _filter_text(self, query: str):
        if not query:
            return
        # Simple text find highlight
        self.console.find(query)

    def _toggle_autoscroll(self, checked: bool):
        if checked:
            self.cb_autoscroll.setText("⬇️ Автопрокрутка: ВКЛ")
        else:
            self.cb_autoscroll.setText("⏸️ Автопрокрутка: ВЫКЛ")
