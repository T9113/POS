"""
PySide6 Return/Refund Dialog for OnesDev POS.
Allows processing returns against a completed order with item selection
and automatic stock restoration.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QMessageBox, QPushButton, QTextEdit
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.icon_helper import get_icon


class QtReturnDialog(SmoothModalOverlay):
    """Modal for processing a return/refund against a sale order."""
    return_completed = Signal()

    def __init__(self, parent, order: dict, on_complete=None):
        super().__init__(parent, target_width=580, target_height=520)
        self.order = order
        self.on_complete = on_complete
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.item_checks = []
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        title_row = QHBoxLayout()
        ico = QLabel(content)
        ico.setPixmap(get_icon("undo", color=COLORS["warning"], size=20).pixmap(20, 20))
        ico.setFixedSize(22, 22)
        title_row.addWidget(ico)

        lbl_title = QLabel(f"Return / Refund  —  {self.order.get('order_number', '')}", content)
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

        # Order summary
        lbl_info = QLabel(
            f"Customer: <b>{self.order.get('customer_name') or 'Walk-in'}</b>  |  "
            f"Total: <b>{self.currency} {self.order.get('total', 0):,.2f}</b>",
            content
        )
        lbl_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: {COLORS['bg_hover']}; padding: 6px 10px; border-radius: 6px;")
        layout.addWidget(lbl_info)

        # Items table with checkboxes
        lbl_items = QLabel("Select items to return:", content)
        lbl_items.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_items)

        self.table = QTableWidget(content)
        items = self.order.get("items", [])
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Return", "Product", "Qty Sold", "Return Qty", "Refund Amount"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setRowCount(len(items))
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-weight: 600; font-size: 12px;
                padding: 6px; border: none;
                border-bottom: 2px solid {COLORS['border']};
            }}
        """)

        self.item_checks = []
        for r, item in enumerate(items):
            chk = QCheckBox()
            chk.stateChanged.connect(self._update_refund_total)
            self.table.setCellWidget(r, 0, chk)
            self.item_checks.append(chk)

            self.table.setItem(r, 1, QTableWidgetItem(item.get("product_name", "")))

            qty_item = QTableWidgetItem(str(item.get("quantity", 0)))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, qty_item)

            qty_edit = QLineEdit(str(item.get("quantity", 0)))
            qty_edit.setFixedHeight(28)
            qty_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_edit.textChanged.connect(self._update_refund_total)
            self.table.setCellWidget(r, 3, qty_edit)

            unit_price = float(item.get("unit_price", 0))
            qty = float(item.get("quantity", 0))
            refund_item = QTableWidgetItem(f"{self.currency} {unit_price * qty:,.2f}")
            refund_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 4, refund_item)

        layout.addWidget(self.table, stretch=1)

        # Reason
        lbl_reason = QLabel("Return Reason:", content)
        lbl_reason.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_reason)

        self.txt_reason = QTextEdit(content)
        self.txt_reason.setFixedHeight(50)
        self.txt_reason.setPlaceholderText("Describe reason for return (defective, wrong item, etc.)")
        self.txt_reason.setStyleSheet(f"border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 6px; font-size: 13px;")
        layout.addWidget(self.txt_reason)

        # Refund total
        self.lbl_refund = QLabel(f"Total Refund: {self.currency} 0.00", content)
        self.lbl_refund.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['danger']}; text-align: right;")
        self.lbl_refund.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lbl_refund)

        # Confirm
        self.btn_confirm = AnimatedButton("Process Return & Refund", content, variant="danger", icon_name="undo", icon_color="#FFFFFF", icon_size=14)
        self.btn_confirm.setFixedHeight(42)
        self.btn_confirm.clicked.connect(self._process_return)
        layout.addWidget(self.btn_confirm)

        self.set_content_widget(content)

    def _update_refund_total(self):
        items = self.order.get("items", [])
        total = 0.0
        for r, item in enumerate(items):
            if r < len(self.item_checks) and self.item_checks[r].isChecked():
                qty_widget = self.table.cellWidget(r, 3)
                try:
                    ret_qty = float(qty_widget.text()) if qty_widget else float(item.get("quantity", 0))
                except ValueError:
                    ret_qty = 0
                ret_qty = min(ret_qty, float(item.get("quantity", 0)))
                unit_price = float(item.get("unit_price", 0))
                line_refund = unit_price * ret_qty
                total += line_refund

                refund_item = QTableWidgetItem(f"{self.currency} {line_refund:,.2f}")
                refund_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r, 4, refund_item)

        self.lbl_refund.setText(f"Total Refund: {self.currency} {total:,.2f}")

    def _process_return(self):
        items = self.order.get("items", [])
        returned_items = []
        total_refund = 0.0

        for r, item in enumerate(items):
            if r < len(self.item_checks) and self.item_checks[r].isChecked():
                qty_widget = self.table.cellWidget(r, 3)
                try:
                    ret_qty = float(qty_widget.text()) if qty_widget else float(item.get("quantity", 0))
                except ValueError:
                    ret_qty = 0
                ret_qty = min(ret_qty, float(item.get("quantity", 0)))
                if ret_qty <= 0:
                    continue
                unit_price = float(item.get("unit_price", 0))
                returned_items.append({
                    "product_id": item.get("product_id"),
                    "product_name": item.get("product_name"),
                    "quantity": ret_qty,
                    "unit_price": unit_price,
                    "refund_amount": unit_price * ret_qty
                })
                total_refund += unit_price * ret_qty

        if not returned_items:
            QMessageBox.warning(self, "No Items", "Please select at least one item to return.")
            return

        reason = self.txt_reason.toPlainText().strip() or "No reason provided"
        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        reply = QMessageBox.question(
            self, "Confirm Return",
            f"Process refund of {self.currency} {total_refund:,.2f}?\n\nItems will be restocked automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        OrderModel.process_return(
            order_id=self.order.get("id"),
            user_id=user_id,
            returned_items=returned_items,
            total_refund=total_refund,
            reason=reason
        )

        self.return_completed.emit()
        if self.on_complete:
            self.on_complete()

        QMessageBox.information(self, "Return Processed", f"Refund of {self.currency} {total_refund:,.2f} processed successfully.\nStock has been restored.")
        self.hide_animated()
