"""
PySide6 Return/Refund Dialog for OnesDev POS.
Item-level returns against a completed sale. Refunds are paid at the effective
price the customer actually paid (after order discount/tax), quantities are
limited to what has not already been returned, and stock is restored.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QMessageBox, QPushButton, QLineEdit
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
        super().__init__(parent, target_width=640, target_height=540)
        self.order = order
        self.on_complete = on_complete
        self.currency = SettingsModel.get("currency_symbol", "Rs")

        subtotal = float(order.get("subtotal") or 0.0)
        total = float(order.get("total") or 0.0)
        self.paid_ratio = (total / subtotal) if subtotal > 0 else 1.0

        already = OrderModel.get_returned_quantities(order.get("id"))
        self.rows = []
        for item in order.get("items", []):
            key = item.get("product_id") or item.get("product_name")
            sold = float(item.get("quantity", 0))
            remaining = max(0.0, sold - already.get(key, 0.0))
            already[key] = max(0.0, already.get(key, 0.0) - sold)
            self.rows.append({
                "item": item,
                "sold": sold,
                "remaining": remaining,
                "unit_refund": round(float(item.get("unit_price", 0)) * self.paid_ratio, 2),
            })
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

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

        pay_method = (self.order.get("payment_method") or "cash").upper()
        info = (
            f"Customer: <b>{self.order.get('customer_name') or 'Walk-in'}</b>  •  "
            f"Paid by: <b>{pay_method}</b>  •  "
            f"Order total: <b>{self.currency} {float(self.order.get('total', 0)):,.2f}</b>"
        )
        lbl_info = QLabel(info, content)
        lbl_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: {COLORS['bg_hover']}; padding: 8px 10px; border-radius: 6px;")
        layout.addWidget(lbl_info)

        lbl_items = QLabel("Tick the items being returned and set the quantity:", content)
        lbl_items.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_items)

        self.table = QTableWidget(content)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Product", "Sold", "Returnable", "Return Qty", "Refund"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 36)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (2, 3, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 96)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setRowCount(len(self.rows))

        self.item_checks = []
        self.qty_spins = []
        for r, row in enumerate(self.rows):
            item = row["item"]
            can_return = row["remaining"] > 0

            chk_wrap = QWidget()
            chk_l = QHBoxLayout(chk_wrap)
            chk_l.setContentsMargins(0, 0, 0, 0)
            chk_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox(chk_wrap)
            chk.setEnabled(can_return)
            chk.stateChanged.connect(self._update_refund_total)
            chk_l.addWidget(chk)
            self.table.setCellWidget(r, 0, chk_wrap)
            self.item_checks.append(chk)

            self.table.setItem(r, 1, QTableWidgetItem(item.get("product_name", "")))
            for col, val in ((2, row["sold"]), (3, row["remaining"])):
                cell = QTableWidgetItem(f"{val:g}")
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, col, cell)

            spin = QDoubleSpinBox()
            spin.setDecimals(0 if float(row["remaining"]).is_integer() else 2)
            spin.setRange(0, row["remaining"])
            spin.setValue(row["remaining"])
            spin.setEnabled(can_return)
            spin.valueChanged.connect(self._update_refund_total)
            self.table.setCellWidget(r, 4, spin)
            self.qty_spins.append(spin)

            refund_cell = QTableWidgetItem("—" if not can_return else f"{self.currency} 0.00")
            refund_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 5, refund_cell)

        layout.addWidget(self.table, stretch=1)

        self.txt_reason = QLineEdit(content)
        self.txt_reason.setFixedHeight(36)
        self.txt_reason.setPlaceholderText("Reason for return (e.g. defective, wrong size, changed mind)")
        layout.addWidget(self.txt_reason)

        total_row = QHBoxLayout()
        self.lbl_destination = QLabel("", content)
        self.lbl_destination.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        total_row.addWidget(self.lbl_destination)
        total_row.addStretch()
        self.lbl_refund = QLabel(f"Refund: {self.currency} 0.00", content)
        self.lbl_refund.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['danger']};")
        total_row.addWidget(self.lbl_refund)
        layout.addLayout(total_row)

        self.btn_confirm = AnimatedButton("Process Return && Refund", content, variant="danger", icon_name="undo", icon_color="#FFFFFF", icon_size=14)
        self.btn_confirm.setFixedHeight(44)
        self.btn_confirm.clicked.connect(self._process_return)
        layout.addWidget(self.btn_confirm)

        self.set_content_widget(content)
        self._update_refund_total()

    def _selected_lines(self):
        lines = []
        for r, row in enumerate(self.rows):
            if not self.item_checks[r].isChecked():
                continue
            qty = min(self.qty_spins[r].value(), row["remaining"])
            if qty <= 0:
                continue
            item = row["item"]
            lines.append({
                "row": r,
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name"),
                "quantity": qty,
                "unit_price": row["unit_refund"],
                "cost_price": float(item.get("cost_price") or 0.0),
                "refund_amount": round(row["unit_refund"] * qty, 2),
            })
        return lines

    def _update_refund_total(self):
        lines = {ln["row"]: ln for ln in self._selected_lines()}
        for r, row in enumerate(self.rows):
            if row["remaining"] <= 0:
                continue
            amt = lines[r]["refund_amount"] if r in lines else 0.0
            cell = QTableWidgetItem(f"{self.currency} {amt:,.2f}")
            cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 5, cell)
        total = round(sum(ln["refund_amount"] for ln in lines.values()), 2)
        self.lbl_refund.setText(f"Refund: {self.currency} {total:,.2f}")
        self.btn_confirm.setEnabled(total > 0)

        if self.order.get("customer_id") and self.order.get("payment_method") in ("credit", "split"):
            self.lbl_destination.setText("Deducted from customer's Khata balance first; any excess is paid in cash.")
        else:
            self.lbl_destination.setText("Refund is paid out in cash from the drawer.")

    def _process_return(self):
        lines = self._selected_lines()
        if not lines:
            QMessageBox.warning(self, "No Items", "Tick at least one item and set a return quantity above zero.")
            return
        total_refund = round(sum(ln["refund_amount"] for ln in lines), 2)

        reply = QMessageBox.question(
            self, "Confirm Return",
            f"Refund {self.currency} {total_refund:,.2f} for {len(lines)} item(s)?\n\nReturned items will be added back to stock.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        user = AuthController.get_current_user()
        returned_items = [{k: v for k, v in ln.items() if k != "row"} for ln in lines]
        OrderModel.process_return(
            order_id=self.order.get("id"),
            user_id=user["id"] if user else None,
            returned_items=returned_items,
            total_refund=total_refund,
            reason=self.txt_reason.text().strip() or "Not specified",
        )

        self.return_completed.emit()
        if self.on_complete:
            self.on_complete()
        QMessageBox.information(self, "Return Processed", f"Refund of {self.currency} {total_refund:,.2f} recorded. Stock has been restored.")
        self.hide_animated()
