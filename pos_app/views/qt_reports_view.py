"""
PySide6 Reports & Analytics View for OnesDev POS.
Hardware-accelerated analytics dashboard with date filters, KPI cards,
breakdown tables, and PDF/Excel export capabilities.
"""
from datetime import datetime, timedelta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QMessageBox, QFrame,
    QButtonGroup, QPushButton
)

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, clear_layout
from pos_app.models.report_model import ReportModel
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.exporter import Exporter
from pos_app.utils.icon_helper import get_icon


class QtReportsView(QWidget):
    """Reports, Analytics, and Financial Overview Screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.date_from = None
        self.date_to = None
        self._set_date_range("Today")

        self._build_ui()
        self.refresh_data()

    def _set_date_range(self, preset: str):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        if preset == "Today":
            self.date_from = today_str
            self.date_to = today_str
        elif preset == "Yesterday":
            yest = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            self.date_from = yest
            self.date_to = yest
        elif preset == "This Week":
            start_week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
            self.date_from = start_week
            self.date_to = today_str
        elif preset == "This Month":
            start_month = now.strftime("%Y-%m-01")
            self.date_from = start_month
            self.date_to = today_str
        elif preset == "All Time":
            self.date_from = None
            self.date_to = None

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Top Control Bar: Date Presets & Export Actions
        top_card = DropShadowCard(self, corner_radius=12)
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(12)

        lbl_filter = QLabel("Date Filter:", top_card)
        lbl_filter.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text_primary']};")
        top_layout.addWidget(lbl_filter)

        # Date preset pills
        self.btn_group = QButtonGroup(self)
        self.preset_buttons = {}
        presets = ["Today", "Yesterday", "This Week", "This Month", "All Time"]

        for p in presets:
            btn = QPushButton(p, top_card)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if p == "Today":
                btn.setChecked(True)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: #FFFFFF;
                        font-weight: 600;
                        font-size: 12px;
                        border-radius: 8px;
                        padding: 0 14px;
                        border: none;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['bg_input']};
                        color: {COLORS['text_secondary']};
                        font-weight: 500;
                        font-size: 12px;
                        border-radius: 8px;
                        padding: 0 14px;
                        border: 1px solid {COLORS['border']};
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['bg_hover']};
                        color: {COLORS['text_primary']};
                    }}
                """)
            btn.clicked.connect(lambda checked, name=p: self._on_preset_clicked(name))
            self.btn_group.addButton(btn)
            self.preset_buttons[p] = btn
            top_layout.addWidget(btn)

        top_layout.addStretch()

        btn_excel = AnimatedButton("Export Excel", top_card, variant="secondary", icon_name="excel")
        btn_excel.setFixedHeight(36)
        btn_excel.clicked.connect(self._export_excel)
        top_layout.addWidget(btn_excel)

        btn_pdf = AnimatedButton("Export PDF", top_card, variant="primary", icon_name="pdf")
        btn_pdf.setFixedHeight(36)
        btn_pdf.clicked.connect(self._export_pdf)
        top_layout.addWidget(btn_pdf)

        main_layout.addWidget(top_card)

        # 2. Financial Metrics KPI Banner
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(14)
        main_layout.addLayout(self.kpi_layout)

        # 3. Report Breakdown Tabs
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_surface']};
                border-radius: 12px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {COLORS['bg_main']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 13px;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['bg_surface']};
                color: {COLORS['primary']};
                border-top: 3px solid {COLORS['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLORS['bg_hover']};
            }}
        """)

        # Products Tab
        self.tab_prod = QWidget()
        l_prod = QVBoxLayout(self.tab_prod)
        l_prod.setContentsMargins(16, 16, 16, 16)
        self.table_prod = self._create_table(["Product Name", "Units Sold", "Total Revenue", "Gross Profit"])
        l_prod.addWidget(self.table_prod)
        self.tabs.addTab(self.tab_prod, get_icon("products", COLORS["text_secondary"], 16), "Product Sales")

        # Category Tab
        self.tab_cat = QWidget()
        l_cat = QVBoxLayout(self.tab_cat)
        l_cat.setContentsMargins(16, 16, 16, 16)
        self.table_cat = self._create_table(["Category Name", "Units Sold", "Total Revenue"])
        l_cat.addWidget(self.table_cat)
        self.tabs.addTab(self.tab_cat, get_icon("tag", COLORS["text_secondary"], 16), "Category Sales")

        # Peak Hours Tab
        self.tab_hour = QWidget()
        l_hour = QVBoxLayout(self.tab_hour)
        l_hour.setContentsMargins(16, 16, 16, 16)
        self.table_hour = self._create_table(["Time Window", "Transactions", "Total Sales"])
        l_hour.addWidget(self.table_hour)
        self.tabs.addTab(self.tab_hour, get_icon("dashboard", COLORS["text_secondary"], 16), "Peak Hours")

        # Payment Methods Tab
        self.tab_pay = QWidget()
        l_pay = QVBoxLayout(self.tab_pay)
        l_pay.setContentsMargins(16, 16, 16, 16)
        self.table_pay = self._create_table(["Payment Method", "Order Count", "Total Revenue"])
        l_pay.addWidget(self.table_pay)
        self.tabs.addTab(self.tab_pay, get_icon("credit_card", COLORS["text_secondary"], 16), "Payment Methods")

        # Top Customers Tab
        self.tab_cust = QWidget()
        l_cust = QVBoxLayout(self.tab_cust)
        l_cust.setContentsMargins(16, 16, 16, 16)
        self.table_cust = self._create_table(["Customer Name", "Phone", "Total Orders", "Total Spent"])
        l_cust.addWidget(self.table_cust)
        self.tabs.addTab(self.tab_cust, get_icon("customers", COLORS["text_secondary"], 16), "Top Customers")

        main_layout.addWidget(self.tabs, stretch=1)

    def _create_table(self, headers: list) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(headers)):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border_subtle']};
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
                color: {COLORS['text_primary']};
            }}
        """)
        return table

    def _on_preset_clicked(self, preset_name: str):
        for name, btn in self.preset_buttons.items():
            if name == preset_name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: #FFFFFF;
                        font-weight: 600;
                        font-size: 12px;
                        border-radius: 8px;
                        padding: 0 14px;
                        border: none;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['bg_input']};
                        color: {COLORS['text_secondary']};
                        font-weight: 500;
                        font-size: 12px;
                        border-radius: 8px;
                        padding: 0 14px;
                        border: 1px solid {COLORS['border']};
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['bg_hover']};
                        color: {COLORS['text_primary']};
                    }}
                """)
        self._set_date_range(preset_name)
        self.refresh_data()

    def refresh_data(self):
        self.currency = SettingsModel.get("currency_symbol", "Rs")

        # 1. Update Financial KPI Banner
        clear_layout(self.kpi_layout)

        summary = ReportModel.get_sales_summary(self.date_from, self.date_to)

        rev_sub = f"{summary['total_orders']} sales"
        if summary.get("total_refunds"):
            rev_sub += f"  •  {self.currency} {summary['total_refunds']:,.2f} refunded"
        self._create_kpi_card("NET REVENUE", f"{self.currency} {summary['total_sales']:,.2f}", rev_sub, COLORS["primary"])
        self._create_kpi_card("GROSS PROFIT", f"{self.currency} {summary['gross_profit']:,.2f}", "Revenue minus product costs", COLORS["success"])
        self._create_kpi_card("EXPENSES", f"{self.currency} {summary['total_expenses']:,.2f}", "Shop operating expenses", COLORS["warning"])
        net_col = COLORS["success"] if summary["net_profit"] >= 0 else COLORS["danger"]
        self._create_kpi_card("NET PROFIT", f"{self.currency} {summary['net_profit']:,.2f}", "Gross profit minus expenses", net_col)

        # 2. Product-wise sales
        prod_sales = ReportModel.get_product_sales(self.date_from, self.date_to)
        self.table_prod.setRowCount(len(prod_sales))
        for r, p in enumerate(prod_sales):
            self.table_prod.setItem(r, 0, QTableWidgetItem(p["product_name"]))
            item_u = QTableWidgetItem(f"{p['total_units_sold']:g}")
            item_u.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_prod.setItem(r, 1, item_u)

            item_rev = QTableWidgetItem(f"{self.currency} {p['total_revenue']:,.2f}")
            item_rev.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_prod.setItem(r, 2, item_rev)

            item_prof = QTableWidgetItem(f"{self.currency} {p['total_profit']:,.2f}")
            item_prof.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_prod.setItem(r, 3, item_prof)

        # 3. Category sales
        cat_sales = ReportModel.get_category_sales(self.date_from, self.date_to)
        self.table_cat.setRowCount(len(cat_sales))
        for r, c in enumerate(cat_sales):
            self.table_cat.setItem(r, 0, QTableWidgetItem(c["category_name"]))
            item_u = QTableWidgetItem(f"{c['total_units_sold']:g}")
            item_u.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_cat.setItem(r, 1, item_u)

            item_rev = QTableWidgetItem(f"{self.currency} {c['total_revenue']:,.2f}")
            item_rev.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_cat.setItem(r, 2, item_rev)

        # 4. Hourly peak hours
        hour_sales = ReportModel.get_hourly_sales(self.date_from, self.date_to)
        self.table_hour.setRowCount(len(hour_sales))
        for r, h in enumerate(hour_sales):
            h_val = int(h['hour']) if str(h['hour']).isdigit() else 0
            self.table_hour.setItem(r, 0, QTableWidgetItem(f"{h_val:02d}:00 - {h_val:02d}:59"))
            item_tx = QTableWidgetItem(f"{h['order_count']} orders")
            item_tx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_hour.setItem(r, 1, item_tx)

            item_sales = QTableWidgetItem(f"{self.currency} {h['total_sales']:,.2f}")
            item_sales.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_hour.setItem(r, 2, item_sales)

        # 5. Payment breakdown
        pay_sales = ReportModel.get_payment_method_breakdown(self.date_from, self.date_to)
        self.table_pay.setRowCount(len(pay_sales))
        for r, p in enumerate(pay_sales):
            self.table_pay.setItem(r, 0, QTableWidgetItem(p["payment_method"].upper()))
            item_c = QTableWidgetItem(f"{p['transaction_count']} orders")
            item_c.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_pay.setItem(r, 1, item_c)

            item_amt = QTableWidgetItem(f"{self.currency} {p['total_amount']:,.2f}")
            item_amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_pay.setItem(r, 2, item_amt)

        # 6. Top Customers
        cust_sales = ReportModel.get_top_customers(self.date_from, self.date_to)
        self.table_cust.setRowCount(len(cust_sales))
        for r, c in enumerate(cust_sales):
            self.table_cust.setItem(r, 0, QTableWidgetItem(c["name"]))
            self.table_cust.setItem(r, 1, QTableWidgetItem(c.get("phone") or "-"))
            item_ord = QTableWidgetItem(f"{c['total_orders']} orders")
            item_ord.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_cust.setItem(r, 2, item_ord)

            item_spent = QTableWidgetItem(f"{self.currency} {c['total_spent']:,.2f}")
            item_spent.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_cust.setItem(r, 3, item_spent)

    def _create_kpi_card(self, title: str, val_str: str, sub_str: str, color: str):
        card = DropShadowCard(self, corner_radius=10)
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(16, 14, 16, 14)
        card_l.setSpacing(4)

        lbl_t = QLabel(title, card)
        lbl_t.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 0.5px;")
        card_l.addWidget(lbl_t)

        lbl_val = QLabel(val_str, card)
        lbl_val.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color};")
        card_l.addWidget(lbl_val)

        lbl_sub = QLabel(sub_str, card)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {COLORS['text_secondary']};")
        card_l.addWidget(lbl_sub)

        self.kpi_layout.addWidget(card)

    def _export_excel(self):
        prod_sales = ReportModel.get_product_sales(self.date_from, self.date_to, limit=500)
        headers = ["Product Name", "Units Sold", "Total Revenue", "Gross Profit"]
        rows = [
            [p["product_name"], p["total_units_sold"], f"{self.currency} {p['total_revenue']:,.2f}", f"{self.currency} {p['total_profit']:,.2f}"]
            for p in prod_sales
        ]
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            path = Exporter.export_excel(filename, "Sales & Profit Report", headers, rows)
            QMessageBox.information(self, "Export Complete", f"Excel report generated successfully:\n\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export Excel file:\n{str(e)}")

    def _export_pdf(self):
        summary = ReportModel.get_sales_summary(self.date_from, self.date_to)
        prod_sales = ReportModel.get_product_sales(self.date_from, self.date_to, limit=100)
        headers = ["Product Name", "Units Sold", "Revenue", "Gross Profit"]
        rows = [
            [p["product_name"], str(p["total_units_sold"]), f"{self.currency} {p['total_revenue']:,.2f}", f"{self.currency} {p['total_profit']:,.2f}"]
            for p in prod_sales
        ]
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        summary_items = [
            ("Gross Sales", f"{self.currency} {summary['gross_sales']:,.2f}"),
            ("Refunds", f"{self.currency} {summary['total_refunds']:,.2f}"),
            ("Net Sales", f"{self.currency} {summary['total_sales']:,.2f}"),
            ("Orders", str(summary["total_orders"])),
            ("Gross Profit", f"{self.currency} {summary['gross_profit']:,.2f}"),
            ("Expenses", f"{self.currency} {summary['total_expenses']:,.2f}"),
            ("Net Profit", f"{self.currency} {summary['net_profit']:,.2f}")
        ]
        try:
            path = Exporter.export_pdf(filename, "Sales & Analytics Summary", headers, rows, summary_items)
            QMessageBox.information(self, "Export Complete", f"PDF report generated successfully:\n\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export PDF file:\n{str(e)}")
