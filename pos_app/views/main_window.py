from datetime import datetime
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS, apply_theme
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dashboard_view import DashboardView
from pos_app.views.pos_view import POSView
from pos_app.views.products_view import ProductsView
from pos_app.views.inventory_view import InventoryView
from pos_app.views.customers_view import CustomersView
from pos_app.views.sales_view import SalesView
from pos_app.views.reports_view import ReportsView
from pos_app.views.expenses_view import ExpensesView
from pos_app.views.settings_view import SettingsView
from pos_app.views.dialogs.shortcuts_dialog import ShortcutsDialog
from pos_app.views.dialogs.product_form_dialog import ProductFormDialog
from pos_app.utils.i18n import t, set_language, get_language

class MainWindow(ctk.CTkFrame):
    def __init__(self, root, on_logout=None):
        super().__init__(root, fg_color=COLORS["bg_main"])
        self.root = root
        self.on_logout = on_logout
        self.current_screen = None
        self.active_nav = "pos"
        self.nav_buttons = {}
        self.theme_mode = SettingsModel.get("theme_mode", "dark")
        self.currency = SettingsModel.get("currency_symbol", "Rs")

        self._build_shell()
        self._bind_shortcuts()
        self._start_clock()
        self.show_screen("pos")

    def _build_shell(self):
        # 1. Top Bar (height 58)
        self.top_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=0, height=58)
        self.top_bar.pack(fill="x", side="top")
        self.top_bar.pack_propagate(False)

        # Brand / Logo
        brand_box = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        brand_box.pack(side="left", padx=16)

        ctk.CTkLabel(brand_box, text="⚡", font=("Segoe UI", 20)).pack(side="left", padx=(0, 6))
        biz_name = SettingsModel.get("business_name", "SwiftPOS")
        self.lbl_brand = ctk.CTkLabel(brand_box, text=biz_name, font=FONTS["title_md"], text_color=COLORS["primary"])
        self.lbl_brand.pack(side="left")

        # Center Live Clock
        clock_box = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        clock_box.pack(side="left", expand=True)
        self.lbl_clock = ctk.CTkLabel(clock_box, text="", font=FONTS["title_sm"], text_color=COLORS["text_secondary"])
        self.lbl_clock.pack()

        # Right Actions: User info, Shortcuts, Theme toggle, Language, Logout
        right_box = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        right_box.pack(side="right", padx=16)

        user = AuthController.get_current_user()
        u_name = user["full_name"] if user else "Cashier"
        u_role = user["role"] if user else "Cashier"
        role_color = COLORS["primary"] if u_role == "Admin" else COLORS["success"]

        user_tag = ctk.CTkFrame(right_box, fg_color=COLORS["bg_hover"], corner_radius=16, height=32)
        user_tag.pack(side="left", padx=6)
        ctk.CTkLabel(user_tag, text=f"👤 {u_name} ", font=FONTS["body_sm"], text_color=COLORS["text_primary"]).pack(side="left", padx=(10, 2))
        ctk.CTkLabel(user_tag, text=f" {u_role} ", font=FONTS["body_sm"], fg_color=role_color, text_color="#FFFFFF", corner_radius=10).pack(side="left", padx=(0, 6), pady=4)

        # Shortcuts Cheat Sheet Button
        ctk.CTkButton(
            right_box, text="⌨️ Shortcuts", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            width=95, height=32, command=self._show_shortcuts
        ).pack(side="left", padx=4)

        # Theme Toggle (Dark / Light)
        self.btn_theme = ctk.CTkButton(
            right_box, text="☀️ Light" if self.theme_mode == "dark" else "🌙 Dark",
            font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], width=75, height=32,
            command=self._toggle_theme
        )
        self.btn_theme.pack(side="left", padx=4)

        # Logout
        ctk.CTkButton(
            right_box, text="Logout", font=FONTS["body_sm"],
            fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
            hover_color=COLORS["danger"], width=70, height=32,
            command=self._do_logout
        ).pack(side="left", padx=(4, 0))

        # 2. Main Work Area (Left Nav Sidebar + Center Viewport)
        self.work_area = ctk.CTkFrame(self, fg_color="transparent")
        self.work_area.pack(fill="both", expand=True)

        # Left Nav Sidebar (width 190)
        self.sidebar = ctk.CTkFrame(self.work_area, width=190, fg_color=COLORS["bg_sidebar"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar_menu()

        # Center Dynamic Screen Container
        self.viewport = ctk.CTkFrame(self.work_area, fg_color="transparent")
        self.viewport.pack(side="left", fill="both", expand=True)

        # 3. Bottom Status Bar (height 30)
        self.status_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=0, height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.lbl_status_sales = ctk.CTkLabel(
            self.status_bar, text="Today's Sales: Rs 0.00",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        )
        self.lbl_status_sales.pack(side="left", padx=16)

        ctk.CTkLabel(
            self.status_bar, text="🟢 100% Offline • Local SQLite Database (Portable)",
            font=FONTS["body_sm"], text_color=COLORS["success"]
        ).pack(side="right", padx=16)

    def _build_sidebar_menu(self):
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("pos", "🛒", "Point of Sale (F1)"),
            ("products", "🏷️", "Products"),
            ("inventory", "📦", "Inventory"),
            ("customers", "👥", "Customers"),
            ("sales", "🧾", "Sales & Orders"),
            ("reports", "📈", "Reports"),
            ("expenses", "💸", "Expenses"),
            ("settings", "⚙️", "Settings")
        ]

        ctk.CTkFrame(self.sidebar, height=8, fg_color="transparent").pack()

        for key, icon, label in nav_items:
            # Check cashier role restriction
            if not AuthController.can_access(key):
                continue

            btn = ctk.CTkButton(
                self.sidebar, text=f" {icon}  {label}",
                font=FONTS["body_md"], height=42, anchor="w",
                fg_color="transparent", text_color=COLORS["text_primary"],
                hover_color=COLORS["bg_hover"], corner_radius=8,
                command=lambda k=key: self.show_screen(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

    def show_screen(self, screen_name: str):
        if not AuthController.can_access(screen_name):
            return

        self.active_nav = screen_name

        # Update sidebar active highlights
        for k, btn in self.nav_buttons.items():
            if k == screen_name:
                btn.configure(fg_color=COLORS["primary"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_primary"])

        # Destroy existing screen
        if self.current_screen:
            self.current_screen.destroy()

        # Instantiate requested screen
        if screen_name == "dashboard":
            self.current_screen = DashboardView(
                self.viewport, on_navigate=self.show_screen,
                on_add_product=lambda: ProductFormDialog(self, on_saved=self._on_product_added)
            )
        elif screen_name == "pos":
            self.current_screen = POSView(self.viewport)
        elif screen_name == "products":
            self.current_screen = ProductsView(self.viewport)
        elif screen_name == "inventory":
            self.current_screen = InventoryView(self.viewport)
        elif screen_name == "customers":
            self.current_screen = CustomersView(self.viewport)
        elif screen_name == "sales":
            self.current_screen = SalesView(self.viewport)
        elif screen_name == "reports":
            self.current_screen = ReportsView(self.viewport)
        elif screen_name == "expenses":
            self.current_screen = ExpensesView(self.viewport)
        elif screen_name == "settings":
            self.current_screen = SettingsView(self.viewport)

        self.current_screen.pack(fill="both", expand=True)
        self._update_status_ticker()

    def _on_product_added(self):
        if self.active_nav == "products":
            self.show_screen("products")

    def _bind_shortcuts(self):
        # Global function keys
        self.root.bind("<F1>", self._on_f1)
        self.root.bind("<F2>", self._on_f2)
        self.root.bind("<F3>", self._on_f3)
        self.root.bind("<F4>", self._on_f4)
        self.root.bind("<F5>", self._on_f5)

    def _on_f1(self, event=None):
        if self.active_nav != "pos":
            self.show_screen("pos")
        elif isinstance(self.current_screen, POSView):
            self.current_screen._on_clear_cart()

    def _on_f2(self, event=None):
        if self.active_nav != "pos":
            self.show_screen("pos")
        if isinstance(self.current_screen, POSView):
            self.current_screen.focus_search()

    def _on_f3(self, event=None):
        if isinstance(self.current_screen, POSView):
            self.current_screen._on_hold_order()

    def _on_f4(self, event=None):
        if isinstance(self.current_screen, POSView):
            self.current_screen._on_recall_order()

    def _on_f5(self, event=None):
        if isinstance(self.current_screen, POSView):
            self.current_screen._on_checkout()

    def _start_clock(self):
        def _tick():
            now = datetime.now()
            clock_text = now.strftime("%A, %d %B %Y  •  %I:%M:%S %p")
            self.lbl_clock.configure(text=clock_text)
            self.after(1000, _tick)

        _tick()

    def _update_status_ticker(self):
        metrics = OrderModel.get_today_metrics()
        self.lbl_status_sales.configure(
            text=f"Today's Sales: {self.currency} {metrics['total_sales']:,.2f}  ({metrics['total_orders']} orders)"
        )

    def _show_shortcuts(self):
        ShortcutsDialog(self)

    def _toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        apply_theme(self.theme_mode)
        SettingsModel.set("theme_mode", self.theme_mode)
        self.btn_theme.configure(text="☀️ Light" if self.theme_mode == "dark" else "🌙 Dark")
        self.show_screen(self.active_nav)

    def _do_logout(self):
        AuthController.logout()
        if self.on_logout:
            self.on_logout()
