import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.settings_model import SettingsModel

class PaymentDialog(ctk.CTkToplevel):
    def __init__(self, parent, total_amount: float, customer: dict = None, on_complete=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.customer = customer
        self.on_complete = on_complete
        self.result = None

        currency = SettingsModel.get("currency_symbol", "Rs")
        self.currency = currency

        self.title("Payment & Checkout")
        self.geometry("520x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 520) // 2)
        y = py + max(0, (ph - 620) // 2)
        self.geometry(f"+{x}+{y}")

        self.payment_method = "cash"
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Total Box
        header_card = ctk.CTkFrame(container, fg_color=COLORS["primary"], corner_radius=10, height=85)
        header_card.pack(fill="x", padx=15, pady=(15, 10))
        header_card.pack_propagate(False)

        ctk.CTkLabel(
            header_card, text="TOTAL AMOUNT DUE", font=FONTS["title_sm"],
            text_color="#E0E7FF"
        ).pack(pady=(10, 0))

        self.lbl_total = ctk.CTkLabel(
            header_card, text=f"{self.currency} {self.total_amount:,.2f}",
            font=FONTS["title_xl"], text_color="#FFFFFF"
        )
        self.lbl_total.pack()

        # Customer display
        cust_name = self.customer["name"] if self.customer else "Walk-in Customer"
        cust_info = f"Customer: {cust_name}"
        if self.customer and self.customer.get("balance", 0) > 0:
            cust_info += f"  (Existing Due: {self.currency} {self.customer['balance']:,.2f})"
        
        ctk.CTkLabel(
            container, text=cust_info, font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(2, 10))

        # Payment Mode Tabs (Segmented Button)
        ctk.CTkLabel(container, text="Select Payment Method:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(5, 4))
        self.method_seg = ctk.CTkSegmentedButton(
            container,
            values=["Cash", "Split", "Credit / Due"],
            command=self._on_method_change,
            height=38,
            font=FONTS["body_lg"]
        )
        self.method_seg.set("Cash")
        self.method_seg.pack(fill="x", padx=20, pady=(0, 15))

        # Dynamic Content Frame for Payment Method
        self.dyn_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.dyn_frame.pack(fill="both", expand=True, padx=20)

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(container, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=(10, 15))

        self.btn_cancel = ctk.CTkButton(
            bottom_bar, text="Cancel (Esc)", fg_color=COLORS["bg_hover"],
            hover_color=COLORS["border"], text_color=COLORS["text_primary"],
            height=46, font=FONTS["body_lg"], command=self.destroy
        )
        self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_confirm = ctk.CTkButton(
            bottom_bar, text=f"COMPLETE SALE ({self.currency} {self.total_amount:,.2f})",
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            text_color="#FFFFFF", height=46, font=FONTS["title_sm"],
            command=self._on_confirm
        )
        self.btn_confirm.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Render initial cash form
        self._render_cash_form()

    def _on_method_change(self, value):
        mode = value.lower()
        if "cash" in mode:
            self.payment_method = "cash"
            self._render_cash_form()
        elif "card" in mode:
            self.payment_method = "card"
            self._render_card_form()
        elif "split" in mode:
            self.payment_method = "split"
            self._render_split_form()
        elif "credit" in mode:
            self.payment_method = "credit"
            self._render_credit_form()

    def _clear_dyn_frame(self):
        for widget in self.dyn_frame.winfo_children():
            widget.destroy()

    def _render_cash_form(self):
        self._clear_dyn_frame()
        
        ctk.CTkLabel(self.dyn_frame, text="Amount Received:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 4))
        
        self.entry_received = ctk.CTkEntry(
            self.dyn_frame, height=44, font=FONTS["title_md"],
            placeholder_text=f"e.g. {self.total_amount:,.2f}"
        )
        self.entry_received.pack(fill="x", pady=(0, 10))
        self.entry_received.insert(0, f"{self.total_amount:g}")
        self.entry_received.bind("<KeyRelease>", self._update_cash_change)
        self.entry_received.focus_set()

        # Quick Preset Buttons (+500, +1000, Exact, etc.)
        preset_frame = ctk.CTkFrame(self.dyn_frame, fg_color="transparent")
        preset_frame.pack(fill="x", pady=(0, 12))

        presets = [
            ("Exact", self.total_amount),
            ("+100", self.total_amount + 100),
            ("+500", self.total_amount + 500),
            ("+1000", self.total_amount + 1000),
            ("+5000", self.total_amount + 5000),
        ]
        for label, val in presets:
            btn = ctk.CTkButton(
                preset_frame, text=label, width=64, height=32,
                font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
                text_color=COLORS["text_primary"],
                command=lambda v=val: self._set_preset_amount(v)
            )
            btn.pack(side="left", padx=3)

        # Change Due Display Box
        self.change_box = ctk.CTkFrame(self.dyn_frame, fg_color=COLORS["bg_card"], corner_radius=8, height=60)
        self.change_box.pack(fill="x", pady=(5, 10))
        self.change_box.pack_propagate(False)

        ctk.CTkLabel(self.change_box, text="Change Due:", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(side="left", padx=15)
        self.lbl_change = ctk.CTkLabel(self.change_box, text=f"{self.currency} 0.00", font=FONTS["title_md"], text_color=COLORS["success"])
        self.lbl_change.pack(side="right", padx=15)

        # Order Note Input
        ctk.CTkLabel(self.dyn_frame, text="Order Note (Optional):", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 2))
        self.entry_note = ctk.CTkEntry(self.dyn_frame, height=36, placeholder_text="e.g. Delivered, Customer discount applied...")
        self.entry_note.pack(fill="x")

        self._update_cash_change()

    def _set_preset_amount(self, val: float):
        self.entry_received.delete(0, "end")
        self.entry_received.insert(0, f"{val:g}")
        self._update_cash_change()

    def _update_cash_change(self, event=None):
        try:
            val_str = self.entry_received.get().strip()
            received = float(val_str) if val_str else 0.0
            change = max(0.0, received - self.total_amount)
            self.lbl_change.configure(text=f"{self.currency} {change:,.2f}")
            if received < self.total_amount:
                self.lbl_change.configure(text=f"Underpaid ({self.currency} {self.total_amount - received:,.2f})", text_color=COLORS["warning"])
            else:
                self.lbl_change.configure(text=f"{self.currency} {change:,.2f}", text_color=COLORS["success"])
        except ValueError:
            self.lbl_change.configure(text="Invalid amount", text_color=COLORS["danger"])

    def _render_card_form(self):
        self._clear_dyn_frame()
        card_box = ctk.CTkFrame(self.dyn_frame, fg_color=COLORS["bg_card"], corner_radius=8)
        card_box.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            card_box, text="Card / Digital POS Terminal",
            font=FONTS["title_md"], text_color=COLORS["text_primary"]
        ).pack(pady=(20, 5))
        ctk.CTkLabel(
            card_box, text=f"Charge {self.currency} {self.total_amount:,.2f} on external POS card machine.\nClick Complete Sale to finalize.",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"], justify="center"
        ).pack(pady=10)

        ctk.CTkLabel(self.dyn_frame, text="Reference / Card Note (Optional):", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(10, 2))
        self.entry_note = ctk.CTkEntry(self.dyn_frame, height=36, placeholder_text="e.g. Card Auth code, Visa ending 4421...")
        self.entry_note.pack(fill="x")

    def _render_split_form(self):
        self._clear_dyn_frame()
        ctk.CTkLabel(self.dyn_frame, text="Split Payment Breakdown", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 10))

        half = round(self.total_amount / 2, 2)

        ctk.CTkLabel(self.dyn_frame, text="Cash Amount:", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.entry_split_cash = ctk.CTkEntry(self.dyn_frame, height=38, font=FONTS["body_lg"])
        self.entry_split_cash.pack(fill="x", pady=(2, 10))
        self.entry_split_cash.insert(0, f"{half:g}")

        ctk.CTkLabel(self.dyn_frame, text="Card / Bank Amount:", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.entry_split_card = ctk.CTkEntry(self.dyn_frame, height=38, font=FONTS["body_lg"])
        self.entry_split_card.pack(fill="x", pady=(2, 10))
        self.entry_split_card.insert(0, f"{self.total_amount - half:g}")

        ctk.CTkLabel(self.dyn_frame, text="Order Note (Optional):", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 2))
        self.entry_note = ctk.CTkEntry(self.dyn_frame, height=36, placeholder_text="Split payment details...")
        self.entry_note.pack(fill="x")

    def _render_credit_form(self):
        self._clear_dyn_frame()
        credit_box = ctk.CTkFrame(self.dyn_frame, fg_color=COLORS["warning_subtle"], corner_radius=8)
        credit_box.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            credit_box, text="Customer Credit (Khata / Udhar)",
            font=FONTS["title_md"], text_color=COLORS["warning"]
        ).pack(pady=(15, 5))

        if not self.customer:
            ctk.CTkLabel(
                credit_box,
                text="⚠️ No customer selected!\nPlease select an existing customer from the POS screen\nbefore selling on credit.",
                font=FONTS["body_md"], text_color=COLORS["danger"], justify="center"
            ).pack(pady=10)
        else:
            ctk.CTkLabel(
                credit_box,
                text=f"Customer: {self.customer['name']}\nCurrent Balance: {self.currency} {self.customer.get('balance', 0):,.2f}\n\nThis sale of {self.currency} {self.total_amount:,.2f} will be added to the customer's due ledger.",
                font=FONTS["body_md"], text_color=COLORS["text_primary"], justify="center"
            ).pack(pady=10)

        ctk.CTkLabel(self.dyn_frame, text="Credit / Due Note:", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 2))
        self.entry_note = ctk.CTkEntry(self.dyn_frame, height=36, placeholder_text="e.g. Promised to pay next Friday...")
        self.entry_note.pack(fill="x")

    def _on_confirm(self):
        note = getattr(self, "entry_note", None)
        note_str = note.get().strip() if note else ""

        amount_paid = self.total_amount

        if self.payment_method == "cash":
            try:
                rec_str = self.entry_received.get().strip()
                amount_paid = float(rec_str) if rec_str else self.total_amount
            except ValueError:
                return
        elif self.payment_method == "card":
            amount_paid = self.total_amount
        elif self.payment_method == "split":
            try:
                cash_part = float(self.entry_split_cash.get().strip() or 0)
                card_part = float(self.entry_split_card.get().strip() or 0)
                amount_paid = cash_part + card_part
                note_str = f"Split: Cash {self.currency} {cash_part:,.2f}, Card {self.currency} {card_part:,.2f}. {note_str}".strip()
            except ValueError:
                return
        elif self.payment_method == "credit":
            if not self.customer:
                return # Block credit without registered customer
            amount_paid = 0.0

        self.result = {
            "payment_method": self.payment_method,
            "amount_paid": amount_paid,
            "note": note_str
        }

        self.destroy()
        if self.on_complete:
            self.on_complete(self.result)
