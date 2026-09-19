import tkinter.filedialog as fd
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.product_controller import ProductController
from pos_app.views.dialogs.product_form_dialog import ProductFormDialog
from pos_app.views.dialogs.stock_adjust_dialog import StockAdjustDialog

class ProductsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.page = 1
        self.page_size = 25
        self.total_count = 0
        self.sort_by = "name"
        self.sort_order = "ASC"
        self.active_category_id = None
        self.selected_product_ids = set()

        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Header Toolbar
        top_bar = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10, height=60)
        top_bar.pack(fill="x", pady=(0, 10))
        top_bar.pack_propagate(False)

        # Search box
        ctk.CTkLabel(top_bar, text="🔍", font=("Segoe UI", 13)).pack(side="left", padx=(14, 4))
        self.entry_search = ctk.CTkEntry(
            top_bar, placeholder_text="Search Products (Name, Barcode, SKU)...",
            height=36, font=FONTS["body_md"], width=260
        )
        self.entry_search.pack(side="left", padx=(0, 10), pady=10)
        self.entry_search.bind("<KeyRelease>", self._on_search_changed)

        # Category Filter Dropdown
        categories = CategoryModel.list_all(active_only=True)
        cat_names = ["All Categories"] + [c["name"] for c in categories]
        self.opt_category = ctk.CTkOptionMenu(
            top_bar, values=cat_names, height=36, font=FONTS["body_sm"],
            command=self._on_category_selected
        )
        self.opt_category.pack(side="left", padx=5)

        # Sort By Dropdown
        self.opt_sort = ctk.CTkOptionMenu(
            top_bar, values=["Sort: Name", "Sort: Price (Low)", "Sort: Price (High)", "Sort: Stock"],
            height=36, font=FONTS["body_sm"], command=self._on_sort_changed
        )
        self.opt_sort.pack(side="left", padx=5)

        # Right Action Buttons
        ctk.CTkButton(
            top_bar, text="➕ Add Product", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=36, text_color="#FFFFFF", command=self._open_add_product
        ).pack(side="right", padx=(5, 14))

        ctk.CTkButton(
            top_bar, text="📤 Export", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            height=36, width=75, command=self._export_excel
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            top_bar, text="📥 Import", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            height=36, width=75, command=self._import_file
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            top_bar, text="💲 Bulk Price", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            height=36, width=90, command=self._bulk_price_update
        ).pack(side="right", padx=5)

        # 2. Products Table
        table_container = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10)
        table_container.pack(fill="both", expand=True, pady=(0, 10))

        # Table Column Headers
        header_row = ctk.CTkFrame(table_container, fg_color=COLORS["bg_input"], corner_radius=6, height=38)
        header_row.pack(fill="x", padx=10, pady=(10, 4))
        header_row.pack_propagate(False)

        ctk.CTkLabel(header_row, text="Product Name", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=230, anchor="w").pack(side="left", padx=(15, 5))
        ctk.CTkLabel(header_row, text="Barcode / SKU", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=130, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Category", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=110, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Cost", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=80, anchor="e").pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Price", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=90, anchor="e").pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Stock Level", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=120, anchor="center").pack(side="left", padx=10)
        ctk.CTkLabel(header_row, text="Actions", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=160, anchor="center").pack(side="right", padx=15)

        # Scrollable Rows
        self.rows_scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.rows_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        # 3. Bottom Pagination Bar
        pag_bar = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10, height=48)
        pag_bar.pack(fill="x")
        pag_bar.pack_propagate(False)

        self.lbl_stats = ctk.CTkLabel(pag_bar, text="Showing 0 products", font=FONTS["body_sm"], text_color=COLORS["text_secondary"])
        self.lbl_stats.pack(side="left", padx=20)

        nav_box = ctk.CTkFrame(pag_bar, fg_color="transparent")
        nav_box.pack(side="right", padx=20)

        self.btn_prev = ctk.CTkButton(
            nav_box, text="◀ Previous", width=90, height=32,
            font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], command=self._prev_page
        )
        self.btn_prev.pack(side="left", padx=5)

        self.lbl_page = ctk.CTkLabel(nav_box, text="Page 1 of 1", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=90)
        self.lbl_page.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(
            nav_box, text="Next ▶", width=80, height=32,
            font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], command=self._next_page
        )
        self.btn_next.pack(side="left", padx=5)

    def _on_search_changed(self, event=None):
        self.page = 1
        self._refresh_table()

    def _on_category_selected(self, choice):
        self.page = 1
        if choice == "All Categories":
            self.active_category_id = None
        else:
            cats = CategoryModel.list_all(active_only=True)
            match = next((c for c in cats if c["name"] == choice), None)
            self.active_category_id = match["id"] if match else None
        self._refresh_table()

    def _on_sort_changed(self, choice):
        self.page = 1
        if "Name" in choice:
            self.sort_by, self.sort_order = "name", "ASC"
        elif "Low" in choice:
            self.sort_by, self.sort_order = "selling_price", "ASC"
        elif "High" in choice:
            self.sort_by, self.sort_order = "selling_price", "DESC"
        elif "Stock" in choice:
            self.sort_by, self.sort_order = "current_stock", "ASC"
        self._refresh_table()

    def _prev_page(self):
        if self.page > 1:
            self.page -= 1
            self._refresh_table()

    def _next_page(self):
        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        if self.page < max_page:
            self.page += 1
            self._refresh_table()

    def _refresh_table(self):
        for w in self.rows_scroll.winfo_children():
            w.destroy()

        query = self.entry_search.get().strip()
        self.total_count = ProductModel.count_products(query, self.active_category_id, active_only=True)
        max_page = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.page = min(self.page, max_page)

        offset = (self.page - 1) * self.page_size
        products = ProductModel.search_products(
            query=query, category_id=self.active_category_id,
            active_only=True, limit=self.page_size, offset=offset,
            sort_by=self.sort_by, sort_order=self.sort_order
        )

        start_idx = offset + 1 if self.total_count > 0 else 0
        end_idx = min(offset + len(products), self.total_count)
        self.lbl_stats.configure(text=f"Showing {start_idx}-{end_idx} of {self.total_count:,} products")
        self.lbl_page.configure(text=f"Page {self.page} of {max_page}")

        self.btn_prev.configure(state="normal" if self.page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.page < max_page else "disabled")

        if not products:
            ctk.CTkLabel(
                self.rows_scroll, text="No products found matching criteria.",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"]
            ).pack(pady=40)
            return

        for prod in products:
            self._render_row(prod)

    def _render_row(self, prod):
        row = ctk.CTkFrame(self.rows_scroll, fg_color=COLORS["bg_card"], corner_radius=6, height=44)
        row.pack(fill="x", pady=2, padx=2)

        # Name
        name = prod["name"]
        ctk.CTkLabel(row, text=name[:28], font=FONTS["body_md"], text_color=COLORS["text_primary"], width=230, anchor="w").pack(side="left", padx=(15, 5))

        # Barcode / SKU
        code = prod.get("barcode") or prod.get("sku") or "-"
        ctk.CTkLabel(row, text=code, font=FONTS["mono"], text_color=COLORS["text_muted"], width=130, anchor="w").pack(side="left", padx=5)

        # Category
        cat = prod.get("category_name") or "General"
        ctk.CTkLabel(row, text=cat[:15], font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=110, anchor="w").pack(side="left", padx=5)

        # Cost & Price
        cost = float(prod.get("cost_price", 0))
        price = float(prod.get("selling_price", 0))
        ctk.CTkLabel(row, text=f"{cost:,.2f}", font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=80, anchor="e").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"{price:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=90, anchor="e").pack(side="left", padx=5)

        # Stock Status Badge (Color coded: Red = below min, Yellow = near min, Green = ok)
        stock = float(prod.get("current_stock", 0))
        min_s = float(prod.get("min_stock", 5))
        if stock <= 0:
            badge_bg = COLORS["danger_subtle"]
            badge_fg = COLORS["danger"]
            badge_txt = f"Out of Stock ({stock:g})"
        elif stock <= min_s:
            badge_bg = COLORS["warning_subtle"]
            badge_fg = COLORS["warning"]
            badge_txt = f"Low ({stock:g})"
        else:
            badge_bg = COLORS["success_subtle"]
            badge_fg = COLORS["success"]
            badge_txt = f"In Stock ({stock:g})"

        badge_box = ctk.CTkFrame(row, width=120, fg_color="transparent")
        badge_box.pack(side="left", padx=10)
        ctk.CTkLabel(
            badge_box, text=badge_txt, font=FONTS["body_sm"],
            fg_color=badge_bg, text_color=badge_fg, corner_radius=6, height=26
        ).pack(fill="x")

        # Action Buttons: Edit, Adjust Stock, Delete
        actions_box = ctk.CTkFrame(row, fg_color="transparent")
        actions_box.pack(side="right", padx=15)

        ctk.CTkButton(
            actions_box, text="✏️ Edit", width=55, height=28,
            font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            command=lambda p=prod: self._open_edit_product(p)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions_box, text="📦 Stock", width=58, height=28,
            font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            command=lambda p=prod: self._open_adjust_stock(p)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions_box, text="✕", width=28, height=28,
            font=FONTS["body_sm"], fg_color=COLORS["danger_subtle"],
            text_color=COLORS["danger"],
            command=lambda p=prod: self._delete_product(p)
        ).pack(side="left", padx=2)

    def _open_add_product(self):
        ProductFormDialog(self, product=None, on_saved=self._refresh_table)

    def _open_edit_product(self, prod):
        ProductFormDialog(self, product=prod, on_saved=self._refresh_table)

    def _open_adjust_stock(self, prod):
        StockAdjustDialog(self, product=prod, on_complete=self._refresh_table)

    def _delete_product(self, prod):
        ok, msg = ProductController.delete_product(prod["id"])
        if ok:
            self._refresh_table()

    def _bulk_price_update(self):
        # Dialog to update prices across current query
        dialog = ctk.CTkInputDialog(text="Enter price adjustment (e.g. +10% or +50 or -5%):", title="Bulk Price Update")
        val_str = dialog.get_input()
        if not val_str:
            return

        val_str = val_str.strip()
        is_pct = val_str.endswith("%")
        try:
            num = float(val_str[:-1] if is_pct else val_str)
            # Fetch IDs of products in current view
            query = self.entry_search.get().strip()
            all_matching = ProductModel.search_products(query, self.active_category_id, limit=5000)
            ids = [p["id"] for p in all_matching]
            if ids:
                ProductController.bulk_update_prices(ids, "percent" if is_pct else "fixed", num)
                self._refresh_table()
        except ValueError:
            pass

    def _export_excel(self):
        path = ProductController.export_products_excel()
        ctk.CTkInputDialog(text=f"Product catalog exported to:\n{path}", title="Export Complete")

    def _import_file(self):
        filepath = fd.askopenfilename(
            title="Import Products",
            filetypes=[("Spreadsheet files", "*.csv *.xlsx *.xls"), ("All files", "*.*")]
        )
        if filepath:
            res = ProductController.import_from_file(filepath)
            msg = f"Imported: {res['imported']} new\nUpdated: {res['updated']} existing\nFailed: {res['failed']}"
            ctk.CTkInputDialog(text=msg, title="Import Summary")
            self._refresh_table()
