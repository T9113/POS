"""
PySide6 Hold Orders Dialog for OnesDev POS.
Displays parked/held orders and allows recall or deletion.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QPushButton
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.icon_helper import get_icon


class QtHoldOrdersDialog(SmoothModalOverlay):
    """Modal dialog listing held/parked orders for recall."""
    order_recalled = Signal(dict)

    def __init__(self, parent, on_recall=None):
        super().__init__(parent, target_width=660, target_height=480)
        self.on_recall = on_recall
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        title_row = QHBoxLayout()
        ico = QLabel(content)
        ico.setPixmap(get_icon("pause", color=COLORS["primary"], size=20).pixmap(20, 20))
        ico.setFixedSize(22, 22)
        title_row.addWidget(ico)

        lbl_title = QLabel("Held / Parked Orders", content)
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

        # Table
        self.table = QTableWidget(content)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "Customer", "Items", "Total", "Held At"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (0, 2, 3, 4):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
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
                padding: 8px; border: none;
                border-bottom: 2px solid {COLORS['border']};
            }}
            QTableWidget::item {{ padding: 6px 10px; font-size: 13px; }}
        """)
        layout.addWidget(self.table, stretch=1)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_recall = AnimatedButton("Recall to Cart", content, variant="primary", icon_name="cart", icon_color="#FFFFFF", icon_size=14)
        self.btn_recall.setFixedHeight(40)
        self.btn_recall.clicked.connect(self._recall_selected)
        btn_row.addWidget(self.btn_recall)

        self.btn_delete = AnimatedButton("Delete", content, variant="danger", icon_name="trash", icon_color="#FFFFFF", icon_size=14)
        self.btn_delete.setFixedHeight(40)
        self.btn_delete.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.btn_delete)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.set_content_widget(content)

    def show_animated(self):
        self._refresh_list()
        super().show_animated()

    def _refresh_list(self):
        orders = OrderModel.list_held_orders()
        self.held_orders = orders
        self.table.setRowCount(len(orders))

        for r, o in enumerate(orders):
            self.table.setItem(r, 0, QTableWidgetItem(str(o.get("id", ""))))

            cust = o.get("customer_name") or "Walk-in"
            self.table.setItem(r, 1, QTableWidgetItem(cust))

            cart = o.get("cart_data", {})
            items = cart.get("items", [])
            self.table.setItem(r, 2, QTableWidgetItem(f"{len(items)} item(s)"))

            total = sum(float(i.get("price", 0)) * float(i.get("quantity", 1)) for i in items)
            total_item = QTableWidgetItem(f"{self.currency} {total:,.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 3, total_item)

            held_at = (o.get("created_at") or "")[5:16]
            self.table.setItem(r, 4, QTableWidgetItem(held_at))

        self.table.clearSpans()
        if not orders:
            self.table.setRowCount(1)
            empty = QTableWidgetItem("No held orders. Use Hold on the POS screen to park a sale.")
            empty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setForeground(QColor(COLORS["text_muted"]))
            self.table.setItem(0, 0, empty)
            self.table.setSpan(0, 0, 1, 5)
        self.btn_recall.setEnabled(bool(orders))
        self.btn_delete.setEnabled(bool(orders))

    def _get_selected_order(self):
        rows = self.table.selectedIndexes()
        if not rows:
            QMessageBox.information(self, "Selection", "Please select a held order first.")
            return None
        row = rows[0].row()
        if row < len(self.held_orders):
            return self.held_orders[row]
        return None

    def _recall_selected(self):
        order = self._get_selected_order()
        if not order:
            return
        cart_data = order.get("cart_data", {})
        if self.on_recall and self.on_recall(cart_data, order.get("customer_id")) is False:
            return
        OrderModel.delete_held_order(order["id"])
        self.order_recalled.emit(cart_data)
        self.hide_animated()

    def _delete_selected(self):
        order = self._get_selected_order()
        if not order:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete held order #{order['id']}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            OrderModel.delete_held_order(order["id"])
            self._refresh_list()
