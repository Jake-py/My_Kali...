from PyQt6.QtCore import QObject, pyqtSignal

THEME_ACCENTS = {
    "Kali Cyan (По умолчанию)": {
        "primary": "#00d2ff",
        "primary_hover": "#00b8e6",
        "bg_dark": "#16161d",
        "card_bg": "#20202b",
        "card_border": "#323242",
        "text_main": "#e6e6ef",
        "text_muted": "#9e9eb3",
        "success": "#2ecc71",
        "danger": "#e74c3c"
    },
    "Matrix Green": {
        "primary": "#00e676",
        "primary_hover": "#00c853",
        "bg_dark": "#121915",
        "card_bg": "#1a2520",
        "card_border": "#283830",
        "text_main": "#e8f5e9",
        "text_muted": "#81c784",
        "success": "#00e676",
        "danger": "#ff5252"
    },
    "Red Ice": {
        "primary": "#ff4d4d",
        "primary_hover": "#ff1a1a",
        "bg_dark": "#1a1414",
        "card_bg": "#261d1d",
        "card_border": "#3b2c2c",
        "text_main": "#fce4e4",
        "text_muted": "#e57373",
        "success": "#2ecc71",
        "danger": "#ff4d4d"
    },
    "Cyber Purple": {
        "primary": "#b388ff",
        "primary_hover": "#7c4dff",
        "bg_dark": "#18141f",
        "card_bg": "#231d2e",
        "card_border": "#362c47",
        "text_main": "#f3e5f5",
        "text_muted": "#b39ddb",
        "success": "#00e676",
        "danger": "#ff4081"
    },
    "Amber Gold": {
        "primary": "#ffb74d",
        "primary_hover": "#ffa726",
        "bg_dark": "#1c1813",
        "card_bg": "#29231b",
        "card_border": "#3d3429",
        "text_main": "#fff8e1",
        "text_muted": "#ffe082",
        "success": "#81c784",
        "danger": "#e57373"
    }
}

class ThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._current_theme_name = "Kali Cyan (По умолчанию)"
        self._bg_opacity = 0.85 # Background dimming for red_ice.png

    @property
    def current_theme(self) -> dict:
        return THEME_ACCENTS.get(self._current_theme_name, THEME_ACCENTS["Kali Cyan (По умолчанию)"])

    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name

    def set_theme(self, theme_name: str):
        if theme_name in THEME_ACCENTS:
            self._current_theme_name = theme_name
            self.theme_changed.emit()

    def get_stylesheet(self) -> str:
        t = self.current_theme
        return f"""
        QMainWindow {{
            background-color: {t['bg_dark']};
            color: {t['text_main']};
            font-family: 'Segoe UI', 'DejaVu Sans', 'Liberation Sans', sans-serif;
            font-size: 13px;
        }}
        QWidget {{
            color: {t['text_main']};
            font-family: 'Segoe UI', 'DejaVu Sans', 'Liberation Sans', sans-serif;
        }}
        QTabWidget::pane {{
            border: 1px solid {t['card_border']};
            background-color: rgba(26, 26, 35, 0.92);
            border-radius: 6px;
        }}
        QTabBar::tab {{
            background-color: {t['card_bg']};
            color: {t['text_muted']};
            border: 1px solid {t['card_border']};
            padding: 9px 20px;
            font-weight: bold;
            font-size: 13px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 3px;
        }}
        QTabBar::tab:selected {{
            background-color: {t['primary']};
            color: #0b0c10;
            border-bottom: 2px solid {t['primary']};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {t['card_border']};
            color: {t['text_main']};
        }}
        QGroupBox {{
            background-color: rgba(32, 32, 43, 0.92);
            border: 1px solid {t['card_border']};
            border-radius: 8px;
            margin-top: 12px;
            font-weight: bold;
            padding: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: {t['primary']};
            background-color: {t['card_bg']};
            border-radius: 4px;
        }}
        QPushButton {{
            background-color: {t['card_bg']};
            color: {t['text_main']};
            border: 1px solid {t['card_border']};
            border-radius: 5px;
            padding: 7px 15px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {t['card_border']};
            border-color: {t['primary']};
        }}
        QPushButton:pressed {{
            background-color: {t['primary']};
            color: #000;
        }}
        QPushButton#primary_btn {{
            background-color: {t['primary']};
            color: #0d0e15;
            font-weight: bold;
            border: none;
        }}
        QPushButton#primary_btn:hover {{
            background-color: {t['primary_hover']};
        }}
        QPushButton#danger_btn {{
            background-color: {t['danger']};
            color: #ffffff;
            font-weight: bold;
            border: none;
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
            background-color: rgba(18, 18, 25, 0.95);
            color: {t['text_main']};
            border: 1px solid {t['card_border']};
            border-radius: 5px;
            padding: 6px 10px;
            selection-background-color: {t['primary']};
            selection-color: #000;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid {t['primary']};
        }}
        QCheckBox {{
            spacing: 8px;
            font-weight: 600;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid {t['card_border']};
            background-color: {t['card_bg']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {t['primary']};
            border-color: {t['primary']};
            image: none;
        }}
        QScrollBar:vertical {{
            background: {t['bg_dark']};
            width: 10px;
            margin: 0px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['card_border']};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t['primary']};
        }}
        """

theme_manager = ThemeManager()
