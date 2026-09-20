"""
PySide6 Inventory View for OnesDev POS.
Stock levels, low stock alerts, stock-in purchases, adjustments log, and suppliers directory.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QDoubleSpinBox, QMessageBox
)
from PySide6.QtGui import QColor

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard
from pos_app.models.product_model import ProductModel
from pos_app.models.supplier_model import SupplierModel
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.icon_helper import get_icon


class QtInventoryView(QWidget):
    """Inventory Management screen with tabbed sections and stock valuation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # 1. Top KPI Valuation Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.card_val = self._create_kpi_card("INVENTORY VALUATION", f"{self.currency} 0.00", "Total purchase cost value of on-hand stock", COLORS["primary"])
        kpi_row.addWidget(self.card_val)

        self.card_low = self._create_kpi_card("ITEMS NEEDING REORDER", "0 Products", "Products at or below minimum stock", COLORS["danger"])
        kpi_row.addWidget(self.card_low)

        self.card_count = self._create_kpi_card("TOTAL CATALOG PRODUCTS", "0 Items", "Active product items tracked in system", COLORS["text_primary"])
        kpi_row.addWidget(self.card_count)

        layout.addLayout(kpi_row)

        # 2. Main Tabs
        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)

        # Tab 1: Low Stock & Reorder
        self.tab_low = QWidget()
        self._build_low_stock_tab()
        self.tabs.addTab(self.tab_low, get_icon("alert", COLORS["warning"], 16), "Low Stock & Reorder")

        # Tab 2: Purchases / Stock-In
        self.tab_stockin = QWidget()
        self._build_stockin_tab()
        self.tabs.addTab(self.tab_stockin, get_icon("download", COLORS["text_secondary"], 16), "Purchases / Stock-In")

        # Tab 3: Suppliers Directory
        self.tab_suppliers = QWidget()
        self._build_suppliers_tab()
        self.tabs.addTab(self.tab_suppliers, get_icon("building", COLORS["text_secondary"], 16), "Suppliers Directory")

        layout.addWidget(self.tabs)

    def _create_kpi_card(self, title, val, sub, color) -> QFrame:
        card = DropShadowCard(self, corner_radius=10, blur_radius=12, offset_y=2, opacity=15)
        l = QVBoxLayout(card)
        l.setContentsMargins(16, 12, 16, 12)
        l.setSpacing(3)

        lbl_t = QLabel(title, card)
        lbl_t.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['text_secondary']};")
        l.addWidget(lbl_t)

        lbl_v = QLabel(val, card)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color}; font-family: Consolas, monospace;")
        l.addWidget(lbl_v)

        lbl_s = QLabel(sub, card)
        lbl_s.setObjectName("sub")
        lbl_s.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        l.addWidget(lbl_s)
        return card

    # --- TAB 1: Low Stock ---
    def _build_low_stock_tab(self):
        l = QVBoxLayout(self.tab_low)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(10)

        self.tbl_low = QTableWidget(self.tab_low)
        self.tbl_low.setColumnCount(6)
        self.tbl_low.setHorizontalHeaderLabels([
            "Barcode / SKU", "Product Name", "Category", "Current Stock", "Min Reorder Level", "Quick Restock"
        ])
        self.tbl_low.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_low.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_low.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_low.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_low.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_low.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_low.verticalHeader().setVisible(False)
        l.addWidget(self.tbl_low)

    # --- TAB 2: Stock-In Purchases ---
    def _build_stockin_tab(self):
        l = QVBoxLayout(self.tab_stockin)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(12)

        form_card = DropShadowCard(self.tab_stockin, corner_radius=10, blur_radius=12, offset_y=2, opacity=15)
        fl = QHBoxLayout(form_card)
        fl.setContentsMargins(14, 12, 14, 12)
        fl.setSpacing(10)

        self.cmb_p_prod = QComboBox(form_card)
        self.cmb_p_prod.setFixedHeight(36)
        fl.addWidget(self.cmb_p_prod, stretch=2)

        self.cmb_p_supp = QComboBox(form_card)
        self.cmb_p_supp.setFixedHeight(36)
        fl.addWidget(self.cmb_p_supp, stretch=2)

        self.spn_p_qty = QDoubleSpinBox(form_card)
        self.spn_p_qty.setMaximum(10000.0)
        self.spn_p_qty.setValue(10.0)
        self.spn_p_qty.setFixedHeight(36)
        fl.addWidget(self.spn_p_qty)

        btn_commit = AnimatedButton("Add Stock-In", form_card, variant="primary", icon_name="download")
        btn_commit.setFixedHeight(36)
        btn_commit.clicked.connect(self._add_stock_in)
        fl.addWidget(btn_commit)

        l.addWidget(form_card)

        self.tbl_adjust = QTableWidget(self.tab_stockin)
        self.tbl_adjust.setColumnCount(5)
        self.tbl_adjust.setHorizontalHeaderLabels(["Date & Time", "Product", "Type / Note", "Quantity Change", "Recorded By"])
        self.tbl_adjust.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_adjust.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_adjust.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_adjust.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_adjust.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_adjust.verticalHeader().setVisible(False)
        l.addWidget(self.tbl_adjust)

    # --- TAB 3: Suppliers Directory ---
    def _build_suppliers_tab(self):
        l = QVBoxLayout(self.tab_suppliers)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addStretch()

        self.tbl_supp = QTableWidget(self.tab_suppliers)
        self.tbl_supp.setColumnCount(4)
        self.tbl_supp.setHorizontalHeaderLabels(["Supplier Company Name", "Contact Phone", "Email", "Address"])
        self.tbl_supp.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_supp.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_supp.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_supp.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_supp.verticalHeader().setVisible(False)
        l.addWidget(self.tbl_supp)

    def refresh_data(self):
        """Reloads all inventory data."""
        prods = ProductModel.get_all()
        total_val = sum(p.get("cost_price", 0.0) * p.get("current_stock", 0.0) for p in prods)
        low_items = ProductModel.get_low_stock_products()

        # Update KPI Cards
        self.card_val.findChild(QLabel, "val").setText(f"{self.currency} {total_val:,.2f}")
        self.card_low.findChild(QLabel, "val").setText(f"{len(low_items)} Products")
        self.card_count.findChild(QLabel, "val").setText(f"{len(prods)} Items")

        # Load Low stock table
        self.tbl_low.setRowCount(len(low_items))
        for row, p in enumerate(low_items):
            code = p.get("barcode") or p.get("sku") or "-"
            it_c = QTableWidgetItem(code)
            it_c.setFlags(it_c.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_low.setItem(row, 0, it_c)

            it_n = QTableWidgetItem(p["name"])
            it_n.setFlags(it_n.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_low.setItem(row, 1, it_n)

            it_cat = QTableWidgetItem(p.get("category_name") or "-")
            it_cat.setFlags(it_cat.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_low.setItem(row, 2, it_cat)

            stk = p.get("current_stock", 0.0)
            it_stk = QTableWidgetItem(f"{stk:g} {p.get('unit', 'pc')}")
            it_stk.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_stk.setForeground(QColor(COLORS["danger"]))
            it_stk.setFlags(it_stk.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_low.setItem(row, 3, it_stk)

            min_s = p.get("min_stock", 5.0)
            it_min = QTableWidgetItem(f"{min_s:g} {p.get('unit', 'pc')}")
            it_min.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_min.setFlags(it_min.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_low.setItem(row, 4, it_min)

            btn_restock = AnimatedButton("+25 Stock", variant="primary")
            btn_restock.setFixedHeight(26)
            btn_restock.setToolTip("Quickly add 25 units to stock")
            btn_restock.clicked.connect(lambda _, pid=p["id"]: self._quick_restock(pid, 25))
            self.tbl_low.setCellWidget(row, 5, btn_restock)

        # Load Comboboxes for Stock-in
        self.cmb_p_prod.clear()
        for p in prods:
            self.cmb_p_prod.addItem(f"{p['name']} (Current: {int(p.get('current_stock', 0))})", p["id"])

        supps = SupplierModel.get_all()
        self.cmb_p_supp.clear()
        for s in supps:
            self.cmb_p_supp.addItem(s["name"], s["id"])

        # Load Suppliers table
        self.tbl_supp.setRowCount(len(supps))
        for row, s in enumerate(supps):
            it_n = QTableWidgetItem(s["name"])
            it_n.setFlags(it_n.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_supp.setItem(row, 0, it_n)

            it_p = QTableWidgetItem(s.get("phone", ""))
            it_p.setFlags(it_p.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_supp.setItem(row, 1, it_p)

            it_e = QTableWidgetItem(s.get("email", ""))
            it_e.setFlags(it_e.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_supp.setItem(row, 2, it_e)

            it_a = QTableWidgetItem(s.get("address", ""))
            it_a.setFlags(it_a.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.tbl_supp.setItem(row, 3, it_a)

    def _quick_restock(self, prod_id, add_qty):
        p = ProductModel.get_by_id(prod_id)
        if p:
            new_stk = p["current_stock"] + add_qty
            ProductModel.update_stock(prod_id, new_stk)
            self.refresh_data()

    def _add_stock_in(self):
        prod_id = self.cmb_p_prod.currentData()
        if not prod_id:
            return
        qty = self.spn_p_qty.value()
        p = ProductModel.get_by_id(prod_id)
        if p:
            new_stk = p["current_stock"] + qty
            ProductModel.update_stock(prod_id, new_stk)
            QMessageBox.information(self, "Stock-In Recorded", f"Added +{qty:g} to '{p['name']}'. New stock: {new_stk:g}")
            self.refresh_data()
