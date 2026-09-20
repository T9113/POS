"""
PySide6 Add Customer Dialog for OnesDev POS.
iPhone-style animated popup for creating customers with credit/Khata allowances.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.models.customer_model import CustomerModel


class QtCustomerDialog(SmoothModalOverlay):
    """Elastic bounce modal for Adding / Registering Customers."""
    customer_created = Signal(dict)

    def __init__(self, parent, on_complete=None):
        super().__init__(parent, target_width=460, target_height=420)
        self.on_complete = on_complete
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header Title
        title_row = QHBoxLayout()
        lbl_title = QLabel("👤 Add New Customer", content)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        title_row.addWidget(lbl_title)

        btn_close = QPushButton("✕", content)
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; color: #94A3B8; font-size: 16px; font-weight: bold; border: none;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_name = QLineEdit(content)
        self.txt_name.setPlaceholderText("Customer Full Name *")
        form.addRow("Full Name *:", self.txt_name)

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

        self.lbl_msg = QLabel("", content)
        self.lbl_msg.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.lbl_msg)

        btn_save = AnimatedButton("💾 Save Customer", content, variant="primary")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self._save_customer)
        layout.addWidget(btn_save)

        self.set_content_widget(content)

    def _save_customer(self):
        name = self.txt_name.text().strip()
        if not name:
            self.lbl_msg.setText("Customer name is required!")
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
