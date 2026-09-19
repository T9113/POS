import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.controllers.inventory_controller import InventoryController

class StockAdjustDialog(ctk.CTkToplevel):
    def __init__(self, parent, product: dict, on_complete=None):
        super().__init__(parent)
        self.product = product
        self.on_complete = on_complete
        self.title(f"Adjust Stock - {product.get('name', '')}")
        self.geometry("450x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 450) // 2)
        y = py + max(0, (ph - 460) // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"Stock Adjustment", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(10, 2))
        ctk.CTkLabel(
            container, text=f"Product: {self.product.get('name')}\nCurrent Stock: {self.product.get('current_stock', 0):g} {self.product.get('unit', 'piece')}",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # Quantity change input
        ctk.CTkLabel(container, text="Quantity Change (+ to add, − to subtract):", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 4))
        self.entry_qty = ctk.CTkEntry(container, height=40, font=FONTS["title_md"], placeholder_text="e.g. +10 or -3")
        self.entry_qty.pack(fill="x", padx=15, pady=(0, 15))
        self.entry_qty.focus_set()

        # Reason selection
        ctk.CTkLabel(container, text="Adjustment Reason:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 4))
        reasons = ["Inventory Count", "Damaged Item", "Lost / Stolen", "Customer Return", "Expired", "Correction"]
        self.opt_reason = ctk.CTkOptionMenu(container, values=reasons, height=36)
        self.opt_reason.pack(fill="x", padx=15, pady=(0, 15))

        # Note
        ctk.CTkLabel(container, text="Audit Note (Optional):", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(0, 4))
        self.entry_note = ctk.CTkEntry(container, height=36, placeholder_text="Reason details...")
        self.entry_note.pack(fill="x", padx=15, pady=(0, 15))

        self.lbl_error = ctk.CTkLabel(container, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self.lbl_error.pack(padx=15, pady=(0, 5))

        # Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Cancel (Esc)", fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], height=42, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Save Adjustment", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            height=42, font=FONTS["title_sm"], command=self._confirm
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _confirm(self):
        val_str = self.entry_qty.get().strip()
        try:
            qty_delta = float(val_str)
            if qty_delta == 0:
                self.lbl_error.configure(text="Quantity change cannot be 0.")
                return
        except ValueError:
            self.lbl_error.configure(text="Please enter a valid number (e.g. 5 or -2).")
            return

        reason = self.opt_reason.get()
        note = self.entry_note.get().strip()

        ok, msg = InventoryController.adjust_stock(self.product["id"], qty_delta, reason, note)
        if ok:
            self.destroy()
            if self.on_complete:
                self.on_complete()
        else:
            self.lbl_error.configure(text=msg)
