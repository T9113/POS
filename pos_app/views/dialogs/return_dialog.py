import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.sales_controller import SalesController

class ReturnDialog(ctk.CTkToplevel):
    def __init__(self, parent, order: dict, on_complete=None):
        super().__init__(parent)
        self.order = order
        self.on_complete = on_complete
        self.title(f"Process Return - Order #{order.get('order_number', '')}")
        self.geometry("620x600")
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 620) // 2)
        y = py + max(0, (ph - 600) // 2)
        self.geometry(f"+{x}+{y}")

        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.item_inputs = {} # product_id -> (entry_qty, unit_price)
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        ctk.CTkLabel(
            container, text=f"Order #{self.order.get('order_number')} Return & Refund",
            font=FONTS["title_md"], text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            container, text="Specify return quantities for items to be refunded and restocked into inventory.",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Items list
        items_scroll = ctk.CTkScrollableFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        items_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Table header
        hdr = ctk.CTkFrame(items_scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=5, pady=(2, 8))
        ctk.CTkLabel(hdr, text="Product", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=200, anchor="w").pack(side="left")
        ctk.CTkLabel(hdr, text="Bought", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=70).pack(side="left")
        ctk.CTkLabel(hdr, text="Price", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=90).pack(side="left")
        ctk.CTkLabel(hdr, text="Return Qty", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=90).pack(side="left")

        for item in self.order.get("items", []):
            row = ctk.CTkFrame(items_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=3, padx=2)

            name = item.get("product_name", "Item")
            qty = float(item.get("quantity", 1))
            price = float(item.get("unit_price", 0)) - float(item.get("discount", 0))

            ctk.CTkLabel(row, text=name[:24], font=FONTS["body_md"], text_color=COLORS["text_primary"], width=200, anchor="w").pack(side="left", padx=5, pady=6)
            ctk.CTkLabel(row, text=f"{qty:g}", font=FONTS["body_md"], text_color=COLORS["text_secondary"], width=70).pack(side="left", pady=6)
            ctk.CTkLabel(row, text=f"{self.currency} {price:,.2f}", font=FONTS["body_md"], text_color=COLORS["text_secondary"], width=90).pack(side="left", pady=6)

            ent_qty = ctk.CTkEntry(row, width=80, height=32, placeholder_text="0")
            ent_qty.pack(side="left", padx=5, pady=6)
            ent_qty.insert(0, "0")
            ent_qty.bind("<KeyRelease>", self._recalculate_total)

            self.item_inputs[item["id"]] = {
                "entry": ent_qty,
                "product_id": item.get("product_id"),
                "product_name": name,
                "max_qty": qty,
                "unit_price": price
            }

        # Reason and Refund Total
        bottom_box = ctk.CTkFrame(container, fg_color="transparent")
        bottom_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(bottom_box, text="Return Reason:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        reasons = ["Customer Return", "Defective Item", "Wrong Item Delivered", "Expired", "Other"]
        self.opt_reason = ctk.CTkOptionMenu(bottom_box, values=reasons, height=36)
        self.opt_reason.pack(fill="x", pady=(0, 8))

        # Total Refund Box
        self.lbl_refund_total = ctk.CTkLabel(
            bottom_box, text=f"Total Refund Amount: {self.currency} 0.00",
            font=FONTS["title_md"], text_color=COLORS["danger"]
        )
        self.lbl_refund_total.pack(anchor="w", pady=(2, 10))

        # Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Cancel (Esc)", fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], height=42, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Process Refund", fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"], text_color="#FFFFFF",
            height=42, font=FONTS["title_sm"], command=self._confirm_return
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _recalculate_total(self, event=None):
        total = 0.0
        for item_data in self.item_inputs.values():
            try:
                q = float(item_data["entry"].get().strip() or 0)
                q = min(q, item_data["max_qty"])
                total += q * item_data["unit_price"]
            except ValueError:
                pass
        self.lbl_refund_total.configure(text=f"Total Refund Amount: {self.currency} {total:,.2f}")

    def _confirm_return(self):
        returned_items = []
        total_refund = 0.0

        for item_data in self.item_inputs.values():
            try:
                q = float(item_data["entry"].get().strip() or 0)
                if q > 0:
                    q = min(q, item_data["max_qty"])
                    ref_amount = q * item_data["unit_price"]
                    total_refund += ref_amount
                    returned_items.append({
                        "product_id": item_data["product_id"],
                        "product_name": item_data["product_name"],
                        "quantity": q,
                        "refund_amount": ref_amount
                    })
            except ValueError:
                pass

        if not returned_items or total_refund <= 0:
            return

        reason = self.opt_reason.get()
        ok, msg = SalesController.process_refund(self.order["id"], returned_items, total_refund, reason)
        if ok:
            self.destroy()
            if self.on_complete:
                self.on_complete()
