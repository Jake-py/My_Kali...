import math
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton,
                             QDialog, QVBoxLayout, QLineEdit, QMessageBox)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from core.sudo_manager import SudoManager
from gui.widgets.theme_manager import theme_manager

class SudoPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Аутентификация Sudo (Root)")
        self.setFixedSize(360, 180)

        t = theme_manager.current_theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['card_bg']};
                border: 2px solid {t['card_border']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {t['text_main']};
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {t['bg_dark']};
                color: {t['text_main']};
                border: 1px solid {t['primary']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("🛡️ Введите пароль пользователя/sudo:")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("Пароль sudo...")
        layout.addWidget(self.pass_edit)

        btn_box = QHBoxLayout()
        self.btn_ok = QPushButton("Подтвердить")
        self.btn_ok.setObjectName("primary_btn")
        self.btn_cancel = QPushButton("Отмена")

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.pass_edit.returnPressed.connect(self.accept)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_ok)
        layout.addLayout(btn_box)

    def get_password(self) -> str:
        return self.pass_edit.text()


class KaliSudoWidget(QWidget):
    def __init__(self, sudo_manager: SudoManager, parent=None):
        super().__init__(parent)
        self.sudo_mgr = sudo_manager
        self.pulse_phase = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 12, 4)
        layout.setSpacing(10)

        # Kali Icon Button
        self.logo_btn = QPushButton(self)
        self.logo_btn.setFixedSize(42, 42)
        self.logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logo_btn.setToolTip("Нажмите для активации/деактивации Sudo (Root)")

        # Load Kali Logo
        pixmap = QPixmap("assets/kali.webp")
        if pixmap.isNull():
            pixmap = QPixmap("kali.webp")
        
        if not pixmap.isNull():
            self.logo_btn.setIcon(QIcon(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.logo_btn.setIconSize(self.logo_btn.size() - QSize(6, 6))
        else:
            self.logo_btn.setText("KALI")

        self.logo_btn.clicked.connect(self._on_logo_clicked)
        layout.addWidget(self.logo_btn)

        # Text Status Badge
        self.status_btn = QPushButton("SUDO: ВЫКЛ", self)
        self.status_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_btn.setToolTip("Статус прав Root/Sudo. Нажмите для изменения.")
        self.status_btn.clicked.connect(self._on_logo_clicked)
        layout.addWidget(self.status_btn)

        # Connect signals
        self.sudo_mgr.sudo_state_changed.connect(self._update_sudo_ui)

        # Pulse timer (50ms interval for smooth slow pulsing)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._on_pulse_tick)
        self.pulse_timer.start(50)

        self._update_sudo_ui(self.sudo_mgr.is_active, "Инициализация")

    def _on_pulse_tick(self):
        self.pulse_phase += 0.05
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase -= 2 * math.pi
        
        # Calculate pulse intensity (0.4 to 1.0)
        intensity = 0.5 + 0.5 * math.sin(self.pulse_phase)
        
        is_active = self.sudo_mgr.is_active
        if is_active:
            # Slow green pulse (#2ecc71)
            alpha = int(100 + 155 * intensity)
            border_col = f"rgba(46, 204, 113, {intensity:.2f})"
            bg_col = f"rgba(46, 204, 113, 0.25)"
            text_col = "#2ecc71"
        else:
            # Slow red pulse (#e74c3c)
            alpha = int(80 + 100 * intensity)
            border_col = f"rgba(231, 76, 60, {intensity:.2f})"
            bg_col = f"rgba(231, 76, 60, 0.20)"
            text_col = "#e74c3c"

        style = f"""
            QPushButton {{
                background-color: {bg_col};
                border: 2px solid {border_col};
                border-radius: 8px;
                color: {text_col};
                padding: 4px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-width: 3px;
            }}
        """
        self.logo_btn.setStyleSheet(style)
        self.status_btn.setStyleSheet(style)

    def _update_sudo_ui(self, active: bool, msg: str):
        if active:
            if self.sudo_mgr.is_root:
                self.status_btn.setText("⚡ ROOT (Запущен от root)")
            else:
                self.status_btn.setText("🛡️ SUDO: АКТИВЕН")
        else:
            self.status_btn.setText("🔒 SUDO: ВЫКЛ")

    def _on_logo_clicked(self):
        if self.sudo_mgr.is_root:
            QMessageBox.information(self, "Root Права", "Приложение запущено от пользователя root. Все команды выполняются с максимальными правами.")
            return

        if self.sudo_mgr.is_active:
            reply = QMessageBox.question(
                self, "Деактивация Sudo",
                "Вы хотите деактивировать sudo режимы для команд?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.sudo_mgr.deactivate()
        else:
            dlg = SudoPasswordDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                pwd = dlg.get_password()
                if not pwd:
                    QMessageBox.warning(self, "Ошибка", "Пароль не может быть пустым.")
                    return
                ok = self.sudo_mgr.authenticate(pwd)
                if not ok:
                    QMessageBox.critical(self, "Ошибка авторизации", "Введен неверный пароль sudo!")
