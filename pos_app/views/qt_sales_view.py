"""
PySide6 Sales & Orders History View for OnesDev POS.
Browse past sales, search by customer/order number, view line items,
reprint thermal receipts, and process refunds/returns.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QFrame, QSplitter
)

from PySide6.QtGui import QColor
from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, clear_layout, order_status_display
from pos_app.utils.icon_helper import get_icon
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.receipt_printer import ReceiptPrinter
from pos_app.views.dialogs.qt_receipt_dialog import QtReceiptPreviewDialog
from pos_app.views.dialogs.qt_return_dialog import QtReturnDialog


class QtSalesView(QWidget):
    """Past Transactions & Order History Screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.selected_order = None
        self._build_ui()
        self.refresh_orders()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Filter Bar Card
        top_card = DropShadowCard(self, corner_radius=12)
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(12)

        lbl_search = QLabel(top_card)
        lbl_search.setPixmap(get_icon("search", color=COLORS["text_muted"], size=16).pixmap(16, 16))
        lbl_search.setFixedSize(18, 18)
        top_layout.addWidget(lbl_search)

        self.txt_search = QLineEdit(top_card)
        self.txt_search.setPlaceholderText("Search Order #, Customer Name, Phone...")
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self._on_search_changed)
        top_layout.addWidget(self.txt_search, stretch=1)

        self.cmb_method = QComboBox(top_card)
        self.cmb_method.addItems(["All Payment Methods", "Cash", "Credit", "Split"])
        self.cmb_method.setFixedHeight(36)
        self.cmb_method.currentIndexChanged.connect(self._on_search_changed)
        top_layout.addWidget(self.cmb_method)

        btn_refresh = AnimatedButton("Refresh", top_card, variant="secondary")
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self.refresh_orders)
        top_layout.addWidget(btn_refresh)

        main_layout.addWidget(top_card)

        # Split View: Left = Orders List, Right = Selected Order Details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left Orders Panel
        left_card = DropShadowCard(splitter, corner_radius=12)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        lbl_list_title = QLabel("PAST ORDERS & TRANSACTIONS", left_card)
        lbl_list_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 0.5px;")
        left_layout.addWidget(lbl_list_title)

        self.table_orders = QTableWidget(left_card)
        self.table_orders.setColumnCount(6)
        self.table_orders.setHorizontalHeaderLabels(["Order #", "Customer", "Date", "Total", "Method", "Status"])
        hdr = self.table_orders.horizontalHeader()
        for col in (0, 2, 3, 4, 5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_orders.verticalHeader().setVisible(False)
        self.table_orders.setAlternatingRowColors(True)
        self.table_orders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_orders.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_orders.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 12px;
                padding: 8px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                font-size: 13px;
            }}
        """)
        self.table_orders.itemSelectionChanged.connect(self._on_order_selected)
        left_layout.addWidget(self.table_orders)
        splitter.addWidget(left_card)

        # Right Order Details Panel
        self.right_card = DropShadowCard(splitter, corner_radius=12)
        self.right_layout = QVBoxLayout(self.right_card)
        self.right_layout.setContentsMargins(16, 16, 16, 16)
        self.right_layout.setSpacing(12)
        self._render_empty_details()
        splitter.addWidget(self.right_card)

        splitter.setSizes([760, 440])
        main_layout.addWidget(splitter, stretch=1)

    def _render_empty_details(self):
        clear_layout(self.right_layout)

        lbl_empty = QLabel("Select any order from the table to inspect receipt details and line items.", self.right_card)
        lbl_empty.setWordWrap(True)
        lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        self.right_layout.addWidget(lbl_empty)

    def _on_search_changed(self):
        self.refresh_orders()

    def refresh_orders(self):
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        search_query = self.txt_search.text().strip()
        method_filter = self.cmb_method.currentText()
        method = None if method_filter == "All Payment Methods" else method_filter.lower()

        orders = OrderModel.list_orders(search=search_query, payment_method=method, limit=100)
        self.orders_cache = orders
        self.table_orders.setRowCount(len(orders))

        for r, o in enumerate(orders):
            self.table_orders.setItem(r, 0, QTableWidgetItem(o.get("order_number", "")))
            cust = o.get("customer_name") or "Walk-in Customer"
            self.table_orders.setItem(r, 1, QTableWidgetItem(cust))

            dt_str = o.get("created_at", "")[5:16]
            self.table_orders.setItem(r, 2, QTableWidgetItem(dt_str))

            tot_item = QTableWidgetItem(f"{self.currency} {o.get('total', 0.0):,.2f}")
            tot_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_orders.setItem(r, 3, tot_item)

            method_item = QTableWidgetItem((o.get("payment_method") or "cash").upper())
            method_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_orders.setItem(r, 4, method_item)

            status_label, status_color = order_status_display(o.get("status"))
            status_item = QTableWidgetItem(status_label)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(status_color))
            self.table_orders.setItem(r, 5, status_item)

    def _on_order_selected(self):
        selected_rows = self.table_orders.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < len(self.orders_cache):
            order = self.orders_cache[row]
            self._render_order_details(order)

    def _render_order_details(self, order: dict):
        clear_layout(self.right_layout)

        # Full order details with items
        full_order = OrderModel.get_order_by_id(order["id"]) or order

        # Order Header
        lbl_ord_num = QLabel(f"Order #{full_order.get('order_number')}", self.right_card)
        lbl_ord_num.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']};")
        self.right_layout.addWidget(lbl_ord_num)

        dt_info = f"Date: {full_order.get('created_at', '')}  |  Cashier: {full_order.get('cashier_name', 'Admin')}"
        lbl_info = QLabel(dt_info, self.right_card)
        lbl_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.right_layout.addWidget(lbl_info)

        cust_row = QHBoxLayout()
        cust_info = f"Customer: {full_order.get('customer_name') or 'Walk-in Customer'} ({full_order.get('payment_method', 'cash').upper()})"
        lbl_cust = QLabel(cust_info, self.right_card)
        lbl_cust.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600;")
        cust_row.addWidget(lbl_cust)
        cust_row.addStretch()
        status_label, status_color = order_status_display(full_order.get("status"))
        lbl_status = QLabel(status_label, self.right_card)
        lbl_status.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: 700; border: 1px solid {status_color}; border-radius: 9px; padding: 2px 10px;")
        cust_row.addWidget(lbl_status)
        self.right_layout.addLayout(cust_row)

        # Line Items Table
        items_table = QTableWidget(self.right_card)
        items = full_order.get("items", [])
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels(["Item", "Qty", "Price", "Total"])
        items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            items_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        items_table.verticalHeader().setVisible(False)
        items_table.setRowCount(len(items))
        items_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 11px;
                padding: 6px;
                border: none;
            }}
        """)

        for i, item in enumerate(items):
            items_table.setItem(i, 0, QTableWidgetItem(item.get("product_name", "")))
            q_item = QTableWidgetItem(f"{item.get('quantity', 1):g}")
            q_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            items_table.setItem(i, 1, q_item)

            p_item = QTableWidgetItem(f"{self.currency} {item.get('unit_price', 0.0):,.2f}")
            p_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(i, 2, p_item)

            t_item = QTableWidgetItem(f"{self.currency} {item.get('total', 0.0):,.2f}")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(i, 3, t_item)

        self.right_layout.addWidget(items_table, stretch=1)

        # Totals breakdown
        totals_card = QFrame(self.right_card)
        totals_card.setObjectName("OrderTotalsCard")
        totals_card.setStyleSheet(f"QFrame#OrderTotalsCard {{ background-color: {COLORS['bg_hover']}; border-radius: 8px; }}")
        tot_l = QVBoxLayout(totals_card)
        tot_l.setSpacing(4)

        subtot = full_order.get("subtotal", 0.0)
        disc = full_order.get("discount_amount", 0.0)
        tax = full_order.get("tax_amount", 0.0)
        grand = full_order.get("total", 0.0)
        paid = full_order.get("amount_paid", 0.0)
        change = full_order.get("change_due", 0.0)

        tot_l.addWidget(QLabel(f"Subtotal: {self.currency} {subtot:,.2f}"))
        if disc > 0:
            tot_l.addWidget(QLabel(f"Discount: -{self.currency} {disc:,.2f}"))
        if tax > 0:
            tot_l.addWidget(QLabel(f"Tax / VAT: +{self.currency} {tax:,.2f}"))

        lbl_grand = QLabel(f"Grand Total: {self.currency} {grand:,.2f}")
        lbl_grand.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['primary']};")
        tot_l.addWidget(lbl_grand)

        tot_l.addWidget(QLabel(f"Amount Paid: {self.currency} {paid:,.2f}  |  Change Due: {self.currency} {change:,.2f}"))
        refunded = OrderModel.get_order_refund_total(full_order["id"]) if full_order.get("id") else 0.0
        if refunded > 0:
            lbl_ref = QLabel(f"Refunded: -{self.currency} {refunded:,.2f}")
            lbl_ref.setStyleSheet(f"color: {COLORS['danger']}; font-weight: 600;")
            tot_l.addWidget(lbl_ref)
        self.right_layout.addWidget(totals_card)

        # Action Buttons: Preview & Reprint Receipt
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        btn_preview = AnimatedButton("Preview", self.right_card, variant="secondary", icon_name="copy")
        btn_preview.setFixedHeight(38)
        btn_preview.clicked.connect(lambda: self._preview_receipt(full_order))
        btn_box.addWidget(btn_preview)

        btn_reprint = AnimatedButton("Print", self.right_card, variant="primary", icon_name="printer", icon_color="#FFFFFF")
        btn_reprint.setFixedHeight(38)
        btn_reprint.clicked.connect(lambda: self._reprint_receipt(full_order))
        btn_box.addWidget(btn_reprint)

        if full_order.get("status") != "returned":
            btn_return = AnimatedButton("Return", self.right_card, variant="danger", icon_name="undo", icon_color="#FFFFFF", icon_size=14)
            btn_return.setFixedHeight(38)
            btn_return.clicked.connect(lambda: self._open_return_dialog(full_order))
            btn_box.addWidget(btn_return)

        self.right_layout.addLayout(btn_box)

    def _preview_receipt(self, order: dict):
        top_window = self.window()
        dlg = QtReceiptPreviewDialog(top_window, order)
        dlg.show_animated()

    def _reprint_receipt(self, order: dict):
        ok, msg = ReceiptPrinter.print_receipt(order)
        if ok:
            QMessageBox.information(self, "Receipt Printed", "Receipt printed successfully.")
        else:
            QMessageBox.warning(self, "Print Notice", msg)

    def _open_return_dialog(self, order: dict):
        top_window = self.window()
        self.dlg_return = QtReturnDialog(top_window, order, on_complete=lambda: self._after_return(order["id"]))
        self.dlg_return.show_animated()

    def _after_return(self, order_id):
        self.refresh_orders()
        refreshed = OrderModel.get_order_by_id(order_id)
        if refreshed:
            self._render_order_details(refreshed)
