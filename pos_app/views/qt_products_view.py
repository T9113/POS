"""
PySide6 Products Management View for OnesDev POS.
Product catalog table, category management, stock alerts, and add/edit dialogs.
"""
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
    """Elastic bounce modal for creating and editing products with rounded corners."""
    def __init__(self, parent, product=None, on_save=None):
        super().__init__(parent, target_width=520, target_height=600)
        self.product = product or {}
        self.on_save = on_save
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header Title row with Close button
        title_row = QHBoxLayout()
        title_text = "✏️ Edit Product" if self.product else "📦 Add New Product"
        lbl_title = QLabel(title_text, content)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        title_row.addWidget(lbl_title)

        btn_close = QPushButton("✕", content)
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; color: #94A3B8; font-size: 16px; font-weight: bold; border: none;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_name = QLineEdit(content)
        self.txt_name.setText(self.product.get("name", ""))
        self.txt_name.setPlaceholderText("Product Name *")
        form.addRow("Product Name *:", self.txt_name)

        self.txt_sku = QLineEdit(content)
        self.txt_sku.setText(self.product.get("sku", ""))
        self.txt_sku.setPlaceholderText("SKU (e.g. BEV-001)")
        form.addRow("SKU Code:", self.txt_sku)

        self.txt_barcode = QLineEdit(content)
        self.txt_barcode.setText(self.product.get("barcode", ""))
        self.txt_barcode.setPlaceholderText("Barcode (e.g. 890100100001)")
        form.addRow("Barcode:", self.txt_barcode)

        self.cmb_cat = QComboBox(content)
        cats = CategoryModel.get_all()
        selected_idx = 0
        for i, c in enumerate(cats):
            self.cmb_cat.addItem(c["name"], c["id"])
            if self.product.get("category_id") == c["id"]:
                selected_idx = i
        if cats:
            self.cmb_cat.setCurrentIndex(selected_idx)
        form.addRow("Category:", self.cmb_cat)

        self.txt_unit = QLineEdit(content)
        self.txt_unit.setText(self.product.get("unit", "piece"))
        form.addRow("Unit (pc/kg/box):", self.txt_unit)

        self.spn_cost = QDoubleSpinBox(content)
        self.spn_cost.setMaximum(1000000.0)
        self.spn_cost.setValue(self.product.get("cost_price", 0.0))
        form.addRow("Cost Price:", self.spn_cost)

        self.spn_sell = QDoubleSpinBox(content)
        self.spn_sell.setMaximum(1000000.0)
        self.spn_sell.setValue(self.product.get("selling_price", 0.0))
        form.addRow("Selling Price *:", self.spn_sell)

        self.spn_wholesale = QDoubleSpinBox(content)
        self.spn_wholesale.setMaximum(1000000.0)
        self.spn_wholesale.setValue(self.product.get("wholesale_price", 0.0))
        form.addRow("Wholesale Price:", self.spn_wholesale)

        self.spn_stock = QDoubleSpinBox(content)
        self.spn_stock.setMaximum(1000000.0)
        self.spn_stock.setValue(self.product.get("current_stock", 0.0))
        form.addRow("Current Stock:", self.spn_stock)

        self.spn_min = QDoubleSpinBox(content)
        self.spn_min.setMaximum(1000000.0)
        self.spn_min.setValue(self.product.get("min_stock", 5.0))
        form.addRow("Min Reorder Stock:", self.spn_min)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = AnimatedButton("Cancel", content, variant="secondary")
        btn_cancel.clicked.connect(self.hide_animated)
        btn_box.addWidget(btn_cancel)

        btn_save = AnimatedButton("Save Product", content, variant="primary")
        btn_save.clicked.connect(self._save)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)
        self.set_content_widget(content)

    def _save(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Product Name is required!")
            return

        payload = {
            "name": name,
            "sku": self.txt_sku.text().strip() or None,
            "barcode": self.txt_barcode.text().strip() or None,
            "category_id": self.cmb_cat.currentData(),
            "unit": self.txt_unit.text().strip() or "piece",
            "cost_price": self.spn_cost.value(),
            "selling_price": self.spn_sell.value(),
            "wholesale_price": self.spn_wholesale.value(),
            "current_stock": self.spn_stock.value(),
            "min_stock": self.spn_min.value(),
            "is_active": 1
        }

        if self.product.get("id"):
            ProductModel.update(self.product["id"], payload)
        else:
            ProductModel.create(payload)

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
        self.txt_search.textChanged.connect(self.load_products)
        tb_layout.addWidget(self.txt_search, stretch=2)

        # Category Filter
        self.cmb_cat = QComboBox(toolbar_card)
        self.cmb_cat.setFixedHeight(36)
        self.cmb_cat.currentIndexChanged.connect(self.load_products)
        tb_layout.addWidget(self.cmb_cat, stretch=1)

        # Category Manager button
        btn_cats = AnimatedButton("🏷️ Categories", toolbar_card, variant="secondary")
        btn_cats.setFixedHeight(36)
        btn_cats.clicked.connect(self._open_category_manager)
        tb_layout.addWidget(btn_cats)

        # Add Product button
        btn_add = AnimatedButton("+ Add Product", toolbar_card, variant="primary")
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

            btn_edit = AnimatedButton("✏️", variant="secondary", is_icon_only=True)
            btn_edit.setFixedSize(30, 28)
            btn_edit.setToolTip("Edit Product")
            btn_edit.clicked.connect(lambda _, prod=p: self._edit_product(prod))
            act_layout.addWidget(btn_edit)

            btn_del = AnimatedButton("🗑️", variant="danger_subtle", is_icon_only=True)
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
            ProductModel.delete(prod_id)
            self.load_products()

    def _open_category_manager(self):
        top_window = self.window()
        self.dlg_cat = QtCategoryManagerDialog(top_window, on_change=self._on_categories_changed)
        self.dlg_cat.show_animated()

    def _on_categories_changed(self):
        self.cmb_cat.clear()
        self.load_products()
