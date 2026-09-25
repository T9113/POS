"""
PySide6 Products Management View for OnesDev POS.
Product catalog table, category management, stock alerts, and add/edit dialogs.
"""
import sqlite3
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
    QDoubleSpinBox, QSpinBox, QMessageBox, QFrame, QPushButton
)
from PySide6.QtGui import QColor

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, SmoothModalOverlay
from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.qt_category_dialog import QtCategoryManagerDialog


class QtProductEditDialog(SmoothModalOverlay):
    """
    Elastic bounce modal for creating and editing products.
    Includes smart inline validation, instant red error highlighting,
    clean 2-column layout, and zero emoji clutter.
    """
    def __init__(self, parent, product=None, on_save=None):
        super().__init__(parent, target_width=540, target_height=600)
        self.product = product or {}
        self.on_save = on_save
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        cur = SettingsModel.get("currency_symbol", "Rs")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 1. Header Title row with clean vector icons
        title_row = QHBoxLayout()
        icon_lbl = QLabel(content)
        from pos_app.utils.icon_helper import get_icon
        icon_lbl.setPixmap(get_icon("products", color=COLORS["primary"], size=22).pixmap(22, 22))
        title_row.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        mode_title = "Edit Product" if self.product.get("id") else "Add New Product"
        lbl_title = QLabel(mode_title, content)
        lbl_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {COLORS['text_primary']};")
        title_vbox.addWidget(lbl_title)

        lbl_sub = QLabel("Fill in the product details and pricing below", content)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        title_vbox.addWidget(lbl_sub)
        title_row.addLayout(title_vbox)

        title_row.addStretch()

        btn_close = QPushButton("", content)
        btn_close.setIcon(get_icon("close", color=COLORS["text_muted"], size=14))
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("background: transparent; border: none; border-radius: 6px;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        # Divider
        div = QFrame(content)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(div)

        # 2. Form Body (Organized into clean, intuitive sections)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        # Field: Product Name (Required)
        lbl_name_tag = QLabel("Product Name *", content)
        lbl_name_tag.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        form_layout.addWidget(lbl_name_tag)

        self.txt_name = QLineEdit(content)
        self.txt_name.setText(self.product.get("name", ""))
        self.txt_name.setPlaceholderText("e.g. Premium White Bread 400g")
        self.txt_name.setFixedHeight(36)
        form_layout.addWidget(self.txt_name)

        self.lbl_name_err = QLabel("", content)
        self.lbl_name_err.setStyleSheet(f"color: {COLORS['text_error']}; font-size: 11px; font-weight: 600; padding-left: 2px;")
        self.lbl_name_err.hide()
        form_layout.addWidget(self.lbl_name_err)

        # 2-Column Row: Category & Barcode
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Category
        col_cat = QVBoxLayout()
        col_cat.setSpacing(4)
        lbl_cat = QLabel("Category *", content)
        lbl_cat.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_cat.addWidget(lbl_cat)

        self.cmb_cat = QComboBox(content)
        cats = CategoryModel.get_all()
        selected_idx = 0
        for i, c in enumerate(cats):
            self.cmb_cat.addItem(c["name"], c["id"])
            if self.product.get("category_id") == c["id"]:
                selected_idx = i
        if cats:
            self.cmb_cat.setCurrentIndex(selected_idx)
        self.cmb_cat.setFixedHeight(36)
        col_cat.addWidget(self.cmb_cat)
        row1.addLayout(col_cat, stretch=1)

        # Barcode / SKU
        col_code = QVBoxLayout()
        col_code.setSpacing(4)
        lbl_barcode = QLabel("Barcode / SKU (Optional)", content)
        lbl_barcode.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_code.addWidget(lbl_barcode)

        self.txt_barcode = QLineEdit(content)
        self.txt_barcode.setText(self.product.get("barcode") or self.product.get("sku", ""))
        self.txt_barcode.setPlaceholderText("e.g. 890123456789")
        self.txt_barcode.setFixedHeight(36)
        col_code.addWidget(self.txt_barcode)
        row1.addLayout(col_code, stretch=1)

        form_layout.addLayout(row1)

        # 2-Column Row: Selling Price & Cost Price
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        col_sell = QVBoxLayout()
        col_sell.setSpacing(4)
        lbl_sell = QLabel(f"Selling Price ({cur}) *", content)
        lbl_sell.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_sell.addWidget(lbl_sell)

        self.spn_sell = QDoubleSpinBox(content)
        self.spn_sell.setMaximum(1000000.0)
        self.spn_sell.setValue(self.product.get("selling_price", 0.0))
        self.spn_sell.setFixedHeight(36)
        col_sell.addWidget(self.spn_sell)
        row2.addLayout(col_sell, stretch=1)

        col_cost = QVBoxLayout()
        col_cost.setSpacing(4)
        lbl_cost = QLabel(f"Cost Price ({cur})", content)
        lbl_cost.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_cost.addWidget(lbl_cost)

        self.spn_cost = QDoubleSpinBox(content)
        self.spn_cost.setMaximum(1000000.0)
        self.spn_cost.setValue(self.product.get("cost_price", 0.0))
        self.spn_cost.setFixedHeight(36)
        col_cost.addWidget(self.spn_cost)
        row2.addLayout(col_cost, stretch=1)

        form_layout.addLayout(row2)

        # Selling price error message label placed under row 2
        self.lbl_sell_err = QLabel("", content)
        self.lbl_sell_err.setStyleSheet(f"color: {COLORS['text_error']}; font-size: 11px; font-weight: 600; padding-left: 2px;")
        self.lbl_sell_err.hide()
        form_layout.addWidget(self.lbl_sell_err)

        # 2-Column Row: Initial Stock & Unit
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        col_stock = QVBoxLayout()
        col_stock.setSpacing(4)
        lbl_stock = QLabel("Current Stock Qty", content)
        lbl_stock.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_stock.addWidget(lbl_stock)

        self.spn_stock = QDoubleSpinBox(content)
        self.spn_stock.setMaximum(1000000.0)
        self.spn_stock.setValue(self.product.get("current_stock", 0.0))
        self.spn_stock.setFixedHeight(36)
        col_stock.addWidget(self.spn_stock)
        row3.addLayout(col_stock, stretch=1)

        col_unit = QVBoxLayout()
        col_unit.setSpacing(4)
        lbl_unit = QLabel("Unit Type", content)
        lbl_unit.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_unit.addWidget(lbl_unit)

        self.cmb_unit = QComboBox(content)
        self.cmb_unit.addItems(["piece", "box", "kg", "pack", "can", "bottle", "liter", "ream"])
        curr_unit = self.product.get("unit", "piece")
        idx = self.cmb_unit.findText(curr_unit)
        if idx >= 0:
            self.cmb_unit.setCurrentIndex(idx)
        self.cmb_unit.setFixedHeight(36)
        col_unit.addWidget(self.cmb_unit)
        row3.addLayout(col_unit, stretch=1)

        form_layout.addLayout(row3)

        # 2-Column Row: Wholesale Price & Low-Stock Alert Level
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        col_ws = QVBoxLayout()
        col_ws.setSpacing(4)
        lbl_ws = QLabel(f"Wholesale Price ({cur})", content)
        lbl_ws.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_ws.addWidget(lbl_ws)
        self.spn_wholesale = QDoubleSpinBox(content)
        self.spn_wholesale.setMaximum(1000000.0)
        self.spn_wholesale.setValue(self.product.get("wholesale_price") or 0.0)
        self.spn_wholesale.setToolTip("Used when the POS is switched to Wholesale mode. Leave 0 to use the selling price.")
        self.spn_wholesale.setFixedHeight(36)
        col_ws.addWidget(self.spn_wholesale)
        row4.addLayout(col_ws, stretch=1)

        col_min = QVBoxLayout()
        col_min.setSpacing(4)
        lbl_min = QLabel("Low-Stock Alert At", content)
        lbl_min.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        col_min.addWidget(lbl_min)
        self.spn_min = QDoubleSpinBox(content)
        self.spn_min.setMaximum(100000.0)
        self.spn_min.setDecimals(0)
        self.spn_min.setValue(self.product.get("min_stock", 5.0) if self.product.get("id") else 5.0)
        self.spn_min.setFixedHeight(36)
        col_min.addWidget(self.spn_min)
        row4.addLayout(col_min, stretch=1)

        form_layout.addLayout(row4)
        layout.addLayout(form_layout)
        layout.addStretch(1)

        # Connect live clearing of validation errors
        self.txt_name.textChanged.connect(lambda: self._clear_field_error(self.txt_name, self.lbl_name_err))
        self.spn_sell.valueChanged.connect(lambda: self._clear_field_error(self.spn_sell, self.lbl_sell_err))
        self.txt_barcode.textChanged.connect(lambda: self.txt_barcode.setStyleSheet(""))

        layout.addSpacing(6)

        # 3. Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = AnimatedButton("Cancel", content, variant="secondary", icon_name="close", icon_size=14)
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.hide_animated)
        btn_box.addWidget(btn_cancel)

        btn_save = AnimatedButton("Save Product", content, variant="primary", icon_name="check", icon_size=15)
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)
        self.set_content_widget(content)

    def _set_field_error(self, widget, error_lbl, message):
        """Highlights the widget in red and displays the inline error message."""
        widget.setStyleSheet(f"""
            border: 1.5px solid {COLORS['border_error']} !important;
            background-color: {COLORS['bg_error']} !important;
        """)
        error_lbl.setText(message)
        error_lbl.show()

    def _clear_field_error(self, widget, error_lbl):
        """Resets the widget border back to default and hides the error label."""
        widget.setStyleSheet("")
        error_lbl.setText("")
        error_lbl.hide()

    def _save(self):
        """Validates all inputs and highlights any missing required fields."""
        has_error = False
        name = self.txt_name.text().strip()
        selling_price = self.spn_sell.value()

        # Validate Product Name
        if not name:
            self._set_field_error(self.txt_name, self.lbl_name_err, "Product name is required.")
            has_error = True

        # Validate Selling Price
        if selling_price <= 0:
            self._set_field_error(self.spn_sell, self.lbl_sell_err, "Selling price must be greater than 0.")
            has_error = True

        if has_error:
            if not name:
                self.txt_name.setFocus()
            else:
                self.spn_sell.setFocus()
            return

        code = self.txt_barcode.text().strip() or None
        if code and ProductModel.is_code_taken(code, exclude_id=self.product.get("id")):
            self.txt_barcode.setStyleSheet(f"border: 1.5px solid {COLORS['border_error']}; background-color: {COLORS['bg_error']};")
            self.txt_barcode.setToolTip("Another product already uses this barcode / SKU.")
            self.txt_barcode.setFocus()
            QMessageBox.warning(self, "Duplicate Barcode", f"Another product already uses the barcode / SKU '{code}'.")
            return

        cost = self.spn_cost.value()
        if cost > selling_price:
            reply = QMessageBox.question(
                self, "Selling Below Cost",
                f"The selling price is lower than the cost price, so every sale loses money.\n\nSave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.spn_sell.setFocus()
                return

        payload = {
            "name": name,
            "sku": code,
            "barcode": code,
            "category_id": self.cmb_cat.currentData(),
            "unit": self.cmb_unit.currentText(),
            "cost_price": cost,
            "selling_price": selling_price,
            "wholesale_price": self.spn_wholesale.value(),
            "current_stock": self.spn_stock.value(),
            "min_stock": self.spn_min.value(),
            "is_active": 1
        }

        try:
            if self.product.get("id"):
                ProductModel.update(self.product["id"], payload)
            else:
                ProductModel.create(payload)
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Could Not Save", f"The product could not be saved: {e}")
            return

        self.hide_animated()
        if self.on_save:
            self.on_save()


class QtProductsView(QWidget):
    """Full Product Catalog management table with instant search and Category Manager."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self.load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Toolbar
        toolbar_card = DropShadowCard(self, corner_radius=10, blur_radius=12, offset_y=2, opacity=15)
        tb_layout = QHBoxLayout(toolbar_card)
        tb_layout.setContentsMargins(14, 10, 14, 10)
        tb_layout.setSpacing(10)

        # Search box
        self.txt_search = QLineEdit(toolbar_card)
        self.txt_search.setPlaceholderText("Search by product name, SKU, or barcode...")
        self.txt_search.setFixedHeight(36)
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1.5px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 12px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {COLORS['primary']};
            }}
        """)
        self.txt_search.textChanged.connect(self.load_products)
        tb_layout.addWidget(self.txt_search, stretch=2)

        # Category Filter
        self.cmb_cat = QComboBox(toolbar_card)
        self.cmb_cat.setFixedHeight(36)
        self.cmb_cat.setStyleSheet(f"""
            QComboBox {{
                background-color: #FFFFFF;
                border: 1.5px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 12px;
                color: {COLORS['text_primary']};
            }}
            QComboBox:focus {{
                border: 1.5px solid {COLORS['primary']};
            }}
        """)
        self.cmb_cat.currentIndexChanged.connect(self.load_products)
        tb_layout.addWidget(self.cmb_cat, stretch=1)

        # Category Manager button
        btn_cats = AnimatedButton(" Categories", toolbar_card, variant="secondary", icon_name="tag", icon_size=15)
        btn_cats.setFixedHeight(36)
        btn_cats.clicked.connect(self._open_category_manager)
        tb_layout.addWidget(btn_cats)

        # Add Product button
        btn_add = AnimatedButton(" Add Product", toolbar_card, variant="primary", icon_name="plus", icon_size=15)
        btn_add.setFixedHeight(36)
        btn_add.setToolTip("Add new product to catalog")
        btn_add.clicked.connect(self._add_product)
        tb_layout.addWidget(btn_add)

        layout.addWidget(toolbar_card)

        # Products Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Barcode / SKU", "Product Name", "Category", "Cost Price",
            "Selling Price", "Wholesale", "Current Stock", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def load_products(self):
        # Refresh categories in combobox if needed
        if self.cmb_cat.count() == 0:
            self.cmb_cat.blockSignals(True)
            self.cmb_cat.addItem("All Categories", None)
            for c in CategoryModel.get_all():
                self.cmb_cat.addItem(c["name"], c["id"])
            self.cmb_cat.blockSignals(False)

        cat_id = self.cmb_cat.currentData()
        q = self.txt_search.text().strip()
        prods = ProductModel.search_products(q, category_id=cat_id, limit=100)

        self.table.setRowCount(len(prods))
        for row, p in enumerate(prods):
            # 0: Code
            code = p.get("barcode") or p.get("sku") or "-"
            it_code = QTableWidgetItem(code)
            it_code.setFlags(it_code.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, it_code)

            # 1: Name
            it_name = QTableWidgetItem(p["name"])
            it_name.setFlags(it_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, it_name)

            # 2: Category
            it_cat = QTableWidgetItem(p.get("category_name") or "-")
            it_cat.setFlags(it_cat.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, it_cat)

            # 3: Cost
            it_cost = QTableWidgetItem(f"{self.currency} {p.get('cost_price', 0.0):,.2f}")
            it_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_cost.setFlags(it_cost.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, it_cost)

            # 4: Sell
            it_sell = QTableWidgetItem(f"{self.currency} {p.get('selling_price', 0.0):,.2f}")
            it_sell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_sell.setForeground(QColor(COLORS["primary"]))
            it_sell.setFlags(it_sell.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, it_sell)

            # 5: Wholesale
            it_ws = QTableWidgetItem(f"{self.currency} {p.get('wholesale_price', 0.0):,.2f}")
            it_ws.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_ws.setFlags(it_ws.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, it_ws)

            # 6: Stock
            stock = p.get("current_stock", 0.0)
            min_s = p.get("min_stock", 5.0)
            it_stk = QTableWidgetItem(f"{stock:g} {p.get('unit', 'pc')}")
            it_stk.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if stock <= min_s:
                it_stk.setForeground(QColor(COLORS["danger"]))
            else:
                it_stk.setForeground(QColor(COLORS["success"]))
            it_stk.setFlags(it_stk.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, it_stk)

            # 7: Action Buttons (Edit / Delete)
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(4, 2, 4, 2)
            act_layout.setSpacing(6)

            btn_edit = AnimatedButton("", variant="secondary", icon_name="edit", icon_color=COLORS["text_secondary"], icon_size=14, is_icon_only=True)
            btn_edit.setFixedSize(30, 28)
            btn_edit.setToolTip("Edit Product")
            btn_edit.clicked.connect(lambda _, prod=p: self._edit_product(prod))
            act_layout.addWidget(btn_edit)

            btn_del = AnimatedButton("", variant="danger_subtle", icon_name="trash", icon_color=COLORS["danger"], icon_size=14, is_icon_only=True)
            btn_del.setFixedSize(30, 28)
            btn_del.setToolTip("Delete Product")
            btn_del.clicked.connect(lambda _, pid=p["id"], pname=p["name"]: self._delete_product(pid, pname))
            act_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 7, act_widget)

    def _add_product(self):
        self.dlg_prod = QtProductEditDialog(self.window(), on_save=self.load_products)
        self.dlg_prod.show_animated()

    def _edit_product(self, prod):
        self.dlg_prod = QtProductEditDialog(self.window(), product=prod, on_save=self.load_products)
        self.dlg_prod.show_animated()

    def _delete_product(self, prod_id, name):
        if QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            ProductModel.soft_delete(prod_id)
            self.load_products()

    def _open_category_manager(self):
        top_window = self.window()
        self.dlg_cat = QtCategoryManagerDialog(top_window, on_change=self._on_categories_changed)
        self.dlg_cat.show_animated()

    def _on_categories_changed(self):
        self.cmb_cat.clear()
        self.load_products()
