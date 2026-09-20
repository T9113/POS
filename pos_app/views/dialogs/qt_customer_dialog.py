"""
PySide6 Add Customer Dialog for OnesDev POS.
iPhone-style animated popup for creating customers with credit/Khata allowances.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.utils.icon_helper import get_icon
from pos_app.models.customer_model import CustomerModel


class QtCustomerDialog(SmoothModalOverlay):
    """Elastic bounce modal for Adding / Registering Customers."""
    customer_created = Signal(dict)

    def __init__(self, parent, on_complete=None):
        super().__init__(parent, target_width=480, target_height=460)
        self.on_complete = on_complete
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header Title
        title_row = QHBoxLayout()
        ico_title = QLabel(content)
        ico_title.setPixmap(get_icon("customers", color=COLORS["primary"], size=20).pixmap(20, 20))
        ico_title.setFixedSize(22, 22)
        title_row.addWidget(ico_title)

        lbl_title = QLabel("Add New Customer", content)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        title_row.addWidget(lbl_title)

        title_row.addStretch()

        btn_close = QPushButton("", content)
        btn_close.setIcon(get_icon("close", color=COLORS["text_muted"], size=14))
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; border: none; border-radius: 6px;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        form = QFormLayout()
        form.setSpacing(10)

        # Customer Name container with error label
        name_container = QWidget(content)
        name_l = QVBoxLayout(name_container)
        name_l.setContentsMargins(0, 0, 0, 0)
        name_l.setSpacing(3)

        self.txt_name = QLineEdit(name_container)
        self.txt_name.setPlaceholderText("Customer Full Name *")
        self.txt_name.textChanged.connect(self._clear_name_error)
        name_l.addWidget(self.txt_name)

        self.lbl_name_err = QLabel("", name_container)
        self.lbl_name_err.setStyleSheet(f"color: {COLORS['border_error']}; font-size: 11px; font-weight: 600;")
        self.lbl_name_err.setVisible(False)
        name_l.addWidget(self.lbl_name_err)

        lbl_name_req = QLabel("Full Name <span style='color:#EF4444;'>*</span>:", content)
        form.addRow(lbl_name_req, name_container)

        self.txt_phone = QLineEdit(content)
        self.txt_phone.setPlaceholderText("Phone number (e.g. 0300-1234567)")
        form.addRow("Phone Number:", self.txt_phone)

        self.txt_email = QLineEdit(content)
        self.txt_email.setPlaceholderText("Email address (optional)")
        form.addRow("Email Address:", self.txt_email)

        self.txt_address = QLineEdit(content)
        self.txt_address.setPlaceholderText("Delivery or billing address")
        form.addRow("Address:", self.txt_address)

        self.txt_notes = QLineEdit(content)
        self.txt_notes.setPlaceholderText("Khata terms, credit allowance, notes")
        form.addRow("Notes / Khata:", self.txt_notes)

        layout.addLayout(form)

        btn_save = AnimatedButton("Save Customer", content, variant="primary", icon_name="check", icon_color="#FFFFFF", icon_size=16)
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self._save_customer)
        layout.addWidget(btn_save)

        self.set_content_widget(content)

    def _clear_name_error(self):
        self.txt_name.setStyleSheet("")
        self.lbl_name_err.setVisible(False)

    def _save_customer(self):
        name = self.txt_name.text().strip()
        if not name:
            self.txt_name.setStyleSheet(f"border: 1.5px solid {COLORS['border_error']}; background-color: {COLORS['bg_error']};")
            self.lbl_name_err.setText("Customer name is required.")
            self.lbl_name_err.setVisible(True)
            self.txt_name.setFocus()
            return

        phone = self.txt_phone.text().strip()
        email = self.txt_email.text().strip()
        addr = self.txt_address.text().strip()
        notes = self.txt_notes.text().strip()

        cid = CustomerModel.create(name, phone, email, addr, notes, 0.0)
        cust = CustomerModel.get_by_id(cid)
        self.customer_created.emit(cust)
        if self.on_complete:
            self.on_complete(cust)
        self.hide_animated()
