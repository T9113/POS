"""
PySide6 Login View for OnesDev POS.
Floating authentication card with soft drop shadow, smooth entry, and quick credentials.
"""
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QMainWindow
)
from PySide6.QtGui import QFont

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.settings_model import SettingsModel


class QtLoginView(QWidget):
    """Modern floating login card with authentic shadow and smooth interaction."""
    login_successful = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # Floating Card Container
        self.card = DropShadowCard(self, corner_radius=16, blur_radius=35, offset_y=10, opacity=45)
        self.card.setFixedSize(420, 520)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 20, 32, 28)
        card_layout.setSpacing(12)

        # Top close button
        top_row = QHBoxLayout()
        top_row.addStretch()
        btn_close = QPushButton("✕", self.card)
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("background: transparent; color: #94A3B8; font-size: 14px; font-weight: bold; border: none; border-radius: 13px;")
        btn_close.clicked.connect(self.close_requested.emit)
        top_row.addWidget(btn_close)
        card_layout.addLayout(top_row)

        # Logo / Brand
        lbl_icon = QLabel("🛒", self.card)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_icon = QFont("Segoe UI Emoji", 34)
        lbl_icon.setFont(font_icon)
        card_layout.addWidget(lbl_icon)

        lbl_title = QLabel("OnesDev POS", self.card)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['primary']};")
        card_layout.addWidget(lbl_title)

        biz_name = SettingsModel.get("business_name", "OnesDev POS Store")
        lbl_sub = QLabel(f"{biz_name}  •  Desktop POS", self.card)
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(lbl_sub)

        card_layout.addSpacing(10)

        # Username
        lbl_user = QLabel("Username / User ID", self.card)
        lbl_user.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(lbl_user)

        self.txt_username = QLineEdit(self.card)
        self.txt_username.setPlaceholderText("Enter username (e.g. admin)")
        self.txt_username.setText("admin")
        self.txt_username.setFixedHeight(40)
        card_layout.addWidget(self.txt_username)

        # Password
        lbl_pass = QLabel("Password", self.card)
        lbl_pass.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(lbl_pass)

        self.txt_password = QLineEdit(self.card)
        self.txt_password.setPlaceholderText("Enter password")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setText("admin")
        self.txt_password.setFixedHeight(40)
        self.txt_password.returnPressed.connect(self._handle_login)
        card_layout.addWidget(self.txt_password)

        # Error label
        self.lbl_error = QLabel("", self.card)
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet(f"color: {COLORS['danger']}; font-weight: 600; font-size: 12px;")
        card_layout.addWidget(self.lbl_error)

        # Login button
        self.btn_login = AnimatedButton("Sign In  ➔", self.card, variant="primary")
        self.btn_login.setFixedHeight(44)
        self.btn_login.clicked.connect(self._handle_login)
        card_layout.addWidget(self.btn_login)

        # Quick login helper buttons
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)

        btn_fill_admin = AnimatedButton("👤 Admin Fill", self.card, variant="secondary")
        btn_fill_admin.setFixedHeight(30)
        btn_fill_admin.clicked.connect(lambda: self._fill_creds("admin", "admin"))
        quick_layout.addWidget(btn_fill_admin)

        btn_fill_cashier = AnimatedButton("💼 Cashier Fill", self.card, variant="secondary")
        btn_fill_cashier.setFixedHeight(30)
        btn_fill_cashier.clicked.connect(lambda: self._fill_creds("cashier", "cashier"))
        quick_layout.addWidget(btn_fill_cashier)

        card_layout.addLayout(quick_layout)
        card_layout.addStretch()

        root_layout.addWidget(self.card)

    def _fill_creds(self, u, p):
        self.txt_username.setText(u)
        self.txt_password.setText(p)
        self.lbl_error.setText("")

    def _handle_login(self):
        u = self.txt_username.text().strip()
        p = self.txt_password.text().strip()
        if not u or not p:
            self.lbl_error.setText("Please enter both username and password.")
            return

        user = AuthController.login(u, p)
        if user:
            self.lbl_error.setText("")
            self.login_successful.emit()
        else:
            self.lbl_error.setText("Invalid username or password.")


class QtLoginWindow(QMainWindow):
    """Frameless translucent wrapper window for QtLoginView."""
    def __init__(self, on_login_success=None):
        super().__init__()
        self.on_login_success = on_login_success
        self.drag_position = QPoint()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 580)

        self.login_view = QtLoginView(self)
        self.login_view.login_successful.connect(self._handle_success)
        self.login_view.close_requested.connect(self.close)
        self.setCentralWidget(self.login_view)

    def _handle_success(self):
        self.close()
        if self.on_login_success:
            self.on_login_success()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()
        event.accept()

