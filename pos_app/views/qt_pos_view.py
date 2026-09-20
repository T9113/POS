"""
PySide6 Point of Sale (POS) View for OnesDev POS.
Barcode scanning, quick add, category pill filters, wholesale toggle,
interactive cart management, customer Khata selection, and checkout.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QGridLayout, QMessageBox
)
from PySide6.QtGui import QFont, QColor

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard
from pos_app.controllers.cart_controller import CartController
from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.qt_payment_dialog import QtPaymentDialog
from pos_app.views.dialogs.qt_customer_dialog import QtCustomerDialog


class QtPOSView(QWidget):
    """Modern Point of Sale interface with quick barcode entry and interactive cart."""
    order_completed = Signal(dict)
    sale_completed = order_completed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cart_controller = CartController()
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.active_category_id = None
        self.is_wholesale = False
        self._build_ui()
        self.refresh_catalog()

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # ==========================================
        # LEFT PANEL: Search, Categories, Products
        # ==========================================
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        # Search Bar
        search_card = DropShadowCard(self, corner_radius=10, blur_radius=12, offset_y=2, opacity=15)
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(12, 10, 12, 10)

        lbl_s_icon = QLabel("🔍", search_card)
        lbl_s_icon.setStyleSheet("font-size: 16px;")
        search_layout.addWidget(lbl_s_icon)

        self.txt_search = QLineEdit(search_card)
        self.txt_search.setPlaceholderText("Scan barcode or search product name / SKU (Press Enter to quick-add)...")
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self._on_search_text_changed)
        self.txt_search.returnPressed.connect(self._on_barcode_enter)
        search_layout.addWidget(self.txt_search)

        left_panel.addWidget(search_card)

        # Categories Horizontal Filter Bar
        self.cat_scroll = QScrollArea(self)
        self.cat_scroll.setFixedHeight(48)
        self.cat_scroll.setWidgetResizable(True)
        self.cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cat_scroll.setStyleSheet("border: none; background: transparent;")

        self.cat_container = QWidget()
        self.cat_layout = QHBoxLayout(self.cat_container)
        self.cat_layout.setContentsMargins(0, 4, 0, 4)
        self.cat_layout.setSpacing(8)
        self.cat_scroll.setWidget(self.cat_container)
        left_panel.addWidget(self.cat_scroll)

        # Products Grid Container (Scrollable)
        self.prod_scroll = QScrollArea(self)
        self.prod_scroll.setWidgetResizable(True)
        self.prod_scroll.setStyleSheet("border: none; background: transparent;")

        self.prod_grid_widget = QWidget()
        self.prod_grid_layout = QGridLayout(self.prod_grid_widget)
        self.prod_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.prod_grid_layout.setSpacing(10)
        self.prod_scroll.setWidget(self.prod_grid_widget)

        left_panel.addWidget(self.prod_scroll)
        root_layout.addLayout(left_panel, stretch=6)

        # ==========================================
        # RIGHT PANEL: Shopping Cart & Checkout
        # ==========================================
        cart_card = DropShadowCard(self, corner_radius=12, blur_radius=20, offset_y=4, opacity=25)
        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(18, 16, 18, 16)
        cart_layout.setSpacing(12)

        # Cart Header
        cart_header = QHBoxLayout()
        lbl_cart = QLabel("🛒 Current Sale Cart", cart_card)
        lbl_cart.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        cart_header.addWidget(lbl_cart)

        cart_header.addStretch()

        # Wholesale toggle
        self.btn_wholesale = AnimatedButton("🏢 Retail", cart_card, variant="secondary")
        self.btn_wholesale.setFixedHeight(30)
        self.btn_wholesale.clicked.connect(self._toggle_wholesale)
        cart_header.addWidget(self.btn_wholesale)

        cart_layout.addLayout(cart_header)

        # Customer Khata Selector Row
        cust_row = QHBoxLayout()
        cust_row.setSpacing(8)

        self.cmb_customer = QComboBox(cart_card)
        self.cmb_customer.setFixedHeight(34)
        self.cmb_customer.addItem("👤 Walk-in Customer (No Khata)", None)
        cust_row.addWidget(self.cmb_customer, stretch=1)

        btn_new_cust = AnimatedButton("➕ New", cart_card, variant="secondary")
        btn_new_cust.setFixedHeight(34)
        btn_new_cust.clicked.connect(self._open_new_customer_dialog)
        cust_row.addWidget(btn_new_cust)

        cart_layout.addLayout(cust_row)

        # Cart Items Table
        self.cart_table = QTableWidget(cart_card)
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Price", "Qty", "Total", ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cart_table.verticalHeader().setVisible(False)
        cart_layout.addWidget(self.cart_table)

        # Discount Row
        disc_row = QHBoxLayout()
        lbl_d = QLabel("Discount (Rs / %):", cart_card)
        lbl_d.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        disc_row.addWidget(lbl_d)

        self.txt_discount = QLineEdit(cart_card)
        self.txt_discount.setPlaceholderText("0.00")
        self.txt_discount.setFixedHeight(30)
        self.txt_discount.setFixedWidth(80)
        self.txt_discount.textChanged.connect(self._apply_discount)
        disc_row.addWidget(self.txt_discount)
        disc_row.addStretch()

        cart_layout.addLayout(disc_row)

        # Totals Card
        totals_frame = QFrame(cart_card)
        totals_frame.setStyleSheet(f"background-color: {COLORS['bg_hover']}; border-radius: 8px; padding: 6px;")
        tot_layout = QVBoxLayout(totals_frame)
        tot_layout.setContentsMargins(12, 8, 12, 8)
        tot_layout.setSpacing(4)

        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Subtotal:", totals_frame))
        self.lbl_subtotal = QLabel(f"{self.currency} 0.00", totals_frame)
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_subtotal.setStyleSheet("font-family: Consolas, monospace; font-weight: bold;")
        sub_row.addWidget(self.lbl_subtotal)
        tot_layout.addLayout(sub_row)

        grand_row = QHBoxLayout()
        lbl_g = QLabel("TOTAL DUE:", totals_frame)
        lbl_g.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COLORS['primary']};")
        grand_row.addWidget(lbl_g)

        self.lbl_grand_total = QLabel(f"{self.currency} 0.00", totals_frame)
        self.lbl_grand_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_grand_total.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['primary']}; font-family: Consolas, monospace;")
        grand_row.addWidget(self.lbl_grand_total)
        tot_layout.addLayout(grand_row)

        cart_layout.addWidget(totals_frame)

        # Bottom Action Bar
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        btn_void = AnimatedButton("Void", cart_card, variant="danger_subtle")
        btn_void.setFixedHeight(38)
        btn_void.clicked.connect(self._void_cart)
        action_row.addWidget(btn_void)

        btn_hold = AnimatedButton("Hold", cart_card, variant="secondary")
        btn_hold.setFixedHeight(38)
        btn_hold.clicked.connect(self._hold_order)
        action_row.addWidget(btn_hold)

        cart_layout.addLayout(action_row)

        self.btn_pay = AnimatedButton(f"Complete Sale (F12)  ➔", cart_card, variant="success")
        self.btn_pay.setFixedHeight(48)
        self.btn_pay.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success_hover']};
            }}
        """)
        self.btn_pay.clicked.connect(self._open_payment_dialog)
        cart_layout.addWidget(self.btn_pay)

        root_layout.addWidget(cart_card, stretch=4)

    def refresh_catalog(self):
        """Loads categories, customers, and products."""
        self._load_categories()
        self._load_customers()
        self._load_products()

    def _load_categories(self):
        # Clear existing category buttons
        while self.cat_layout.count() > 0:
            item = self.cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        btn_all = AnimatedButton("🏷️ All Products", variant="primary" if self.active_category_id is None else "secondary")
        btn_all.setFixedHeight(34)
        btn_all.clicked.connect(lambda: self._select_category(None))
        self.cat_layout.addWidget(btn_all)

        cats = CategoryModel.get_all()
        for c in cats:
            is_active = self.active_category_id == c["id"]
            btn = AnimatedButton(c["name"], variant="primary" if is_active else "secondary")
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, cid=c["id"]: self._select_category(cid))
            self.cat_layout.addWidget(btn)

        self.cat_layout.addStretch()

    def _select_category(self, cat_id):
        self.active_category_id = cat_id
        self._load_categories()
        self._load_products()

    def _load_customers(self):
        self.cmb_customer.clear()
        self.cmb_customer.addItem("👤 Walk-in Customer (No Khata)", None)
        custs = CustomerModel.get_all()
        for c in custs:
            bal = c.get("balance", 0.0)
            bal_str = f" [Due: {self.currency} {bal:,.2f}]" if bal > 0 else ""
            self.cmb_customer.addItem(f"👤 {c['name']}{bal_str}", c)

    def _load_products(self):
        # Clear products grid
        while self.prod_grid_layout.count() > 0:
            item = self.prod_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.txt_search.text().strip()
        prods = ProductModel.search_products(query, category_id=self.active_category_id, limit=30)

        cols = 3
        for idx, p in enumerate(prods):
            r = idx // cols
            c = idx % cols
            card = self._create_product_tile(p)
            self.prod_grid_layout.addWidget(card, r, c)

    def _create_product_tile(self, p: dict) -> QFrame:
        tile = DropShadowCard(self.prod_grid_widget, corner_radius=10, blur_radius=10, offset_y=2, opacity=15)
        tile.setFixedHeight(115)
        tile.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(tile)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Top row: Name + Category badge
        lbl_name = QLabel(p["name"], tile)
        lbl_name.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLORS['text_primary']};")
        lbl_name.setWordWrap(True)
        layout.addWidget(lbl_name)

        # SKU / Barcode
        lbl_sub = QLabel(f"SKU: {p.get('sku') or '-'} • {p.get('unit', 'pc')}", tile)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        layout.addWidget(lbl_sub)

        layout.addStretch()

        # Bottom row: Price & Stock
        price = p["wholesale_price"] if self.is_wholesale and p.get("wholesale_price") else p["selling_price"]
        bot_row = QHBoxLayout()

        lbl_price = QLabel(f"{self.currency} {price:,.2f}", tile)
        lbl_price.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['primary']}; font-family: Consolas, monospace;")
        bot_row.addWidget(lbl_price)

        bot_row.addStretch()

        stock = p.get("current_stock", 0.0)
        min_s = p.get("min_stock", 5.0)
        stock_col = COLORS["danger"] if stock <= min_s else COLORS["success"]
        lbl_stock = QLabel(f"Stock: {int(stock)}", tile)
        lbl_stock.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {stock_col}; background: {COLORS['bg_hover']}; padding: 2px 6px; border-radius: 4px;")
        bot_row.addWidget(lbl_stock)

        layout.addLayout(bot_row)

        # Click to add item to cart
        tile.mousePressEvent = lambda e, prod=p: self._add_product_to_cart(prod)
        return tile

    def _on_search_text_changed(self):
        self._load_products()

    def _on_barcode_enter(self):
        term = self.txt_search.text().strip()
        if not term:
            return
        prod = ProductModel.get_by_barcode_or_sku(term)
        if prod:
            self._add_product_to_cart(prod)
            self.txt_search.clear()
        else:
            prods = ProductModel.search_products(term, limit=1)
            if prods:
                self._add_product_to_cart(prods[0])
                self.txt_search.clear()

    def _add_product_to_cart(self, p: dict):
        price = p["wholesale_price"] if self.is_wholesale and p.get("wholesale_price") else p["selling_price"]
        self.cart_controller.add_item(
            product_id=p["id"],
            name=p["name"],
            price=price,
            cost_price=p.get("cost_price", 0.0),
            quantity=1,
            unit=p.get("unit", "pc")
        )
        self._render_cart()

    def _render_cart(self):
        items = self.cart_controller.get_items()
        self.cart_table.setRowCount(len(items))

        for row, itm in enumerate(items):
            # 0: Name
            item_name = QTableWidgetItem(itm["name"])
            item_name.setFlags(item_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 0, item_name)

            # 1: Price
            item_p = QTableWidgetItem(f"{itm['price']:,.2f}")
            item_p.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_p.setFlags(item_p.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 1, item_p)

            # 2: Qty Stepper (- Qty +)
            qty_frame = QWidget()
            qty_layout = QHBoxLayout(qty_frame)
            qty_layout.setContentsMargins(2, 2, 2, 2)
            qty_layout.setSpacing(4)

            btn_minus = AnimatedButton("-", variant="secondary")
            btn_minus.setFixedSize(22, 22)
            btn_minus.clicked.connect(lambda _, pid=itm["product_id"]: self._adjust_qty(pid, -1))
            qty_layout.addWidget(btn_minus)

            lbl_q = QLabel(str(itm["quantity"]), qty_frame)
            lbl_q.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_q.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 20px;")
            qty_layout.addWidget(lbl_q)

            btn_plus = AnimatedButton("+", variant="secondary")
            btn_plus.setFixedSize(22, 22)
            btn_plus.clicked.connect(lambda _, pid=itm["product_id"]: self._adjust_qty(pid, 1))
            qty_layout.addWidget(btn_plus)

            self.cart_table.setCellWidget(row, 2, qty_frame)

            # 3: Subtotal
            tot = itm["price"] * itm["quantity"]
            item_tot = QTableWidgetItem(f"{tot:,.2f}")
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_tot.setFlags(item_tot.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 3, item_tot)

            # 4: Delete Button
            btn_del = AnimatedButton("✕", variant="danger_subtle")
            btn_del.setFixedSize(24, 24)
            btn_del.clicked.connect(lambda _, pid=itm["product_id"]: self._remove_from_cart(pid))
            self.cart_table.setCellWidget(row, 4, btn_del)

        # Update totals
        subtotal = self.cart_controller.get_subtotal()
        grand_total = self.cart_controller.get_grand_total()
        self.lbl_subtotal.setText(f"{self.currency} {subtotal:,.2f}")
        self.lbl_grand_total.setText(f"{self.currency} {grand_total:,.2f}")

    def _adjust_qty(self, product_id, delta):
        self.cart_controller.adjust_quantity(product_id, delta)
        self._render_cart()

    def _remove_from_cart(self, product_id):
        self.cart_controller.remove_item(product_id)
        self._render_cart()

    def _apply_discount(self):
        txt = self.txt_discount.text().strip()
        try:
            val = float(txt or 0.0)
            self.cart_controller.set_discount(val)
        except ValueError:
            self.cart_controller.set_discount(0.0)
        self._render_cart()

    def _toggle_wholesale(self):
        self.is_wholesale = not self.is_wholesale
        self.btn_wholesale.setText("🏢 Wholesale" if self.is_wholesale else "🏢 Retail")
        self.btn_wholesale.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: #FFFFFF;" if self.is_wholesale else ""
        )
        self._load_products()

    def _void_cart(self):
        if not self.cart_controller.get_items():
            return
        if QMessageBox.question(self, "Void Cart", "Are you sure you want to void all items in the cart?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.cart_controller.clear()
            self._render_cart()

    def _hold_order(self):
        items = self.cart_controller.get_items()
        if not items:
            QMessageBox.information(self, "Hold Order", "Cart is empty. Nothing to put on hold.")
            return
        self.cart_controller.hold_current_order()
        self.cart_controller.clear()
        self._render_cart()
        QMessageBox.information(self, "Order Held", "Order has been placed on hold successfully.")

    def _open_new_customer_dialog(self):
        top_window = self.window()
        self.dlg_cust = QtCustomerDialog(top_window, on_complete=self._on_customer_added)
        self.dlg_cust.show_animated()

    def _on_customer_added(self, customer):
        self._load_customers()
        # Find index of newly added customer and select it
        for idx in range(self.cmb_customer.count()):
            cdata = self.cmb_customer.itemData(idx)
            if cdata and cdata.get("id") == customer.get("id"):
                self.cmb_customer.setCurrentIndex(idx)
                break

    def _open_payment_dialog(self):
        items = self.cart_controller.get_items()
        if not items:
            QMessageBox.warning(self, "Empty Cart", "Please add at least one product before proceeding to payment!")
            return

        customer = self.cmb_customer.currentData()
        cart_data = {
            "items": items,
            "subtotal": self.cart_controller.get_subtotal(),
            "discount": self.cart_controller.get_discount(),
            "grand_total": self.cart_controller.get_grand_total()
        }

        top_window = self.window()
        self.dlg_pay = QtPaymentDialog(top_window, cart_data=cart_data, customer=customer, on_complete=self._on_payment_completed)
        self.dlg_pay.show_animated()

    def _on_payment_completed(self, order):
        self.cart_controller.clear()
        self.txt_discount.clear()
        self._render_cart()
        self.refresh_catalog()
        self.sale_completed.emit(order)
