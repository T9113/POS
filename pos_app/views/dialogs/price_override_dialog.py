import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.settings_model import SettingsModel

class PriceOverrideDialog(ctk.CTkToplevel):
    def __init__(self, parent, item: dict, on_override=None):
        super().__init__(parent)
        self.item = item
        self.on_override = on_override
        self.title("Price Override")
        self.geometry("420x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 420) // 2)
        y = py + max(0, (ph - 420) // 2)
        self.geometry(f"+{x}+{y}")

        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=8)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Price Override", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(10, 4))
        ctk.CTkLabel(
            container, text=f"Item: {self.item['product_name']}\nCurrent Unit Price: {self.currency} {self.item['unit_price']:,.2f}",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # New Price
        ctk.CTkLabel(container, text="New Unit Selling Price:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_price = ctk.CTkEntry(container, height=40, font=FONTS["mono_bold"])
        self.entry_price.pack(fill="x", padx=15, pady=(0, 15))
        self.entry_price.insert(0, str(self.item["unit_price"]))
        self.entry_price.focus_set()

        # Reason
        ctk.CTkLabel(container, text="Reason for Override:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 2))
        reasons = ["Manager Discretion", "Price Match Competitor", "Clearance / Expiring Soon", "Damaged Packaging", "Bulk Purchase Agreement", "Other"]
        self.opt_reason = ctk.CTkOptionMenu(container, values=reasons, height=36)
        self.opt_reason.pack(fill="x", padx=15, pady=(0, 10))

        self.entry_custom_reason = ctk.CTkEntry(container, height=36, placeholder_text="Specific note (optional)...")
        self.entry_custom_reason.pack(fill="x", padx=15, pady=(0, 15))

        self.lbl_error = ctk.CTkLabel(container, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self.lbl_error.pack(padx=15, pady=(0, 5))

        # Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkButton(
            btn_bar, text="Cancel (Esc)", fg_color=COLORS["border"],
            text_color=COLORS["text_primary"], height=42, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Apply Override", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            height=42, font=FONTS["title_sm"], command=self._apply
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _apply(self):
        val_str = self.entry_price.get().strip()
        try:
            new_p = float(val_str)
            if new_p < 0:
                self.lbl_error.configure(text="Price cannot be negative.")
                return
        except ValueError:
            self.lbl_error.configure(text="Please enter a valid price.")
            return

        reason = self.opt_reason.get()
        custom = self.entry_custom_reason.get().strip()
        final_reason = f"{reason}: {custom}" if custom else reason

        self.destroy()
        if self.on_override:
            self.on_override(self.item["product_id"], new_p, final_reason)
