"""
Design system, theme tokens, QSS styling, and animated widgets for OnesDev POS.
Unified Deep Royal Blue premium business theme with iOS-inspired physics.
"""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QPushButton, QFrame, QLabel, QGraphicsDropShadowEffect,
    QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
)
from PySide6.QtGui import QColor, QFont, QCursor

COLORS = {
    # App shell & surfaces
    "bg_main": "#F1F5F9",
    "bg_surface": "#FFFFFF",
    "bg_surface_raised": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "bg_hover": "#F1F5F9",
    "bg_input": "#F8FAFC",

    # Sidebar: Deep Navy
    "bg_sidebar": "#0F172A",
    "sidebar_text": "#94A3B8",
    "sidebar_hover": "#1E293B",
    "sidebar_active_bg": "#1E293B",
    "sidebar_active_text": "#FFFFFF",
    "sidebar_indicator": "#3B82F6",

    # Borders & Dividers
    "border": "#E2E8F0",
    "border_subtle": "#F1F5F9",
    "border_focus": "#2563EB",

    # Typography
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "text_on_dark": "#F8FAFC",
    "text_on_primary": "#FFFFFF",

    # Primary: Deep Royal Blue
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_subtle": "#EFF6FF",

    # Semantic
    "success": "#059669",
    "success_hover": "#047857",
    "success_subtle": "#ECFDF5",
    "warning": "#D97706",
    "warning_hover": "#B45309",
    "warning_subtle": "#FFFBEB",
    "danger": "#DC2626",
    "danger_hover": "#B91C1C",
    "danger_subtle": "#FEF2F2",
    "border_error": "#EF4444",
    "bg_error": "#FEF2F2",
    "text_error": "#DC2626",
    "gold": "#D97706",
    "info": "#0284C7",
    "info_subtle": "#F0F9FF",
}

GLOBAL_QSS = f"""
* {{
    font-family: 'Segoe UI', 'Segoe UI Emoji', 'Segoe UI Symbol', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    outline: none;
}}

QWidget {{
    color: {COLORS["text_primary"]};
}}

QDialog {{
    background-color: {COLORS["bg_surface"]};
    border-radius: 14px;
}}

#MainWindowContainer {{
    background-color: {COLORS["bg_main"]};
    border-radius: 14px;
}}

#TitleBar {{
    background-color: {COLORS["bg_sidebar"]};
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}}

#Sidebar {{
    background-color: {COLORS["bg_sidebar"]};
}}

.Card {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS["bg_input"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["primary"]};
    selection-color: #FFFFFF;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {COLORS["primary"]};
    background-color: #FFFFFF;
}}

.input-error, QLineEdit[error="true"], QSpinBox[error="true"], QDoubleSpinBox[error="true"], QComboBox[error="true"] {{
    border: 1.5px solid {COLORS["border_error"]} !important;
    background-color: {COLORS["bg_error"]} !important;
}}

.error-label {{
    color: {COLORS["text_error"]};
    font-size: 11px;
    font-weight: 600;
}}

QComboBox {{
    background-color: {COLORS["bg_surface"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    color: {COLORS["text_primary"]};
    min-height: 24px;
}}

QComboBox:focus {{
    border: 1.5px solid {COLORS["primary"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    selection-background-color: {COLORS["primary_subtle"]};
    selection-color: {COLORS["primary"]};
    padding: 4px;
}}

QTableWidget {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    gridline-color: {COLORS["border_subtle"]};
    font-size: 13px;
    selection-background-color: {COLORS["primary_subtle"]};
    selection-color: {COLORS["text_primary"]};
}}

QHeaderView::section {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_secondary"]};
    padding: 8px 10px;
    border: none;
    border-bottom: 1.5px solid {COLORS["border"]};
    font-weight: bold;
    font-size: 12px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_muted"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    background: none;
    border: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    border: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["border"]};
    min-width: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS["text_muted"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: none;
    border: none;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    border: none;
}}

QScrollBar::corner {{
    background: transparent;
    border: none;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    background-color: {COLORS["bg_surface"]};
}}

QTabBar::tab {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_secondary"]};
    font-weight: 600;
    font-size: 12px;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS["primary"]};
    color: #FFFFFF;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS["border"]};
}}

QCheckBox {{
    spacing: 8px;
    font-size: 13px;
    color: {COLORS["text_secondary"]};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid {COLORS["border"]};
    background: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["primary"]};
    border-color: {COLORS["primary"]};
}}

QToolTip {{
    background-color: {COLORS["bg_sidebar"]};
    color: {COLORS["text_on_dark"]};
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

QMessageBox {{
    background-color: {COLORS["bg_surface"]};
}}

QMessageBox QLabel {{
    color: {COLORS["text_primary"]};
    font-size: 13px;
}}

QMessageBox QPushButton {{
    background-color: {COLORS["primary"]};
    color: #FFFFFF;
    font-weight: 600;
    font-size: 12px;
    border-radius: 6px;
    padding: 6px 20px;
    min-width: 80px;
    border: none;
}}

QMessageBox QPushButton:hover {{
    background-color: {COLORS["primary_hover"]};
}}
"""


def apply_windows_native_corners(widget):
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            hwnd = int(widget.winId())
            val = ctypes.c_int(DWMWCP_ROUND)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(val),
                ctypes.sizeof(val)
            )
        except Exception:
            pass


class AnimatedButton(QPushButton):
    """Button with scale-press micro-animation and variant-based styling."""
    def __init__(self, text="", parent=None, variant="primary", is_icon_only=False, icon_name=None, icon_color=None, icon_size=16):
        super().__init__(text, parent)
        self.variant = variant
        self.is_icon_only = is_icon_only or (len(text.strip()) == 0 and icon_name is not None) or (len(text.strip()) <= 3 and icon_name is None)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(90)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._apply_variant_style()

        if icon_name:
            from pos_app.utils.icon_helper import get_icon
            default_color = "#FFFFFF" if variant in ("primary", "danger", "success") else (COLORS["danger"] if variant == "danger_subtle" else COLORS["text_secondary"])
            c = icon_color or default_color
            self.setIcon(get_icon(icon_name, color=c, size=icon_size))
            self.setIconSize(QSize(icon_size, icon_size))

    def _apply_variant_style(self):
        padding = "padding: 0px; text-align: center;" if self.is_icon_only else "padding: 8px 16px;"
        font_size = "14px" if self.is_icon_only else "13px"
        font_family = "'Segoe UI', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif"

        styles = {
            "primary": f"""
                QPushButton {{
                    background-color: {COLORS["primary"]};
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: {font_size};
                    font-family: {font_family};
                    border-radius: 8px;
                    {padding}
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["primary_hover"]};
                }}
            """,
            "secondary": f"""
                QPushButton {{
                    background-color: {COLORS["bg_hover"]};
                    color: {COLORS["text_primary"]};
                    font-weight: 600;
                    font-size: {font_size};
                    font-family: {font_family};
                    border-radius: 8px;
                    {padding}
                    border: 1px solid {COLORS["border"]};
                }}
                QPushButton:hover {{
                    background-color: {COLORS["border"]};
                }}
            """,
            "success": f"""
                QPushButton {{
                    background-color: {COLORS["success"]};
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: {font_size};
                    font-family: {font_family};
                    border-radius: 8px;
                    {padding}
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["success_hover"]};
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background-color: {COLORS["danger"]};
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: {font_size};
                    font-family: {font_family};
                    border-radius: 8px;
                    {padding}
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["danger_hover"]};
                }}
            """,
            "danger_subtle": f"""
                QPushButton {{
                    background-color: {COLORS["danger_subtle"]};
                    color: {COLORS["danger"]};
                    font-weight: bold;
                    font-size: {font_size};
                    font-family: {font_family};
                    border-radius: 8px;
                    {padding}
                    border: 1px solid #FECACA;
                }}
                QPushButton:hover {{
                    background-color: #FEE2E2;
                }}
            """,
            "outline": f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS["primary"]};
                    font-weight: 600;
                    font-size: {font_size};
                    font-family: {font_family};
                    border-radius: 8px;
                    {padding}
                    border: 1.5px solid {COLORS["primary"]};
                }}
                QPushButton:hover {{
                    background-color: {COLORS["primary_subtle"]};
                }}
            """
        }
        self.setStyleSheet(styles.get(self.variant, styles["primary"]))

    def mousePressEvent(self, event):
        g = self.geometry()
        self.anim.stop()
        self.anim.setEndValue(QRect(g.x() + 2, g.y() + 1, max(10, g.width() - 4), max(10, g.height() - 2)))
        self.anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        g = self.geometry()
        self.anim.stop()
        self.anim.setEndValue(QRect(g.x() - 2, g.y() - 1, g.width() + 4, g.height() + 2))
        self.anim.start()
        super().mouseReleaseEvent(event)


class DropShadowCard(QFrame):
    """Surface card with rounded corners and ambient drop shadow."""
    def __init__(self, parent=None, corner_radius=12, blur_radius=18, offset_y=4, opacity=25):
        super().__init__(parent)
        self.setObjectName("DropShadowCard")
        self.setStyleSheet(f"""
            QFrame#DropShadowCard {{
                background-color: {COLORS["bg_surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {corner_radius}px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(15, 23, 42, opacity))
        shadow.setOffset(0, offset_y)
        self.setGraphicsEffect(shadow)


class SmoothModalOverlay(QWidget):
    """Backdrop modal overlay with scale/bounce animation."""
    closed = Signal()

    def __init__(self, parent, target_width=500, target_height=420):
        super().__init__(parent)
        self.target_width = target_width
        self.target_height = target_height
        self.hide()

        self.resize(parent.size())

        self.backdrop = QFrame(self)
        self.backdrop.setGeometry(0, 0, parent.width(), parent.height())
        self.backdrop.setStyleSheet("background-color: rgba(15, 23, 42, 140);")

        self.card = QFrame(self)
        self.card.setObjectName("ModalCard")
        self.card.setStyleSheet(f"""
            QFrame#ModalCard {{
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid {COLORS["border"]};
            }}
        """)

        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(32)
        card_shadow.setColor(QColor(0, 0, 0, 80))
        card_shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(card_shadow)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(24, 20, 24, 20)

        self.anim = QPropertyAnimation(self.card, b"geometry")
        self.anim.setDuration(340)

    def set_content_widget(self, widget: QWidget):
        self.card_layout.addWidget(widget)

    def show_animated(self):
        if not self.parent():
            return
        self.resize(self.parent().size())
        self.backdrop.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.show()
        self.raise_()

        cx = (self.width() - self.target_width) // 2
        cy = (self.height() - self.target_height) // 2

        self.anim.stop()
        self.anim.setDuration(340)
        self.anim.setStartValue(QRect(cx + self.target_width // 2, cy + self.target_height // 2, 0, 0))
        self.anim.setEndValue(QRect(cx, cy, self.target_width, self.target_height))
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()

    def hide_animated(self):
        cx = (self.width() - self.target_width) // 2
        cy = (self.height() - self.target_height) // 2

        self.anim.stop()
        self.anim.setDuration(220)
        self.anim.setStartValue(QRect(cx, cy, self.target_width, self.target_height))
        self.anim.setEndValue(QRect(cx + self.target_width // 2, cy + self.target_height // 2, 0, 0))
        self.anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        try:
            self.anim.finished.disconnect(self._on_hide_finished)
        except Exception:
            pass
        self.hide()
        self.closed.emit()
