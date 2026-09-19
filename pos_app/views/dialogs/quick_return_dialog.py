import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.return_dialog import ReturnDialog

class QuickReturnDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_returned=None):
        super().__init__(parent)
        self.on_returned = on_returned
        self.title("Quick Return (Recent Orders)")
        self.geometry("640x520")
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 640) // 2)
        y = py + max(0, (ph - 520) // 2)
        self.geometry(f"+{x}+{y}")

        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=8)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=15, pady=(10, 10))

        ctk.CTkLabel(hdr, text="Quick Return - Recent Orders", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(hdr, text="Close (Esc)", width=80, height=32, font=FONTS["body_sm"], fg_color=COLORS["border"], text_color=COLORS["text_primary"], command=self.destroy).pack(side="right")

        ctk.CTkLabel(
            container, text="Select an order below to immediately return items and issue a refund.",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.scroll_orders = ctk.CTkScrollableFrame(container, fg_color=COLORS["bg_input"], corner_radius=6)
        self.scroll_orders.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._load_recent_orders()

    def _load_recent_orders(self):
        orders = OrderModel.list_orders(limit=12)
        if not orders:
            ctk.CTkLabel(self.scroll_orders, text="No completed orders found.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=40)
            return

        for o in orders:
            row = ctk.CTkFrame(self.scroll_orders, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            cust = o.get("customer_name") or "Walk-in"
            ctk.CTkLabel(info_box, text=f"{o['order_number']}  •  {cust}", font=FONTS["title_sm"], text_color=COLORS["text_primary"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_box, text=f"Time: {o['created_at']}  |  {o['payment_method'].capitalize()}", font=FONTS["body_sm"], text_color=COLORS["text_muted"], anchor="w").pack(anchor="w")

            ctk.CTkLabel(row, text=f"{self.currency} {o['total']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=100, anchor="e").pack(side="left", padx=10)

            ctk.CTkButton(
                row, text="Select Return", width=100, height=32, font=FONTS["body_sm"],
                fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
                hover_color=COLORS["danger"],
                command=lambda oid=o["id"]: self._open_return(oid)
            ).pack(side="right", padx=10)

    def _open_return(self, order_id):
        full_order = OrderModel.get_order_by_id(order_id)
        if full_order:
            self.destroy()
            ReturnDialog(self.master, full_order, on_complete=self.on_returned)
