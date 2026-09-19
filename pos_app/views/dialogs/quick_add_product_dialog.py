import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.category_model import CategoryModel
from pos_app.controllers.product_controller import ProductController

class QuickAddProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, barcode: str = "", on_product_added=None):
        super().__init__(parent)
        self.barcode = barcode
        self.on_product_added = on_product_added
        self.title("Quick-Add New Product")
        self.geometry("460x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 460) // 2)
        y = py + max(0, (ph - 520) // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=8)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container, text="Product Not Found",
            font=FONTS["title_md"], text_color=COLORS["warning"]
        ).pack(anchor="w", padx=15, pady=(10, 2))

        ctk.CTkLabel(
            container, text="Quickly register this item to immediately add it to the cart.",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # Barcode (pre-filled)
        ctk.CTkLabel(container, text="Barcode", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_barcode = ctk.CTkEntry(container, height=36, font=FONTS["mono"])
        self.entry_barcode.pack(fill="x", padx=15, pady=(0, 10))
        self.entry_barcode.insert(0, self.barcode)

        # Name
        ctk.CTkLabel(container, text="Product Name *", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_name = ctk.CTkEntry(container, height=36, placeholder_text="e.g. New Chocolate Bar")
        self.entry_name.pack(fill="x", padx=15, pady=(0, 10))
        self.entry_name.focus_set()

        # Category
        ctk.CTkLabel(container, text="Category", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 2))
        cats = CategoryModel.list_all(active_only=True)
        cat_names = [c["name"] for c in cats] or ["General"]
        self.opt_category = ctk.CTkOptionMenu(container, values=cat_names, height=36)
        self.opt_category.pack(fill="x", padx=15, pady=(0, 10))

        # Price row: Selling Price & Cost Price
        pr_row = ctk.CTkFrame(container, fg_color="transparent")
        pr_row.pack(fill="x", padx=15, pady=(0, 10))

        p1 = ctk.CTkFrame(pr_row, fg_color="transparent")
        p1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(p1, text="Selling Price *", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_sell = ctk.CTkEntry(p1, height=36, placeholder_text="0.00")
        self.entry_sell.pack(fill="x", pady=(2, 0))

        p2 = ctk.CTkFrame(pr_row, fg_color="transparent")
        p2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(p2, text="Initial Stock", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_stock = ctk.CTkEntry(p2, height=36, placeholder_text="10")
        self.entry_stock.pack(fill="x", pady=(2, 0))
        self.entry_stock.insert(0, "10")

        self.lbl_error = ctk.CTkLabel(container, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self.lbl_error.pack(padx=15, pady=(0, 5))

        # Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(10, 10))

        ctk.CTkButton(
            btn_bar, text="Cancel (Esc)", fg_color=COLORS["border"],
            text_color=COLORS["text_primary"], height=42, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Save & Add to Cart", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            height=42, font=FONTS["title_sm"], command=self._save_and_add
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _save_and_add(self):
        name = self.entry_name.get().strip()
        if not name:
            self.lbl_error.configure(text="Product Name is required.")
            return

        try:
            sell_price = float(self.entry_sell.get().strip())
            stock = float(self.entry_stock.get().strip() or 10)
        except ValueError:
            self.lbl_error.configure(text="Please enter valid numbers for price and stock.")
            return

        cat_id = CategoryModel.get_or_create(self.opt_category.get())
        barcode = self.entry_barcode.get().strip() or None

        data = {
            "name": name,
            "barcode": barcode,
            "category_id": cat_id,
            "selling_price": sell_price,
            "cost_price": round(sell_price * 0.7, 2),
            "current_stock": stock,
            "min_stock": 5.0,
            "unit": "piece",
            "is_active": 1
        }

        ok, msg, pid = ProductController.save_product(data)
        if ok:
            created_prod = ProductController.get_product(pid)
            self.destroy()
            if self.on_product_added and created_prod:
                self.on_product_added(created_prod)
        else:
            self.lbl_error.configure(text=msg)
