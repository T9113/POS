"""
Design system, theme tokens, QSS styling, and animated widgets for OnesDev POS.
Hardware-accelerated Slate & Indigo commercial theme with iOS-inspired physics.
"""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, Signal
from PySide6.QtWidgets import (
    QWidget, QPushButton, QFrame, QLabel, QGraphicsDropShadowEffect,
    QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
)
from PySide6.QtGui import QColor, QFont, QCursor

# Color Tokens (Slate & Indigo Palette)
COLORS = {
    # App shell & surfaces
    "bg_main": "#F8F9FB",
    "bg_surface": "#FFFFFF",
    "bg_surface_raised": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "bg_hover": "#F1F5F9",
    "bg_input": "#F8F9FB",

    # Sidebar: Deep Slate
    "bg_sidebar": "#1E293B",
    "sidebar_text": "#94A3B8",
    "sidebar_hover": "#334155",
    "sidebar_active_bg": "#334155",
    "sidebar_active_text": "#FFFFFF",
    "sidebar_indicator": "#6366F1",

    # Borders & Dividers
    "border": "#E2E8F0",
    "border_subtle": "#F1F5F9",
    "border_focus": "#6366F1",

    # Typography
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "text_on_dark": "#F8FAFC",
    "text_on_primary": "#FFFFFF",

    # Accents & Semantic
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_subtle": "#EEF2FF",
    "success": "#059669",
    "success_hover": "#047857",
    "success_subtle": "#ECFDF5",
    "warning": "#D97706",
    "warning_hover": "#B45309",
    "warning_subtle": "#FFFBEB",
    "danger": "#DC2626",
    "danger_hover": "#B91C1C",
    "danger_subtle": "#FEF2F2",
    "gold": "#D97706",
}

# Global QSS Stylesheet
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

/* Main background */
#MainWindowContainer {{
    background-color: {COLORS["bg_main"]};
    border-radius: 14px;
}}

/* Title bar */
#TitleBar {{
    background-color: {COLORS["bg_sidebar"]};
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}}

/* Sidebar */
#Sidebar {{
    background-color: {COLORS["bg_sidebar"]};
}}

/* Cards & Panels */
.Card {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}

/* Input Fields */
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

/* Combobox */
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

/* Tables */
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

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_muted"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["border"]};
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS["text_muted"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Tab Widget */
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
"""


def apply_windows_native_corners(widget):
    """
    Applies Windows 11 Desktop Window Manager (DWM) native rounded corners (16px)
    to any native window handle, preventing sharp/square corners.
    """
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
    """
    Button with iPhone-like scale-press micro-animation.
    Shrinks slightly on click with OutQuad easing and snaps back on release.
    Automatically formats icon buttons and short symbols with 0px padding so icons are never clipped.
    """
    def __init__(self, text="", parent=None, variant="primary", is_icon_only=False):
        super().__init__(text, parent)
        self.variant = variant
        self.is_icon_only = is_icon_only or len(text.strip()) <= 3
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Setup geometry animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(90)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._apply_variant_style()

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
    """Clean surface card with rounded corners and ambient soft drop shadow."""
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
    """
    iPhone-style backdrop modal overlay.
    Dims the background with transparent slate, and scales/bounces the central card
    into place using QEasingCurve.Type.OutBack.
    """
    closed = Signal()

    def __init__(self, parent, target_width=500, target_height=420):
        super().__init__(parent)
        self.target_width = target_width
        self.target_height = target_height
        self.hide()

        # Fill entire parent window
        self.resize(parent.size())

        # Semi-transparent dimmed backdrop
        self.backdrop = QFrame(self)
        self.backdrop.setGeometry(0, 0, parent.width(), parent.height())
        self.backdrop.setStyleSheet("background-color: rgba(15, 23, 42, 140);")

        # Modal Card Container
        self.card = QFrame(self)
        self.card.setObjectName("ModalCard")
        self.card.setStyleSheet(f"""
            QFrame#ModalCard {{
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid {COLORS["border"]};
            }}
        """)

        # Soft shadow for the modal card
        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(32)
        card_shadow.setColor(QColor(0, 0, 0, 80))
        card_shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(card_shadow)

        # Card content layout
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(24, 20, 24, 20)

        # Animation engine
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

        # Center coordinates
        cx = (self.width() - self.target_width) // 2
        cy = (self.height() - self.target_height) // 2

        # Animate from small center point to full size with elastic OutBack curve
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
