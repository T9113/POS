"""
PySide6 Category Manager Dialog for OnesDev POS.
iPhone-style animated popup for creating and managing product categories.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.models.category_model import CategoryModel


class QtCategoryManagerDialog(SmoothModalOverlay):
    """Elastic bounce modal for Category Management."""
    categories_updated = Signal()

    def __init__(self, parent, on_change=None):
        super().__init__(parent, target_width=500, target_height=480)
        self.on_change = on_change
        self._build_dialog_ui()
        self._load_categories()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header Title
        title_row = QHBoxLayout()
        lbl_title = QLabel("🏷️ Manage Categories", content)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        title_row.addWidget(lbl_title)

        btn_close = QPushButton("✕", content)
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; color: #94A3B8; font-size: 16px; font-weight: bold; border: none;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        # Add new category row
        add_row = QHBoxLayout()
        self.txt_new_cat = QLineEdit(content)
        self.txt_new_cat.setPlaceholderText("Enter new category name...")
        self.txt_new_cat.setFixedHeight(36)
        self.txt_new_cat.returnPressed.connect(self._add_category)
        add_row.addWidget(self.txt_new_cat)

        btn_add = AnimatedButton("➕ Add", content, variant="primary")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._add_category)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        # Categories Table
        self.table = QTableWidget(content)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Category Name", "Products", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.set_content_widget(content)

    def _load_categories(self):
        cats = CategoryModel.get_all_with_counts()
        self.table.setRowCount(len(cats))
        for row, c in enumerate(cats):
            item_name = QTableWidgetItem(c.get("name", ""))
            item_name.setFlags(item_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_name)

            cnt = c.get("product_count", 0)
            item_cnt = QTableWidgetItem(f"{cnt} items")
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cnt.setFlags(item_cnt.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_cnt)

            btn_del = AnimatedButton("🗑️", variant="danger_subtle")
            btn_del.setFixedSize(36, 28)
            btn_del.clicked.connect(lambda _, cid=c["id"], cname=c["name"], pcount=cnt: self._delete_category(cid, cname, pcount))
            self.table.setCellWidget(row, 2, btn_del)

    def _add_category(self):
        name = self.txt_new_cat.text().strip()
        if not name:
            return
        CategoryModel.get_or_create(name)
        self.txt_new_cat.clear()
        self._load_categories()
        self.categories_updated.emit()
        if self.on_change:
            self.on_change()

    def _delete_category(self, cat_id, cat_name, pcount):
        if pcount > 0:
            QMessageBox.warning(self, "Cannot Delete Category", f"Category '{cat_name}' contains {pcount} products.\nPlease reassign or delete the products first.")
            return
        CategoryModel.delete(cat_id)
        self._load_categories()
        self.categories_updated.emit()
        if self.on_change:
            self.on_change()
