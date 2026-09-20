"""
PySide6 Expenses View for OnesDev POS.
Track operational expenses (rent, utilities, salaries, maintenance),
view category breakdowns, and calculate accurate net profits.
"""
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox
)

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard
from pos_app.models.expense_model import ExpenseModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController


class QtExpensesView(QWidget):
    """Store Operational Expenses Screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self.refresh_expenses()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Total Expenses KPI Banner
        kpi_card = DropShadowCard(self, corner_radius=12)
        kpi_layout = QVBoxLayout(kpi_card)
        kpi_layout.setContentsMargins(20, 16, 20, 16)
        kpi_layout.setSpacing(4)

        lbl_kpi_t = QLabel("TOTAL OPERATING EXPENSES", kpi_card)
        lbl_kpi_t.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 0.5px;")
        kpi_layout.addWidget(lbl_kpi_t)

        self.lbl_kpi_val = QLabel(f"{self.currency} 0.00", kpi_card)
        self.lbl_kpi_val.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {COLORS['warning']};")
        kpi_layout.addWidget(self.lbl_kpi_val)

        main_layout.addWidget(kpi_card)

        # 2. Add Expense Form Card
        add_card = DropShadowCard(self, corner_radius=12)
        add_layout = QVBoxLayout(add_card)
        add_layout.setContentsMargins(18, 14, 18, 14)
        add_layout.setSpacing(10)

        lbl_form_t = QLabel("➕ Record New Store Expense", add_card)
        lbl_form_t.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['text_primary']};")
        add_layout.addWidget(lbl_form_t)

        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        self.cmb_cat = QComboBox(add_card)
        self.cmb_cat.addItems(ExpenseModel.CATEGORIES)
        self.cmb_cat.setFixedHeight(38)
        self.cmb_cat.setFixedWidth(180)
        form_row.addWidget(self.cmb_cat)

        self.txt_amount = QLineEdit(add_card)
        self.txt_amount.setPlaceholderText(f"Amount ({self.currency}) *")
        self.txt_amount.setFixedHeight(38)
        self.txt_amount.setFixedWidth(140)
        form_row.addWidget(self.txt_amount)

        self.txt_desc = QLineEdit(add_card)
        self.txt_desc.setPlaceholderText("Description / notes (e.g. Utility bill payment, packaging boxes)...")
        self.txt_desc.setFixedHeight(38)
        form_row.addWidget(self.txt_desc, stretch=1)

        btn_add = AnimatedButton("Save Expense", add_card, variant="primary")
        btn_add.setFixedHeight(38)
        btn_add.clicked.connect(self._add_expense)
        form_row.addWidget(btn_add)

        add_layout.addLayout(form_row)
        main_layout.addWidget(add_card)

        # 3. Expenses History Table Card
        table_card = DropShadowCard(self, corner_radius=12)
        t_layout = QVBoxLayout(table_card)
        t_layout.setContentsMargins(14, 14, 14, 14)
        t_layout.setSpacing(8)

        lbl_t_title = QLabel("RECORDED EXPENSES LOG", table_card)
        lbl_t_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 0.5px;")
        t_layout.addWidget(lbl_t_title)

        self.table_exp = QTableWidget(table_card)
        self.table_exp.setColumnCount(4)
        self.table_exp.setHorizontalHeaderLabels(["Category", "Description", "Date & Time", "Amount"])
        self.table_exp.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_exp.verticalHeader().setVisible(False)
        self.table_exp.setAlternatingRowColors(True)
        self.table_exp.setStyleSheet(f"""
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
        t_layout.addWidget(self.table_exp)
        main_layout.addWidget(table_card, stretch=1)

    def refresh_expenses(self):
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        tot = ExpenseModel.get_total_expenses()
        self.lbl_kpi_val.setText(f"{self.currency} {tot:,.2f}")

        expenses = ExpenseModel.list_expenses(limit=100)
        self.table_exp.setRowCount(len(expenses))

        for r, e in enumerate(expenses):
            cat_item = QTableWidgetItem(e.get("category", "General"))
            self.table_exp.setItem(r, 0, cat_item)

            self.table_exp.setItem(r, 1, QTableWidgetItem(e.get("description", "")))
            self.table_exp.setItem(r, 2, QTableWidgetItem(e.get("created_at", "")[:16]))

            amt_item = QTableWidgetItem(f"{self.currency} {e.get('amount', 0.0):,.2f}")
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            amt_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table_exp.setItem(r, 3, amt_item)

    def _add_expense(self):
        amt_str = self.txt_amount.text().strip()
        desc = self.txt_desc.text().strip()
        cat = self.cmb_cat.currentText()

        try:
            amt = float(amt_str)
            if amt <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid positive numeric expense amount.")
            return

        user = AuthController.get_current_user()
        user_id = user["id"] if user else None

        ExpenseModel.create(cat, amt, desc, user_id=user_id)
        self.txt_amount.clear()
        self.txt_desc.clear()
        self.refresh_expenses()
        QMessageBox.information(self, "Expense Added", "Operating expense recorded successfully.")
