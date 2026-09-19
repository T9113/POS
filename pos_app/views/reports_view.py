from datetime import datetime, timedelta
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.report_model import ReportModel
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.exporter import Exporter

class ReportsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.date_from = None
        self.date_to = None
        self._set_date_range("Today")

        self._build_ui()
        self._refresh_report()

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
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Filter Toolbar
        top_bar = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10, height=54)
        top_bar.pack(fill="x", pady=(0, 10))
        top_bar.pack_propagate(False)

        ctk.CTkLabel(top_bar, text="📅 Date Filter:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left", padx=(14, 5))
        
        self.opt_preset = ctk.CTkSegmentedButton(
            top_bar, values=["Today", "Yesterday", "This Week", "This Month", "All Time"],
            command=self._on_preset_changed,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=32
        )
        self.opt_preset.set("Today")
        self.opt_preset.pack(side="left", padx=5)

        # Export Buttons (Excel & PDF)
        ctk.CTkButton(
            top_bar, text="📄 Export PDF", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=34, text_color="#FFFFFF", command=self._export_pdf
        ).pack(side="right", padx=(5, 14))

        ctk.CTkButton(
            top_bar, text="📊 Export Excel", font=FONTS["title_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            height=34, command=self._export_excel
        ).pack(side="right", padx=5)

        # 2. Financial Metrics KPI Banner
        self.kpi_container = ctk.CTkFrame(container, fg_color="transparent")
        self.kpi_container.pack(fill="x", pady=(0, 10))

        # 3. Report Section Tabs
        self.tabs = ctk.CTkTabview(container, fg_color=COLORS["bg_surface"])
        self.tabs.pack(fill="both", expand=True)

        self.tab_products = self.tabs.add("📦 Product-wise Sales")
        self.tab_categories = self.tabs.add("🏷️ Category Sales")
        self.tab_hourly = self.tabs.add("⏰ Peak Hours")
        self.tab_payment = self.tabs.add("💳 Payment Methods")
        self.tab_customers = self.tabs.add("👥 Top Customers")

        # Scrollable frames for each tab
        self.scroll_prod = ctk.CTkScrollableFrame(self.tab_products, fg_color=COLORS["bg_input"], corner_radius=8)
        self.scroll_prod.pack(fill="both", expand=True, padx=10, pady=10)

        self.scroll_cat = ctk.CTkScrollableFrame(self.tab_categories, fg_color=COLORS["bg_input"], corner_radius=8)
        self.scroll_cat.pack(fill="both", expand=True, padx=10, pady=10)

        self.scroll_hour = ctk.CTkScrollableFrame(self.tab_hourly, fg_color=COLORS["bg_input"], corner_radius=8)
        self.scroll_hour.pack(fill="both", expand=True, padx=10, pady=10)

        self.scroll_pay = ctk.CTkScrollableFrame(self.tab_payment, fg_color=COLORS["bg_input"], corner_radius=8)
        self.scroll_pay.pack(fill="both", expand=True, padx=10, pady=10)

        self.scroll_cust = ctk.CTkScrollableFrame(self.tab_customers, fg_color=COLORS["bg_input"], corner_radius=8)
        self.scroll_cust.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_preset_changed(self, value):
        self._set_date_range(value)
        self._refresh_report()

    def _refresh_report(self):
        # 1. Update Financial KPI Banner
        for w in self.kpi_container.winfo_children():
            w.destroy()

        summary = ReportModel.get_sales_summary(self.date_from, self.date_to)

        self._create_kpi_card(
            self.kpi_container, "TOTAL REVENUE",
            f"{self.currency} {summary['total_sales']:,.2f}",
            f"{summary['total_orders']} completed sales", COLORS["primary"]
        )
        self._create_kpi_card(
            self.kpi_container, "GROSS PROFIT",
            f"{self.currency} {summary['gross_profit']:,.2f}",
            "Revenue minus product purchase costs", COLORS["success"]
        )
        self._create_kpi_card(
            self.kpi_container, "EXPENSES",
            f"{self.currency} {summary['total_expenses']:,.2f}",
            "Operating shop expenses", COLORS["warning"]
        )
        net_col = COLORS["success"] if summary["net_profit"] >= 0 else COLORS["danger"]
        self._create_kpi_card(
            self.kpi_container, "NET PROFIT",
            f"{self.currency} {summary['net_profit']:,.2f}",
            "Gross profit minus total expenses", net_col
        )

        # 2. Product-wise sales tab
        for w in self.scroll_prod.winfo_children():
            w.destroy()
        prod_sales = ReportModel.get_product_sales(self.date_from, self.date_to)
        if not prod_sales:
            ctk.CTkLabel(self.scroll_prod, text="No sales recorded in this period.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
        else:
            for p in prod_sales:
                row = ctk.CTkFrame(self.scroll_prod, fg_color=COLORS["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=p["product_name"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=240, anchor="w").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"Units: {p['total_units_sold']:g}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=100).pack(side="left")
                ctk.CTkLabel(row, text=f"Revenue: {self.currency} {p['total_revenue']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=140, anchor="e").pack(side="right", padx=15)
                ctk.CTkLabel(row, text=f"Profit: {self.currency} {p['total_profit']:,.2f}", font=FONTS["body_sm"], text_color=COLORS["success"], width=130, anchor="e").pack(side="right", padx=10)

        # 3. Category sales tab
        for w in self.scroll_cat.winfo_children():
            w.destroy()
        cat_sales = ReportModel.get_category_sales(self.date_from, self.date_to)
        if not cat_sales:
            ctk.CTkLabel(self.scroll_cat, text="No sales recorded in this period.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
        else:
            for c in cat_sales:
                row = ctk.CTkFrame(self.scroll_cat, fg_color=COLORS["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=c["category_name"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=220, anchor="w").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"Units: {c['total_units_sold']:g}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=100).pack(side="left")
                ctk.CTkLabel(row, text=f"Revenue: {self.currency} {c['total_revenue']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=140, anchor="e").pack(side="right", padx=15)

        # 4. Hourly peak hours tab
        for w in self.scroll_hour.winfo_children():
            w.destroy()
        hour_sales = ReportModel.get_hourly_sales(self.date_from, self.date_to)
        if not hour_sales:
            ctk.CTkLabel(self.scroll_hour, text="No sales recorded in this period.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
        else:
            for h in hour_sales:
                row = ctk.CTkFrame(self.scroll_hour, fg_color=COLORS["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                hour_label = f"{h['hour']}:00 - {h['hour']}:59"
                ctk.CTkLabel(row, text=hour_label, font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=180, anchor="w").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"{h['order_count']} transactions", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=130).pack(side="left")
                ctk.CTkLabel(row, text=f"Sales: {self.currency} {h['total_sales']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=140, anchor="e").pack(side="right", padx=15)

        # 5. Payment breakdown tab
        for w in self.scroll_pay.winfo_children():
            w.destroy()
        pay_sales = ReportModel.get_payment_method_breakdown(self.date_from, self.date_to)
        if not pay_sales:
            ctk.CTkLabel(self.scroll_pay, text="No sales recorded in this period.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
        else:
            for p in pay_sales:
                row = ctk.CTkFrame(self.scroll_pay, fg_color=COLORS["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=p["payment_method"].upper(), font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=180, anchor="w").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"{p['transaction_count']} orders", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=120).pack(side="left")
                ctk.CTkLabel(row, text=f"{self.currency} {p['total_amount']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=140, anchor="e").pack(side="right", padx=15)

        # 6. Top customers tab
        for w in self.scroll_cust.winfo_children():
            w.destroy()
        cust_sales = ReportModel.get_top_customers(self.date_from, self.date_to)
        if not cust_sales:
            ctk.CTkLabel(self.scroll_cust, text="No customer sales recorded in this period.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
        else:
            for c in cust_sales:
                row = ctk.CTkFrame(self.scroll_cust, fg_color=COLORS["bg_card"], corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(row, text=c["name"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=220, anchor="w").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=c.get("phone") or "No phone", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=130).pack(side="left")
                ctk.CTkLabel(row, text=f"{c['total_orders']} orders", font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=100).pack(side="left")
                ctk.CTkLabel(row, text=f"{self.currency} {c['total_spent']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=130, anchor="e").pack(side="right", padx=15)

    def _create_kpi_card(self, parent, title, val_str, sub_str, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=10)
        card.pack(side="left", fill="both", expand=True, padx=4)

        ctk.CTkLabel(card, text=title, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(10, 2))
        ctk.CTkLabel(card, text=val_str, font=FONTS["stat_value"], text_color=color).pack(anchor="w", padx=15, pady=(0, 2))
        ctk.CTkLabel(card, text=sub_str, font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(0, 10))

    def _export_excel(self):
        prod_sales = ReportModel.get_product_sales(self.date_from, self.date_to, limit=500)
        headers = ["Product Name", "Units Sold", "Total Revenue", "Gross Profit"]
        rows = [
            [p["product_name"], p["total_units_sold"], f"{self.currency} {p['total_revenue']:,.2f}", f"{self.currency} {p['total_profit']:,.2f}"]
            for p in prod_sales
        ]
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = Exporter.export_excel(filename, "Sales & Profit Report", headers, rows)
        ctk.CTkInputDialog(text=f"Report exported to Excel:\n{path}", title="Export Complete")

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
            ("Total Sales", f"{self.currency} {summary['total_sales']:,.2f}"),
            ("Orders", str(summary["total_orders"])),
            ("Gross Profit", f"{self.currency} {summary['gross_profit']:,.2f}"),
            ("Expenses", f"{self.currency} {summary['total_expenses']:,.2f}"),
            ("Net Profit", f"{self.currency} {summary['net_profit']:,.2f}")
        ]
        path = Exporter.export_pdf(filename, "Sales & Analytics Summary", headers, rows, summary_items)
        ctk.CTkInputDialog(text=f"Report exported to PDF:\n{path}", title="Export Complete")
