import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.sales_controller import SalesController
from pos_app.controllers.auth_controller import AuthController
from pos_app.views.dialogs.receipt_preview_dialog import ReceiptPreviewDialog
from pos_app.views.dialogs.return_dialog import ReturnDialog

class SalesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.page = 1
        self.page_size = 25
        self.total_count = 0
        self.selected_order = None

        self._build_ui()
        self._refresh_orders()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Filter & Search Bar
        top_bar = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10, height=54)
        top_bar.pack(fill="x", pady=(0, 10))
        top_bar.pack_propagate(False)

        ctk.CTkLabel(top_bar, text="🔍", font=("Segoe UI", 13)).pack(side="left", padx=(14, 4))
        self.entry_search = ctk.CTkEntry(
            top_bar, placeholder_text="Search Order #, Customer, Phone...",
            height=36, font=FONTS["body_md"], width=280
        )
        self.entry_search.pack(side="left", padx=(0, 10), pady=9)
        self.entry_search.bind("<KeyRelease>", lambda e: self._on_filter_changed())

        # Payment Method filter
        self.opt_method = ctk.CTkOptionMenu(
            top_bar, values=["All Payment Methods", "Cash", "Credit", "Split"],
            height=36, font=FONTS["body_sm"], command=lambda v: self._on_filter_changed()
        )
        self.opt_method.pack(side="left", padx=5)

        # Split Container: Left = Orders List, Right = Order Details
        split_box = ctk.CTkFrame(container, fg_color="transparent")
        split_box.pack(fill="both", expand=True)

        # Left Orders Table
        self.orders_panel = ctk.CTkFrame(split_box, width=540, fg_color=COLORS["bg_surface"], corner_radius=10)
        self.orders_panel.pack(side="left", fill="both", padx=(0, 10))
        self.orders_panel.pack_propagate(False)

        # Header
        hdr = ctk.CTkFrame(self.orders_panel, fg_color=COLORS["bg_input"], corner_radius=6, height=36)
        hdr.pack(fill="x", padx=10, pady=(10, 4))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Order #", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=130, anchor="w").pack(side="left", padx=(10, 5))
        ctk.CTkLabel(hdr, text="Customer", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=130, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Method", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=80, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Total", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=90, anchor="e").pack(side="right", padx=15)

        self.orders_scroll = ctk.CTkScrollableFrame(self.orders_panel, fg_color="transparent")
        self.orders_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Bottom pagination
        pag_bar = ctk.CTkFrame(self.orders_panel, fg_color="transparent", height=38)
        pag_bar.pack(fill="x", padx=10, pady=6)
        self.lbl_pag = ctk.CTkLabel(pag_bar, text="Page 1", font=FONTS["body_sm"], text_color=COLORS["text_secondary"])
        self.lbl_pag.pack(side="left")

        ctk.CTkButton(pag_bar, text="▶", width=32, height=28, command=self._next_page).pack(side="right", padx=2)
        ctk.CTkButton(pag_bar, text="◀", width=32, height=28, command=self._prev_page).pack(side="right", padx=2)

        # Right Order Detail View
        self.detail_panel = ctk.CTkFrame(split_box, fg_color=COLORS["bg_surface"], corner_radius=10)
        self.detail_panel.pack(side="left", fill="both", expand=True)
        self._render_empty_detail()

    def _render_empty_detail(self):
        for w in self.detail_panel.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.detail_panel, text="👈 Select an order from the list\nto inspect details, reprint receipt, or process return.",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"], justify="center"
        ).pack(expand=True)

    def _on_filter_changed(self):
        self.page = 1
        self._refresh_orders()

    def _prev_page(self):
        if self.page > 1:
            self.page -= 1
            self._refresh_orders()

    def _next_page(self):
        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        if self.page < max_page:
            self.page += 1
            self._refresh_orders()

    def _refresh_orders(self):
        for w in self.orders_scroll.winfo_children():
            w.destroy()

        q = self.entry_search.get().strip()
        method_filter = self.opt_method.get()
        method = None if method_filter == "All Payment Methods" else method_filter.lower()

        self.total_count = SalesController.count_orders(query=q, payment_method=method)
        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.page = min(self.page, max_page)
        self.lbl_pag.configure(text=f"Showing {self.total_count} orders (Page {self.page}/{max_page})")

        offset = (self.page - 1) * self.page_size
        orders = SalesController.list_orders(query=q, payment_method=method, limit=self.page_size, offset=offset)

        if not orders:
            ctk.CTkLabel(self.orders_scroll, text="No orders found.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for o in orders:
            row = ctk.CTkFrame(self.orders_scroll, fg_color=COLORS["bg_card"], corner_radius=6, height=44)
            row.pack(fill="x", pady=2, padx=2)

            num = o["order_number"]
            cust = o.get("customer_name") or "Walk-in"
            m = o.get("payment_method", "cash").capitalize()
            total = float(o.get("total", 0))

            ctk.CTkLabel(row, text=num, font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=130, anchor="w").pack(side="left", padx=(10, 5))
            ctk.CTkLabel(row, text=cust[:16], font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=130, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=m, font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=80, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{self.currency} {total:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=90, anchor="e").pack(side="right", padx=15)

            # Click to select
            row.bind("<Button-1>", lambda e, oid=o["id"]: self._select_order(oid))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, oid=o["id"]: self._select_order(oid))

    def _select_order(self, order_id):
        order = SalesController.get_order(order_id)
        if order:
            self.selected_order = order
            self._render_order_detail(order)

    def _render_order_detail(self, order):
        for w in self.detail_panel.winfo_children():
            w.destroy()

        # Header Info
        hdr = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(15, 10))

        left_info = ctk.CTkFrame(hdr, fg_color="transparent")
        left_info.pack(side="left")

        ctk.CTkLabel(left_info, text=f"Order {order['order_number']}", font=FONTS["title_lg"], text_color=COLORS["text_primary"]).pack(anchor="w")
        cust = order.get("customer_name") or "Walk-in Customer"
        cashier = order.get("cashier_name") or "Admin"
        date_str = order.get("created_at", "")
        ctk.CTkLabel(
            left_info,
            text=f"Date: {date_str}  •  Cashier: {cashier}  •  Customer: {cust}",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Status Badge
        status_str = order.get("status", "completed").upper()
        status_col = COLORS["success"] if status_str == "COMPLETED" else COLORS["danger"]
        ctk.CTkLabel(
            hdr, text=status_str, font=FONTS["title_sm"],
            text_color="#FFFFFF", fg_color=status_col, corner_radius=6, height=28, width=95
        ).pack(side="right")

        # Action Buttons: Reprint Receipt, Return / Refund
        btn_bar = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="🖨️ Reprint Receipt", font=FONTS["body_md"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=lambda: self._reprint(order)
        ).pack(side="left", padx=(0, 8))

        if order.get("status") != "returned":
            ctk.CTkButton(
                btn_bar, text="↩️ Process Return / Refund", font=FONTS["body_md"],
                fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
                command=lambda: self._open_return_dialog(order)
            ).pack(side="left", padx=8)

        # Items Table
        items_scroll = ctk.CTkScrollableFrame(self.detail_panel, fg_color=COLORS["bg_input"], corner_radius=8)
        items_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        is_admin = AuthController.is_admin()

        for item in order.get("items", []):
            i_row = ctk.CTkFrame(items_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            i_row.pack(fill="x", pady=2, padx=2)

            name = item.get("product_name", "Item")
            qty = float(item.get("quantity", 1))
            unit_p = float(item.get("unit_price", 0))
            tot = float(item.get("total", 0))
            cost_p = float(item.get("cost_price", 0) or 0)
            item_profit = tot - (cost_p * qty)

            ctk.CTkLabel(i_row, text=name, font=FONTS["body_md"], text_color=COLORS["text_primary"], width=180, anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(i_row, text=f"Qty: {qty:g}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=65).pack(side="left")
            ctk.CTkLabel(i_row, text=f"{self.currency} {unit_p:,.2f}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=85).pack(side="left")

            if is_admin:
                ctk.CTkLabel(i_row, text=f"Cost: {self.currency} {cost_p * qty:,.2f}", font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=95).pack(side="left")
                ctk.CTkLabel(i_row, text=f"Profit: {self.currency} {item_profit:,.2f}", font=FONTS["body_sm"], text_color=COLORS["success"], width=100).pack(side="left")

            ctk.CTkLabel(i_row, text=f"{self.currency} {tot:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=100, anchor="e").pack(side="right", padx=12)

        # Financial Summary Footer
        sum_box = ctk.CTkFrame(self.detail_panel, fg_color=COLORS["bg_card"], corner_radius=8)
        sum_box.pack(fill="x", padx=20, pady=(0, 15))

        sub = float(order.get("subtotal", 0))
        disc = float(order.get("discount_amount", 0))
        tax = float(order.get("tax_amount", 0))
        total = float(order.get("total", 0))
        paid = float(order.get("amount_paid", 0))
        change = float(order.get("change_due", 0))
        cost_total = float(order.get("cost_total", 0) or 0)
        profit = float(order.get("profit", 0) or 0)
        margin_pct = (profit / total * 100) if total > 0 else 0.0

        f_row1 = ctk.CTkFrame(sum_box, fg_color="transparent")
        f_row1.pack(fill="x", padx=15, pady=(8, 2))
        ctk.CTkLabel(f_row1, text=f"Subtotal: {self.currency} {sub:,.2f}  |  Discount: -{self.currency} {disc:,.2f}  |  Tax: {self.currency} {tax:,.2f}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(side="left")

        f_row2 = ctk.CTkFrame(sum_box, fg_color="transparent")
        f_row2.pack(fill="x", padx=15, pady=(2, 4))
        ctk.CTkLabel(f_row2, text=f"Paid ({order['payment_method'].capitalize()}): {self.currency} {paid:,.2f}  |  Change: {self.currency} {change:,.2f}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(side="left")
        ctk.CTkLabel(f_row2, text=f"TOTAL: {self.currency} {total:,.2f}", font=FONTS["title_md"], text_color=COLORS["primary"]).pack(side="right")

        if is_admin:
            f_row3 = ctk.CTkFrame(sum_box, fg_color="transparent")
            f_row3.pack(fill="x", padx=15, pady=(2, 8))
            ctk.CTkLabel(f_row3, text=f"Cost Total: {self.currency} {cost_total:,.2f}  •  Gross Profit: {self.currency} {profit:,.2f}  ({margin_pct:.1f}% margin)", font=FONTS["title_sm"], text_color=COLORS["success"]).pack(side="left")

    def _reprint(self, order):
        ReceiptPreviewDialog(self, order)

    def _open_return_dialog(self, order):
        ReturnDialog(self, order, on_complete=lambda: self._select_order(order["id"]))
