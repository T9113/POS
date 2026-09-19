from datetime import datetime
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.order_model import OrderModel
from pos_app.models.product_model import ProductModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, on_navigate=None, on_add_product=None):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.on_navigate = on_navigate
        self.on_add_product = on_add_product
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()

    def _build_ui(self):
        # Scrollable container for dashboard
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        # 1. Greeting & Quick Actions Header
        top_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))

        user = AuthController.get_current_user()
        user_name = user["full_name"] if user else "Cashier"
        hour = datetime.now().hour
        greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")

        greeting_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        greeting_frame.pack(side="left")

        ctk.CTkLabel(
            greeting_frame, text=f"{greeting}, {user_name} 👋",
            font=FONTS["title_lg"], text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        today_str = datetime.now().strftime("%A, %d %B %Y")
        ctk.CTkLabel(
            greeting_frame, text=f"Today is {today_str}  •  System Ready & 100% Offline",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Quick action buttons on right
        actions_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_frame.pack(side="right")

        ctk.CTkButton(
            actions_frame, text="⚡ New Sale (F1)", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=42, text_color="#FFFFFF",
            command=lambda: self._navigate("pos")
        ).pack(side="left", padx=5)

        if AuthController.is_admin():
            ctk.CTkButton(
                actions_frame, text="➕ Add Product", font=FONTS["title_sm"],
                fg_color=COLORS["bg_surface"], hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_primary"], height=42,
                command=self._add_product_clicked
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                actions_frame, text="📊 Reports", font=FONTS["title_sm"],
                fg_color=COLORS["bg_surface"], hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_primary"], height=42,
                command=lambda: self._navigate("reports")
            ).pack(side="left", padx=5)

        # 2. KPI Cards Row (Today Sales, Today Orders, Avg Order Value, Today Profit / Low Stock)
        metrics = OrderModel.get_today_metrics()
        low_stock_count = ProductModel.get_low_stock_count()
        tot_sales = float(metrics.get("total_sales", 0))
        tot_orders = int(metrics.get("total_orders", 0))
        avg_order = (tot_sales / tot_orders) if tot_orders > 0 else 0.0

        kpi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 20))

        # KPI 1: Today Sales
        self._create_kpi_card(
            kpi_row, "TODAY'S TOTAL SALES",
            f"{self.currency} {tot_sales:,.2f}",
            "💳 All completed transactions", COLORS["primary"], "💰"
        )

        # KPI 2: Today Orders
        self._create_kpi_card(
            kpi_row, "TODAY'S ORDERS",
            f"{tot_orders:,}",
            "🧾 Orders completed today", COLORS["success"], "🛍️"
        )

        # KPI 3: Average Order Value
        self._create_kpi_card(
            kpi_row, "AVG ORDER VALUE",
            f"{self.currency} {avg_order:,.2f}",
            "📊 Sales per ticket today", COLORS["accent"], "📈"
        )

        # KPI 4: Today Gross Profit or Low Stock
        if AuthController.is_admin():
            self._create_kpi_card(
                kpi_row, "ESTIMATED PROFIT",
                f"{self.currency} {metrics['gross_profit']:,.2f}",
                "💹 Revenue minus cost", COLORS["warning"], "💹"
            )

        stock_color = COLORS["danger"] if low_stock_count > 0 else COLORS["success"]
        self._create_kpi_card(
            kpi_row, "LOW STOCK WARNINGS",
            f"{low_stock_count} Items",
            "⚠️ Needs reorder" if low_stock_count > 0 else "✅ Stock healthy",
            stock_color, "📦"
        )

        # 3. Two Columns: Left = Top 5 Selling Products Today, Right = Low Stock Alerts List
        two_col = ctk.CTkFrame(scroll, fg_color="transparent")
        two_col.pack(fill="both", expand=True, pady=(0, 15))

        # Column Left: Top Products
        col_left = ctk.CTkFrame(two_col, fg_color=COLORS["bg_surface"], corner_radius=12)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        top_hdr = ctk.CTkFrame(col_left, fg_color="transparent")
        top_hdr.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(top_hdr, text="🏆 Top Selling Products Today", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")

        top_products = metrics.get("top_products", [])
        if not top_products:
            ctk.CTkLabel(
                col_left, text="No sales recorded yet today.\nStart ringing orders from the POS Counter!",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"], justify="center"
            ).pack(pady=40)
        else:
            for idx, p in enumerate(top_products, start=1):
                p_row = ctk.CTkFrame(col_left, fg_color=COLORS["bg_card"], corner_radius=8)
                p_row.pack(fill="x", padx=15, pady=4)

                badge = ctk.CTkLabel(
                    p_row, text=f"#{idx}", width=32, height=32,
                    font=FONTS["title_sm"], fg_color=COLORS["primary_subtle"],
                    text_color=COLORS["primary"], corner_radius=6
                )
                badge.pack(side="left", padx=8, pady=8)

                ctk.CTkLabel(
                    p_row, text=p["product_name"], font=FONTS["body_lg"],
                    text_color=COLORS["text_primary"], anchor="w"
                ).pack(side="left", fill="x", expand=True, padx=5)

                ctk.CTkLabel(
                    p_row, text=f"{p['total_qty']:g} sold", font=FONTS["title_sm"],
                    text_color=COLORS["text_secondary"]
                ).pack(side="right", padx=15)

        # Column Right: Low Stock Alert List
        col_right = ctk.CTkFrame(two_col, fg_color=COLORS["bg_surface"], corner_radius=12)
        col_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        low_hdr = ctk.CTkFrame(col_right, fg_color="transparent")
        low_hdr.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(low_hdr, text="⚠️ Low Stock Alert Items", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            low_hdr, text="Manage Inventory", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            width=110, height=30, command=lambda: self._navigate("inventory")
        ).pack(side="right")

        low_prods = ProductModel.get_low_stock_products(limit=5)
        if not low_prods:
            ctk.CTkLabel(
                col_right, text="🎉 All stock levels are sufficient.\nNo items currently below minimum stock.",
                font=FONTS["body_md"], text_color=COLORS["success"], justify="center"
            ).pack(pady=40)
        else:
            for lp in low_prods:
                l_row = ctk.CTkFrame(col_right, fg_color=COLORS["bg_card"], corner_radius=8)
                l_row.pack(fill="x", padx=15, pady=4)

                ctk.CTkLabel(
                    l_row, text=lp["name"], font=FONTS["body_lg"],
                    text_color=COLORS["text_primary"], anchor="w"
                ).pack(side="left", fill="x", expand=True, padx=12, pady=10)

                ctk.CTkLabel(
                    l_row, text=f"Stock: {lp['current_stock']:g} (Min: {lp['min_stock']:g})",
                    font=FONTS["title_sm"], text_color=COLORS["danger"]
                ).pack(side="right", padx=12)

        # 4. Recent 5 Orders Quick List
        recent_box = ctk.CTkFrame(scroll, fg_color=COLORS["bg_surface"], corner_radius=12)
        recent_box.pack(fill="x", pady=(0, 15))

        rec_hdr = ctk.CTkFrame(recent_box, fg_color="transparent")
        rec_hdr.pack(fill="x", padx=15, pady=(12, 8))
        ctk.CTkLabel(rec_hdr, text="🧾 Recent Orders Quick List", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            rec_hdr, text="View All Sales", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            width=110, height=30, command=lambda: self._navigate("sales")
        ).pack(side="right")

        recent_orders = OrderModel.list_orders(limit=5)
        if not recent_orders:
            ctk.CTkLabel(
                recent_box, text="No recent transactions recorded today.",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"]
            ).pack(pady=20)
        else:
            for ro in recent_orders:
                r_row = ctk.CTkFrame(recent_box, fg_color=COLORS["bg_card"], corner_radius=8)
                r_row.pack(fill="x", padx=15, pady=3)

                ctk.CTkLabel(r_row, text=ro["order_number"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=130, anchor="w").pack(side="left", padx=12, pady=8)
                cust_name = ro.get("customer_name") or "Walk-in Customer"
                ctk.CTkLabel(r_row, text=cust_name, font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=150, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(r_row, text=ro.get("created_at", "")[:19], font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=140, anchor="w").pack(side="left", padx=5)
                m_name = (ro.get("payment_method") or "cash").capitalize()
                ctk.CTkLabel(r_row, text=m_name, font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=80).pack(side="left", padx=5)
                ctk.CTkLabel(r_row, text=f"{self.currency} {float(ro.get('total', 0)):,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=110, anchor="e").pack(side="right", padx=12)

    def _create_kpi_card(self, parent, title, value, subtitle, accent_color, icon):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=12)
        card.pack(side="left", fill="both", expand=True, padx=6)

        header_box = ctk.CTkFrame(card, fg_color="transparent")
        header_box.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            header_box, text=title, font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_box, text=icon, font=("Segoe UI", 16)
        ).pack(side="right")

        ctk.CTkLabel(
            card, text=value, font=FONTS["stat_value"],
            text_color=accent_color
        ).pack(anchor="w", padx=16, pady=(0, 2))

        ctk.CTkLabel(
            card, text=subtitle, font=FONTS["body_sm"],
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def _navigate(self, target: str):
        if self.on_navigate:
            self.on_navigate(target)

    def _add_product_clicked(self):
        if self.on_add_product:
            self.on_add_product()
