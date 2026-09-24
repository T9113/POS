"""
PySide6 Stock Adjustment Dialog for OnesDev POS.
Quick stock-in/stock-out adjustments with reason tracking.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QMessageBox, QPushButton, QTextEdit
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.models.inventory_model import InventoryModel
from pos_app.models.product_model import ProductModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.icon_helper import get_icon


class QtStockAdjustDialog(SmoothModalOverlay):
    """Modal for adjusting a product's stock level."""
    stock_adjusted = Signal()

    def __init__(self, parent, product: dict = None, on_complete=None):
        super().__init__(parent, target_width=460, target_height=420)
        self.product = product
        self.on_complete = on_complete
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        title_row = QHBoxLayout()
        ico = QLabel(content)
        ico.setPixmap(get_icon("package", color=COLORS["primary"], size=20).pixmap(20, 20))
        ico.setFixedSize(22, 22)
        title_row.addWidget(ico)

        lbl_title = QLabel("Stock Adjustment", content)
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

        # Product selector (if not pre-selected)
        if not self.product:
            lbl_prod = QLabel("Select Product:", content)
            lbl_prod.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
            layout.addWidget(lbl_prod)

            self.cmb_product = QComboBox(content)
            self.cmb_product.setFixedHeight(38)
            self.products = ProductModel.list_all()
            for p in self.products:
                self.cmb_product.addItem(f"{p['name']} (Stock: {p.get('current_stock', 0)})", p["id"])
            self.cmb_product.currentIndexChanged.connect(self._update_current_stock)
            layout.addWidget(self.cmb_product)
        else:
            lbl_prod_info = QLabel(
                f"Product: <b>{self.product['name']}</b>  |  Current Stock: <b>{self.product.get('current_stock', 0)}</b>",
                content
            )
            lbl_prod_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; background: {COLORS['bg_hover']}; padding: 8px 10px; border-radius: 6px;")
            layout.addWidget(lbl_prod_info)

        # Direction
        lbl_dir = QLabel("Adjustment Type:", content)
        lbl_dir.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_dir)

        self.cmb_direction = QComboBox(content)
        self.cmb_direction.setFixedHeight(38)
        self.cmb_direction.addItems(["Stock In (+)", "Stock Out (-)"])
        layout.addWidget(self.cmb_direction)

        # Quantity
        lbl_qty = QLabel("Quantity:", content)
        lbl_qty.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_qty)

        self.txt_qty = QLineEdit(content)
        self.txt_qty.setPlaceholderText("Enter quantity to adjust")
        self.txt_qty.setFixedHeight(38)
        layout.addWidget(self.txt_qty)

        # Reason
        lbl_reason = QLabel("Reason:", content)
        lbl_reason.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_reason)

        self.cmb_reason = QComboBox(content)
        self.cmb_reason.setFixedHeight(38)
        self.cmb_reason.addItems([
            "Physical Count Correction",
            "Damaged / Expired",
            "Lost / Theft",
            "Supplier Return",
            "New Stock Received",
            "Transfer",
            "Other"
        ])
        layout.addWidget(self.cmb_reason)

        # Note
        lbl_note = QLabel("Note (optional):", content)
        lbl_note.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_note)

        self.txt_note = QTextEdit(content)
        self.txt_note.setFixedHeight(50)
        self.txt_note.setPlaceholderText("Additional details...")
        self.txt_note.setStyleSheet(f"border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 6px; font-size: 13px;")
        layout.addWidget(self.txt_note)

        # Confirm
        self.btn_save = AnimatedButton("Save Adjustment", content, variant="primary", icon_name="check", icon_color="#FFFFFF", icon_size=14)
        self.btn_save.setFixedHeight(42)
        self.btn_save.clicked.connect(self._save_adjustment)
        layout.addWidget(self.btn_save)

        self.set_content_widget(content)

    def _update_current_stock(self):
        pass

    def _save_adjustment(self):
        try:
            qty = float(self.txt_qty.text())
            if qty <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Quantity", "Please enter a positive number.")
            return

        if self.cmb_direction.currentIndex() == 1:
            qty = -qty

        reason = self.cmb_reason.currentText()
        note = self.txt_note.toPlainText().strip()

        if self.product:
            product_id = self.product["id"]
        else:
            idx = self.cmb_product.currentIndex()
            if idx < 0:
                QMessageBox.warning(self, "No Product", "Please select a product.")
                return
            product_id = self.products[idx]["id"]

        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        InventoryModel.adjust_stock(product_id, user_id, qty, reason, note)

        self.stock_adjusted.emit()
        if self.on_complete:
            self.on_complete()

        QMessageBox.information(self, "Stock Updated", f"Stock adjusted by {qty:+g} units.")
        self.hide_animated()
