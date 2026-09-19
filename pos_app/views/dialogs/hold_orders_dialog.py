import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel

class HoldOrdersDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_recall=None):
        super().__init__(parent)
        self.on_recall = on_recall
        self.title("Held Orders (Recall / Parked Orders)")
        self.geometry("620x500")
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 620) // 2)
        y = py + max(0, (ph - 500) // 2)
        self.geometry(f"+{x}+{y}")

        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 10))

        ctk.CTkLabel(header, text="Parked / Held Orders", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(header, text="Close (Esc)", width=80, height=32, font=FONTS["body_sm"], fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"], command=self.destroy).pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._load_held_orders()

    def _load_held_orders(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        held_orders = OrderModel.list_held_orders()

        if not held_orders:
            ctk.CTkLabel(
                self.scroll_frame, text="No orders currently on hold.",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"]
            ).pack(pady=40)
            return

        for held in held_orders:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=5, padx=5)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

            cust = held.get("customer_name") or "Walk-in Customer"
            cart_data = held.get("cart_data", {})
            items = cart_data.get("items", [])
            total_items = len(items)
            total_sum = sum(i.get("total", 0) for i in items)
            time_str = held.get("created_at", "")

            ctk.CTkLabel(
                info_frame, text=f"Order #{held['id']}  •  {cust}",
                font=FONTS["title_sm"], text_color=COLORS["text_primary"], anchor="w"
            ).pack(anchor="w")

            sub_text = f"Items: {total_items}  |  Total: {self.currency} {total_sum:,.2f}  |  Time: {time_str}"
            if held.get("note"):
                sub_text += f"\nNote: {held['note']}"
            ctk.CTkLabel(
                info_frame, text=sub_text,
                font=FONTS["body_sm"], text_color=COLORS["text_secondary"], anchor="w", justify="left"
            ).pack(anchor="w", pady=(2, 0))

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=10)

            ctk.CTkButton(
                btn_frame, text="Recall to Cart", width=110, height=36,
                font=FONTS["body_md"], fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                command=lambda hid=held["id"]: self._recall(hid)
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                btn_frame, text="Delete", width=70, height=36,
                font=FONTS["body_md"], fg_color=COLORS["danger_subtle"],
                text_color=COLORS["danger"], hover_color=COLORS["danger"],
                command=lambda hid=held["id"]: self._delete(hid)
            ).pack(side="left")

    def _recall(self, held_id: int):
        self.destroy()
        if self.on_recall:
            self.on_recall(held_id)

    def _delete(self, held_id: int):
        OrderModel.delete_held_order(held_id)
        self._load_held_orders()
