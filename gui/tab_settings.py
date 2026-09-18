from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QSlider, QGroupBox, QPushButton, QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from gui.widgets.theme_manager import theme_manager, THEME_ACCENTS
from core.tool_adapter import ToolState, tool_registry

class SettingsTab(QWidget):
    wallpaper_opacity_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        lbl_head = QLabel("⚙️ Настройки Оформления & Параметры Kali OSINT", self)
        lbl_head.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_head)

        # Theme Groupbox
        box_theme = QGroupBox("🎨 Цветовая Схема и Стиль (about_gui.txt)", self)
        theme_layout = QVBoxLayout(box_theme)
        theme_layout.setSpacing(10)

        theme_row = QHBoxLayout()
        lbl_theme = QLabel("Выберите цветовую акцентную схему:", self)
        lbl_theme.setFont(QFont("Segoe UI", 10))
        theme_row.addWidget(lbl_theme)

        self.cb_themes = QComboBox(self)
        self.cb_themes.addItems(list(THEME_ACCENTS.keys()))
        self.cb_themes.setCurrentText(theme_manager.current_theme_name)
        self.cb_themes.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.cb_themes)

        theme_layout.addLayout(theme_row)

        # Wallpaper Opacity Slider
        opacity_row = QHBoxLayout()
        lbl_opacity = QLabel("Прозрачность обоев (red_ice.png):", self)
        opacity_row.addWidget(lbl_opacity)

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_opacity.setRange(10, 100)
        self.slider_opacity.setValue(85)
        self.slider_opacity.valueChanged.connect(self._on_slider_changed)
        opacity_row.addWidget(self.slider_opacity)

        self.lbl_opacity_val = QLabel("85%", self)
        opacity_row.addWidget(self.lbl_opacity_val)

        theme_layout.addLayout(opacity_row)
        layout.addWidget(box_theme)

        # Tools Installed Audit Groupbox
        box_tools = QGroupBox("📍 Статус и Пути Исполняемых Бинарников Kali", self)
        tools_layout = QVBoxLayout(box_tools)
        tools_layout.setSpacing(6)

        for adapter, health in tool_registry.audit(include_version=True):
            row = QHBoxLayout()
            lbl_name = QLabel(f"• {adapter.name}:", self)
            lbl_name.setFixedWidth(140)
            lbl_name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            row.addWidget(lbl_name)

            if health.state == ToolState.READY:
                version = f" — {health.version}" if health.version else ""
                path_str = f"✓ Ready{version}\n{health.path}"
            elif health.state == ToolState.NOT_CONFIGURED:
                path_str = f"⚠ API не настроен: {health.detail}"
            else:
                path_str = f"✗ Missing: {adapter.binary}"
            lbl_p = QLabel(path_str, self)
            lbl_p.setWordWrap(True)
            if health.state != ToolState.READY:
                lbl_p.setStyleSheet("color: #e74c3c; font-style: italic;")
            else:
                lbl_p.setStyleSheet("color: #2ecc71; font-family: monospace;")
            row.addWidget(lbl_p)

            tools_layout.addLayout(row)

        layout.addWidget(box_tools)
        layout.addStretch()

    def _on_theme_changed(self, theme_name: str):
        theme_manager.set_theme(theme_name)

    def _on_slider_changed(self, value: int):
        self.lbl_opacity_val.setText(f"{value}%")
        self.wallpaper_opacity_changed.emit(value / 100.0)
