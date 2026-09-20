"""
PySide6 Registration & Software Activation Dialog for OnesDev POS.
Hardware-locked activation card with ambient drop shadow, OutBack spring bounce,
1-click Machine ID clipboard copy, and file/paste license activation.
"""
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QFileDialog, QMessageBox, QFrame,
    QApplication
)
from PySide6.QtGui import QFont, QGuiApplication

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, apply_windows_native_corners
from pos_app.utils.license_manager import LicenseManager


class QtRegistrationWindow(QMainWindow):
    """Frameless translucent software activation window."""
    activation_successful = Signal(dict)

    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()

        # Frameless & translucent background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(540, 640)
        apply_windows_native_corners(self)

        self._build_ui()

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(15, 15, 15, 15)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Floating Card Container
        self.card = DropShadowCard(central, corner_radius=18, blur_radius=35, offset_y=8, opacity=50)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 24, 32, 28)
        card_layout.setSpacing(12)

        # Top Bar (Close button)
        top_bar = QHBoxLayout()
        lbl_brand_tag = QLabel("🔒 LICENSED SOFTWARE", self.card)
        lbl_brand_tag.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLORS['primary']}; letter-spacing: 0.5px;")
        top_bar.addWidget(lbl_brand_tag)

        top_bar.addStretch()

        btn_close = QPushButton("✕", self.card)
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("background: transparent; color: #94A3B8; font-size: 14px; font-weight: bold; border: none; border-radius: 13px;")
        btn_close.clicked.connect(self.close)
        top_bar.addWidget(btn_close)
        card_layout.addLayout(top_bar)

        # Title & Branding
        lbl_title = QLabel("OnesDev POS Activation", self.card)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text_primary']};")
        card_layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "This installation is locked to this specific computer.\nCopying software files to another PC requires a new license.",
            self.card
        )
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(lbl_desc)

        card_layout.addSpacing(6)

        # Machine ID Box Card
        hwid_box = QFrame(self.card)
        hwid_box.setObjectName("HwidBox")
        hwid_box.setStyleSheet(f"""
            #HwidBox {{
                background-color: {COLORS['bg_hover']};
                border: 1.5px dashed {COLORS['border_focus']};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        hw_layout = QVBoxLayout(hwid_box)
        hw_layout.setContentsMargins(12, 10, 12, 10)
        hw_layout.setSpacing(6)

        lbl_hw_label = QLabel("YOUR UNIQUE MACHINE ID:", hwid_box)
        lbl_hw_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 0.5px;")
        hw_layout.addWidget(lbl_hw_label)

        self.machine_id = LicenseManager.get_machine_id()
        self.lbl_machine_id = QLabel(self.machine_id, hwid_box)
        self.lbl_machine_id.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['primary']}; font-family: Consolas, monospace;")
        self.lbl_machine_id.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hw_layout.addWidget(self.lbl_machine_id)

        btn_copy = AnimatedButton("📋 Copy Machine ID to Clipboard", hwid_box, variant="secondary")
        btn_copy.setFixedHeight(34)
        btn_copy.clicked.connect(self._copy_machine_id)
        hw_layout.addWidget(btn_copy)

        self.lbl_copied = QLabel("", hwid_box)
        self.lbl_copied.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_copied.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['success']};")
        hw_layout.addWidget(self.lbl_copied)

        card_layout.addWidget(hwid_box)

        # License Key Input Box
        lbl_key = QLabel("Enter License Key", self.card)
        lbl_key.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(lbl_key)

        self.txt_key = QPlainTextEdit(self.card)
        self.txt_key.setPlaceholderText("Paste your official cryptographic license key string here...")
        self.txt_key.setFixedHeight(85)
        self.txt_key.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLORS['bg_input']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }}
            QPlainTextEdit:focus {{
                border: 1.5px solid {COLORS['border_focus']};
            }}
        """)
        card_layout.addWidget(self.txt_key)

        # Load file button row
        file_row = QHBoxLayout()
        btn_load_file = QPushButton("📂 Load from .lic file", self.card)
        btn_load_file.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_load_file.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['primary']};
                font-size: 12px;
                font-weight: 600;
                border: none;
                text-decoration: underline;
            }}
        """)
        btn_load_file.clicked.connect(self._load_from_file)
        file_row.addWidget(btn_load_file)
        file_row.addStretch()
        card_layout.addLayout(file_row)

        # Error / Status Label
        self.lbl_error = QLabel("", self.card)
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet(f"color: {COLORS['danger']}; font-weight: 600; font-size: 12px;")
        card_layout.addWidget(self.lbl_error)

        # Activate Button
        self.btn_activate = AnimatedButton("🔓 Activate Software Now", self.card, variant="primary")
        self.btn_activate.setFixedHeight(44)
        self.btn_activate.clicked.connect(self._handle_activate)
        card_layout.addWidget(self.btn_activate)

        card_layout.addStretch()
        root_layout.addWidget(self.card)

    def _copy_machine_id(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.machine_id)
        self.lbl_copied.setText("✓ Copied to clipboard! Send this ID to OnesDev to receive your key.")

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select License File", "", "License Files (*.lic *.key);;All Files (*.*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                    self.txt_key.setPlainText(key)
                    self.lbl_error.setText("")
            except Exception as e:
                self.lbl_error.setText(f"Could not read license file: {str(e)}")

    def _handle_activate(self):
        key = self.txt_key.toPlainText().strip()
        if not key:
            self.lbl_error.setText("Please paste a valid license key or load a .lic file.")
            return

        valid, msg, payload = LicenseManager.verify_license(key)
        if not valid:
            self.lbl_error.setText(f"❌ Activation Failed: {msg}")
            return

        # Save verified license
        LicenseManager.save_license(key)
        self.lbl_error.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 13px;")
        client_name = payload.get("client", "Customer")
        self.lbl_error.setText(f"✓ Activation Successful for {client_name}!")
        self.btn_activate.setEnabled(False)

        # Complete activation
        QMessageBox.information(
            self, "Activation Complete",
            f"Thank you for registering!\n\nLicensed To: {client_name}\nMachine ID: {self.machine_id}\nLicense: Lifetime Commercial\n\nThe application is now fully unlocked."
        )
        self.close()
        self.activation_successful.emit(payload)

    # Window Dragging
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
