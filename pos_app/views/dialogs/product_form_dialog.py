import secrets
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.category_model import CategoryModel
from pos_app.controllers.product_controller import ProductController

class ProductFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, product: dict = None, on_saved=None):
        super().__init__(parent)
        self.product = product
        self.on_saved = on_saved
        self.title("Edit Product" if product else "Add New Product")
        self.geometry("620x700")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 620) // 2)
        y = py + max(0, (ph - 700) // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 15))

        title_text = f"Edit Product: {self.product['name']}" if self.product else "Create New Product"
        ctk.CTkLabel(header, text=title_text, font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")

        # Scrollable form body
        body = ctk.CTkScrollableFrame(container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 1. Product Name
        ctk.CTkLabel(body, text="Product Name *", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(5, 2))
        self.entry_name = ctk.CTkEntry(body, height=38, font=FONTS["body_lg"], placeholder_text="e.g. Basmati Rice 5kg")
        self.entry_name.pack(fill="x", pady=(0, 10))
        if self.product:
            self.entry_name.insert(0, self.product.get("name", ""))

        # 2. SKU and Barcode (Row)
        sku_row = ctk.CTkFrame(body, fg_color="transparent")
        sku_row.pack(fill="x", pady=(0, 10))

        sku_col = ctk.CTkFrame(sku_row, fg_color="transparent")
        sku_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(sku_col, text="SKU / Item Code", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        sku_input_box = ctk.CTkFrame(sku_col, fg_color="transparent")
        sku_input_box.pack(fill="x")
        self.entry_sku = ctk.CTkEntry(sku_input_box, height=36, placeholder_text="Auto or custom")
        self.entry_sku.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            sku_input_box, text="Gen", width=44, height=36,
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=self._generate_sku
        ).pack(side="right", padx=(5, 0))
        if self.product and self.product.get("sku"):
            self.entry_sku.insert(0, self.product["sku"])

        bar_col = ctk.CTkFrame(sku_row, fg_color="transparent")
        bar_col.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(bar_col, text="Barcode (Scan or Type)", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        self.entry_barcode = ctk.CTkEntry(bar_col, height=36, placeholder_text="e.g. 890123456789")
        self.entry_barcode.pack(fill="x")
        if self.product and self.product.get("barcode"):
            self.entry_barcode.insert(0, self.product["barcode"])

        # 3. Category and Unit (Row)
        cat_row = ctk.CTkFrame(body, fg_color="transparent")
        cat_row.pack(fill="x", pady=(0, 10))

        cat_col = ctk.CTkFrame(cat_row, fg_color="transparent")
        cat_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(cat_col, text="Category", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))

        self.categories = CategoryModel.list_all(active_only=True)
        cat_names = [c["name"] for c in self.categories] or ["General"]
        self.opt_category = ctk.CTkOptionMenu(cat_col, values=cat_names, height=36, font=FONTS["body_md"])
        self.opt_category.pack(fill="x")
        if self.product and self.product.get("category_name"):
            if self.product["category_name"] in cat_names:
                self.opt_category.set(self.product["category_name"])

        unit_col = ctk.CTkFrame(cat_row, fg_color="transparent")
        unit_col.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(unit_col, text="Unit of Measurement", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        units = ["piece", "kg", "gram", "liter", "meter", "box", "pack", "dozen", "pair", "bottle", "can"]
        self.opt_unit = ctk.CTkOptionMenu(unit_col, values=units, height=36, font=FONTS["body_md"])
        self.opt_unit.pack(fill="x")
        current_unit = self.product.get("unit", "piece") if self.product else "piece"
        self.opt_unit.set(current_unit if current_unit in units else "piece")

        # 4. Pricing (Cost, Selling, Wholesale)
        price_row = ctk.CTkFrame(body, fg_color="transparent")
        price_row.pack(fill="x", pady=(0, 10))

        # Cost Price
        cost_col = ctk.CTkFrame(price_row, fg_color="transparent")
        cost_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(cost_col, text="Cost Price", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        self.entry_cost = ctk.CTkEntry(cost_col, height=36, placeholder_text="0.00")
        self.entry_cost.pack(fill="x")
        self.entry_cost.insert(0, str(self.product.get("cost_price", 0.0) if self.product else 0.0))

        # Selling Price
        sell_col = ctk.CTkFrame(price_row, fg_color="transparent")
        sell_col.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(sell_col, text="Selling Price *", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        self.entry_sell = ctk.CTkEntry(sell_col, height=36, placeholder_text="0.00")
        self.entry_sell.pack(fill="x")
        self.entry_sell.insert(0, str(self.product.get("selling_price", 0.0) if self.product else 0.0))

        # Wholesale Price
        ws_col = ctk.CTkFrame(price_row, fg_color="transparent")
        ws_col.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(ws_col, text="Wholesale Price", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        self.entry_wholesale = ctk.CTkEntry(ws_col, height=36, placeholder_text="0.00")
        self.entry_wholesale.pack(fill="x")
        self.entry_wholesale.insert(0, str(self.product.get("wholesale_price", 0.0) if self.product else 0.0))

        # 5. Stock Levels (Current Stock, Min Stock)
        stock_row = ctk.CTkFrame(body, fg_color="transparent")
        stock_row.pack(fill="x", pady=(0, 10))

        cur_stock_col = ctk.CTkFrame(stock_row, fg_color="transparent")
        cur_stock_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(cur_stock_col, text="Initial / Current Stock", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        self.entry_current_stock = ctk.CTkEntry(cur_stock_col, height=36, placeholder_text="0")
        self.entry_current_stock.pack(fill="x")
        self.entry_current_stock.insert(0, str(self.product.get("current_stock", 0) if self.product else 0))

        min_stock_col = ctk.CTkFrame(stock_row, fg_color="transparent")
        min_stock_col.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(min_stock_col, text="Min Stock Alert Level", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 2))
        self.entry_min_stock = ctk.CTkEntry(min_stock_col, height=36, placeholder_text="5")
        self.entry_min_stock.pack(fill="x")
        self.entry_min_stock.insert(0, str(self.product.get("min_stock", 5) if self.product else 5))

        # 6. Description / Notes
        ctk.CTkLabel(body, text="Description / Details", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(5, 2))
        self.entry_desc = ctk.CTkEntry(body, height=36, placeholder_text="Optional product description...")
        self.entry_desc.pack(fill="x", pady=(0, 10))
        if self.product and self.product.get("description"):
            self.entry_desc.insert(0, self.product["description"])

        # Error label
        self.lbl_error = ctk.CTkLabel(body, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self.lbl_error.pack(anchor="w", pady=(0, 5))

        # Bottom Buttons
        bottom_bar = ctk.CTkFrame(container, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkButton(
            bottom_bar, text="Cancel (Esc)", fg_color=COLORS["bg_hover"],
            hover_color=COLORS["border"], text_color=COLORS["text_primary"],
            height=44, font=FONTS["body_lg"], command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            bottom_bar, text="Save Product", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            height=44, font=FONTS["title_sm"], command=self._save
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _generate_sku(self):
        token = secrets.token_hex(4).upper()
        self.entry_sku.delete(0, "end")
        self.entry_sku.insert(0, f"SKU-{token}")

    def _save(self):
        name = self.entry_name.get().strip()
        if not name:
            self.lbl_error.configure(text="Product Name is required.")
            return

        try:
            cost_price = float(self.entry_cost.get().strip() or 0.0)
            selling_price = float(self.entry_sell.get().strip() or 0.0)
            wholesale_price = float(self.entry_wholesale.get().strip() or 0.0)
            current_stock = float(self.entry_current_stock.get().strip() or 0.0)
            min_stock = float(self.entry_min_stock.get().strip() or 5.0)
        except ValueError:
            self.lbl_error.configure(text="Please enter valid numbers for price and stock fields.")
            return

        selected_cat_name = self.opt_category.get()
        cat_id = CategoryModel.get_or_create(selected_cat_name)

        data = {
            "name": name,
            "sku": self.entry_sku.get().strip() or None,
            "barcode": self.entry_barcode.get().strip() or None,
            "category_id": cat_id,
            "unit": self.opt_unit.get(),
            "cost_price": cost_price,
            "selling_price": selling_price,
            "wholesale_price": wholesale_price,
            "current_stock": current_stock,
            "min_stock": min_stock,
            "description": self.entry_desc.get().strip(),
            "is_active": 1
        }

        pid = self.product["id"] if self.product else None
        ok, msg, res_id = ProductController.save_product(data, pid)
        if ok:
            self.destroy()
            if self.on_saved:
                self.on_saved()
        else:
            self.lbl_error.configure(text=msg)
