import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.supplier_model import SupplierModel
from pos_app.models.product_model import ProductModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.inventory_controller import InventoryController

class PurchaseOrderDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_complete=None, initial_items=None):
        super().__init__(parent)
        self.on_complete = on_complete
        self.title("New Purchase / Stock-In")
        self.geometry("700x650")
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 700) // 2)
        y = py + max(0, (ph - 650) // 2)
        self.geometry(f"+{x}+{y}")

        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.po_items = list(initial_items) if initial_items else [] # list of dicts: {product_id, product_name, quantity, cost_price, total}
        self.suppliers = SupplierModel.list_all()
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(container, text="Stock-In / Purchase Order", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(10, 5))

        # Supplier Row
        sup_frame = ctk.CTkFrame(container, fg_color="transparent")
        sup_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(sup_frame, text="Supplier:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left", padx=(0, 10))
        sup_names = [s["name"] for s in self.suppliers] or ["No Suppliers Configured"]
        self.opt_supplier = ctk.CTkOptionMenu(sup_frame, values=sup_names, height=36, font=FONTS["body_md"])
        self.opt_supplier.pack(side="left", fill="x", expand=True)

        # Add Item Section
        add_box = ctk.CTkFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        add_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(add_box, text="Add Product to Purchase:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=10, pady=(8, 4))

        input_row = ctk.CTkFrame(add_box, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=(0, 8))

        self.entry_search_item = ctk.CTkEntry(input_row, height=36, placeholder_text="Barcode / SKU / Name...")
        self.entry_search_item.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.entry_qty = ctk.CTkEntry(input_row, width=80, height=36, placeholder_text="Qty")
        self.entry_qty.pack(side="left", padx=3)
        self.entry_qty.insert(0, "10")

        self.entry_cost = ctk.CTkEntry(input_row, width=100, height=36, placeholder_text="Cost Price")
        self.entry_cost.pack(side="left", padx=3)

        ctk.CTkButton(
            input_row, text="+ Add Item", width=90, height=36,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._add_item
        ).pack(side="left", padx=(5, 0))

        self.lbl_add_err = ctk.CTkLabel(add_box, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self.lbl_add_err.pack(anchor="w", padx=10, pady=(0, 5))

        # Items Table
        self.items_scroll = ctk.CTkScrollableFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        self.items_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Total and Note
        bottom_info = ctk.CTkFrame(container, fg_color="transparent")
        bottom_info.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_po_total = ctk.CTkLabel(
            bottom_info, text=f"Total Purchase Amount: {self.currency} 0.00",
            font=FONTS["title_md"], text_color=COLORS["success"]
        )
        self.lbl_po_total.pack(anchor="w", pady=(0, 5))

        self.entry_po_note = ctk.CTkEntry(bottom_info, height=36, placeholder_text="Purchase Order Note / Invoice #...")
        self.entry_po_note.pack(fill="x")

        # Bottom Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Cancel (Esc)", fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], height=42, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Receive & Update Stock", fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"], text_color="#FFFFFF",
            height=42, font=FONTS["title_sm"], command=self._receive_order
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

        self._refresh_items_table()

    def _add_item(self):
        query = self.entry_search_item.get().strip()
        if not query:
            self.lbl_add_err.configure(text="Please enter product barcode, SKU, or name.")
            return

        # Find product
        prod = ProductModel.get_by_barcode_or_sku(query)
        if not prod:
            matches = ProductModel.search_products(query, limit=1)
            prod = matches[0] if matches else None

        if not prod:
            self.lbl_add_err.configure(text=f"No product found matching '{query}'.")
            return

        try:
            qty = float(self.entry_qty.get().strip() or 1)
            cost_str = self.entry_cost.get().strip()
            cost = float(cost_str) if cost_str else float(prod.get("cost_price", 0))
            if qty <= 0:
                self.lbl_add_err.configure(text="Quantity must be greater than 0.")
                return
        except ValueError:
            self.lbl_add_err.configure(text="Invalid quantity or cost number.")
            return

        self.lbl_add_err.configure(text="")
        total = round(qty * cost, 2)
        self.po_items.append({
            "product_id": prod["id"],
            "product_name": prod["name"],
            "quantity": qty,
            "cost_price": cost,
            "total": total
        })

        self.entry_search_item.delete(0, "end")
        self.entry_cost.delete(0, "end")
        self._refresh_items_table()

    def _refresh_items_table(self):
        for w in self.items_scroll.winfo_children():
            w.destroy()

        if not self.po_items:
            ctk.CTkLabel(self.items_scroll, text="No items added yet.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            self.lbl_po_total.configure(text=f"Total Purchase Amount: {self.currency} 0.00")
            return

        total_sum = 0.0
        for idx, itm in enumerate(self.po_items):
            total_sum += itm["total"]
            row = ctk.CTkFrame(self.items_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=itm["product_name"][:26], font=FONTS["body_md"], text_color=COLORS["text_primary"], width=220, anchor="w").pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=f"Qty: {itm['quantity']:g}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=80).pack(side="left", pady=6)
            ctk.CTkLabel(row, text=f"Cost: {self.currency} {itm['cost_price']:,.2f}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=120).pack(side="left", pady=6)
            ctk.CTkLabel(row, text=f"Total: {self.currency} {itm['total']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=120).pack(side="left", pady=6)

            ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
                command=lambda i=idx: self._remove_item(i)
            ).pack(side="right", padx=6)

        self.lbl_po_total.configure(text=f"Total Purchase Amount: {self.currency} {total_sum:,.2f}")

    def _remove_item(self, idx: int):
        if 0 <= idx < len(self.po_items):
            self.po_items.pop(idx)
            self._refresh_items_table()

    def _receive_order(self):
        if not self.po_items:
            self.lbl_add_err.configure(text="Please add at least one item before receiving.")
            return

        sel_name = self.opt_supplier.get()
        sup = next((s for s in self.suppliers if s["name"] == sel_name), None)
        supplier_id = sup["id"] if sup else None

        note = self.entry_po_note.get().strip()
        ok, msg, pid = InventoryController.receive_purchase(supplier_id, self.po_items, note)
        if ok:
            self.destroy()
            if self.on_complete:
                self.on_complete()
