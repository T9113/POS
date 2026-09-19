import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.controllers.pos_controller import POSController
from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.payment_dialog import PaymentDialog
from pos_app.views.dialogs.hold_orders_dialog import HoldOrdersDialog
from pos_app.views.dialogs.receipt_preview_dialog import ReceiptPreviewDialog
from pos_app.utils.sound import play_beep
from pos_app.utils.receipt_printer import ReceiptPrinter

class POSView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.controller = POSController()
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.active_category_id = None
        self.view_mode = "grid" # 'grid' or 'list'
        self.all_customers = []

        self._build_layout()
        self._load_categories()
        self._load_customers()
        self._refresh_products()
        self._refresh_cart()

    def _build_layout(self):
        # 3-column / 2-column layout:
        # Left: Category Sidebar (width ~160)
        # Center: Search bar + Products Grid / List (expandable)
        # Right: Cart & Checkout Panel (fixed width ~380)

        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=12, pady=12)

        # 1. Left Category Sidebar
        self.cat_sidebar = ctk.CTkFrame(main_box, width=160, fg_color=COLORS["bg_surface"], corner_radius=10)
        self.cat_sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.cat_sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.cat_sidebar, text="CATEGORIES", font=FONTS["title_sm"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.cat_scroll = ctk.CTkScrollableFrame(self.cat_sidebar, fg_color="transparent")
        self.cat_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        # 2. Right Cart Panel (Built before center so it stays on right)
        self.cart_panel = ctk.CTkFrame(main_box, width=400, fg_color=COLORS["bg_surface"], corner_radius=10)
        self.cart_panel.pack(side="right", fill="both", padx=(10, 0))
        self.cart_panel.pack_propagate(False)
        self._build_cart_panel()

        # 3. Center Product Explorer
        self.center_panel = ctk.CTkFrame(main_box, fg_color="transparent")
        self.center_panel.pack(side="left", fill="both", expand=True)
        self._build_center_panel()

    def _build_center_panel(self):
        # Search and Toolbar Header
        toolbar = ctk.CTkFrame(self.center_panel, fg_color=COLORS["bg_surface"], corner_radius=10, height=54)
        toolbar.pack(fill="x", pady=(0, 10))
        toolbar.pack_propagate(False)

        # Search / Barcode Entry
        ctk.CTkLabel(toolbar, text="🔍", font=("Segoe UI", 14)).pack(side="left", padx=(14, 4))
        self.entry_search = ctk.CTkEntry(
            toolbar, placeholder_text="Scan Barcode or Search Products (F2)...",
            font=FONTS["body_lg"], height=38, border_width=0, fg_color=COLORS["bg_input"]
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(4, 10), pady=8)
        self.entry_search.bind("<KeyRelease>", self._on_search_type)
        self.entry_search.bind("<Return>", self._on_barcode_enter)

        # View Mode Toggle (Grid vs List)
        self.btn_view_mode = ctk.CTkSegmentedButton(
            toolbar, values=["Grid", "List"], command=self._toggle_view_mode,
            height=32, font=FONTS["body_sm"]
        )
        self.btn_view_mode.set("Grid")
        self.btn_view_mode.pack(side="right", padx=(0, 12))

        # Product Scrollable Area
        self.products_scroll = ctk.CTkScrollableFrame(self.center_panel, fg_color="transparent")
        self.products_scroll.pack(fill="both", expand=True)

    def _build_cart_panel(self):
        # Customer Row
        cust_row = ctk.CTkFrame(self.cart_panel, fg_color="transparent")
        cust_row.pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(cust_row, text="👤", font=("Segoe UI", 13)).pack(side="left", padx=(0, 4))
        self.opt_customer = ctk.CTkOptionMenu(
            cust_row, values=["Walk-in Customer"],
            command=self._on_customer_change, height=34, font=FONTS["body_md"]
        )
        self.opt_customer.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            cust_row, text="Clear (F1)", width=75, height=34,
            fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
            hover_color=COLORS["danger"], font=FONTS["body_sm"],
            command=self._on_clear_cart
        ).pack(side="right", padx=(8, 0))

        # Divider
        ctk.CTkFrame(self.cart_panel, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=14, pady=4)

        # Cart Items Header
        cart_hdr = ctk.CTkFrame(self.cart_panel, fg_color="transparent")
        cart_hdr.pack(fill="x", padx=14, pady=(4, 4))
        ctk.CTkLabel(cart_hdr, text="ITEM", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=150, anchor="w").pack(side="left")
        ctk.CTkLabel(cart_hdr, text="QTY", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=70).pack(side="left")
        ctk.CTkLabel(cart_hdr, text="TOTAL", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=90, anchor="e").pack(side="right")

        # Scrollable Cart Items Container
        self.cart_scroll = ctk.CTkScrollableFrame(self.cart_panel, fg_color=COLORS["bg_input"], corner_radius=8)
        self.cart_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        # Cart Summary Box
        summary_box = ctk.CTkFrame(self.cart_panel, fg_color=COLORS["bg_card"], corner_radius=8)
        summary_box.pack(fill="x", padx=14, pady=(0, 8))

        self.lbl_subtotal = self._create_summary_row(summary_box, "Subtotal", f"{self.currency} 0.00")
        
        # Discount row with interactive button
        disc_row = ctk.CTkFrame(summary_box, fg_color="transparent")
        disc_row.pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(
            disc_row, text="Discount 🏷️", font=FONTS["body_sm"],
            fg_color="transparent", text_color=COLORS["primary"],
            hover_color=COLORS["bg_hover"], width=70, height=22,
            command=self._prompt_discount
        ).pack(side="left")
        self.lbl_discount = ctk.CTkLabel(disc_row, text=f"-{self.currency} 0.00", font=FONTS["body_md"], text_color=COLORS["text_secondary"])
        self.lbl_discount.pack(side="right")

        self.lbl_tax = self._create_summary_row(summary_box, "Tax", f"{self.currency} 0.00")

        ctk.CTkFrame(summary_box, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=4)

        # Grand Total
        total_row = ctk.CTkFrame(summary_box, fg_color="transparent")
        total_row.pack(fill="x", padx=12, pady=(2, 6))
        ctk.CTkLabel(total_row, text="GRAND TOTAL", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        self.lbl_grand_total = ctk.CTkLabel(total_row, text=f"{self.currency} 0.00", font=FONTS["title_xl"], text_color=COLORS["primary"])
        self.lbl_grand_total.pack(side="right")

        # Action Buttons: Hold (F3), Recall (F4)
        hold_bar = ctk.CTkFrame(self.cart_panel, fg_color="transparent")
        hold_bar.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(
            hold_bar, text="⏸ Hold (F3)", height=36, font=FONTS["body_md"],
            fg_color=COLORS["warning_subtle"], text_color=COLORS["warning"],
            hover_color=COLORS["warning"], command=self._on_hold_order
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            hold_bar, text="📂 Recall (F4)", height=36, font=FONTS["body_md"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=self._on_recall_order
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Main Big Charge Button (F5) - min 48px height touch friendly
        self.btn_charge = ctk.CTkButton(
            self.cart_panel, text=f"CHARGE {self.currency} 0.00 (F5)",
            height=52, font=FONTS["title_lg"], fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"], text_color="#FFFFFF",
            corner_radius=8, command=self._on_checkout
        )
        self.btn_charge.pack(fill="x", padx=14, pady=(0, 14))

    def _create_summary_row(self, parent, label: str, val: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(row, text=label, font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(side="left")
        lbl_val = ctk.CTkLabel(row, text=val, font=FONTS["body_md"], text_color=COLORS["text_secondary"])
        lbl_val.pack(side="right")
        return lbl_val

    def _load_categories(self):
        for w in self.cat_scroll.winfo_children():
            w.destroy()

        categories = CategoryModel.list_all(active_only=True)
        
        # 'All' category button
        all_btn = ctk.CTkButton(
            self.cat_scroll, text="All Items", font=FONTS["body_md"],
            fg_color=COLORS["primary"] if self.active_category_id is None else "transparent",
            text_color="#FFFFFF" if self.active_category_id is None else COLORS["text_primary"],
            hover_color=COLORS["primary_hover"], height=36, anchor="w",
            command=lambda: self._select_category(None)
        )
        all_btn.pack(fill="x", pady=2)

        for cat in categories:
            is_active = self.active_category_id == cat["id"]
            btn = ctk.CTkButton(
                self.cat_scroll, text=cat["name"], font=FONTS["body_md"],
                fg_color=COLORS["primary"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else COLORS["text_primary"],
                hover_color=COLORS["primary_hover"], height=36, anchor="w",
                command=lambda cid=cat["id"]: self._select_category(cid)
            )
            btn.pack(fill="x", pady=2)

    def _select_category(self, cat_id):
        self.active_category_id = cat_id
        self._load_categories()
        self._refresh_products()

    def _load_customers(self):
        self.all_customers = CustomerModel.list_all(limit=200)
        options = ["Walk-in Customer"] + [f"{c['name']} ({c.get('phone') or 'No phone'})" for c in self.all_customers]
        self.opt_customer.configure(values=options)

    def _on_customer_change(self, choice):
        if choice == "Walk-in Customer":
            self.controller.set_customer(None)
        else:
            idx = self.opt_customer.cget("values").index(choice) - 1
            if 0 <= idx < len(self.all_customers):
                self.controller.set_customer(self.all_customers[idx])

    def _on_search_type(self, event=None):
        self._refresh_products()

    def _on_barcode_enter(self, event=None):
        code = self.entry_search.get().strip()
        if not code:
            return

        # Check if code directly matches a product
        prod = ProductModel.get_by_barcode_or_sku(code)
        if prod:
            self.controller.add_product(prod, 1.0)
            play_beep("beep")
            self.entry_search.delete(0, "end")
            self._refresh_cart()
            self._refresh_products()
        else:
            # Fallback search
            self._refresh_products()

    def _toggle_view_mode(self, mode):
        self.view_mode = mode.lower()
        self._refresh_products()

    def _refresh_products(self):
        for w in self.products_scroll.winfo_children():
            w.destroy()

        query = self.entry_search.get().strip()
        products = ProductModel.search_products(
            query=query, category_id=self.active_category_id,
            active_only=True, limit=60
        )

        if not products:
            ctk.CTkLabel(
                self.products_scroll, text="No products found.\nTry a different search term or add products in Catalog.",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"], justify="center"
            ).pack(pady=40)
            return

        if self.view_mode == "grid":
            # Grid layout (3 or 4 columns)
            grid_frame = ctk.CTkFrame(self.products_scroll, fg_color="transparent")
            grid_frame.pack(fill="both", expand=True)

            cols = 3
            for i in range(cols):
                grid_frame.columnconfigure(i, weight=1, uniform="col")

            for idx, prod in enumerate(products):
                r = idx // cols
                c = idx % cols
                self._render_product_card(grid_frame, prod, r, c)
        else:
            # List layout
            for prod in products:
                self._render_product_row(self.products_scroll, prod)

    def _render_product_card(self, parent, prod, row, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        # Stock indicator badge
        stock = prod.get("current_stock", 0)
        min_s = prod.get("min_stock", 5)
        stock_color = COLORS["danger"] if stock <= min_s else COLORS["text_secondary"]
        stock_text = f"Stock: {stock:g} {prod.get('unit', 'pc')}"

        top_info = ctk.CTkFrame(card, fg_color="transparent")
        top_info.pack(fill="x", padx=10, pady=(10, 4))
        
        cat_tag = prod.get("category_name") or "General"
        ctk.CTkLabel(top_info, text=cat_tag[:14], font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(top_info, text=stock_text, font=FONTS["body_sm"], text_color=stock_color).pack(side="right")

        # Name
        name_lbl = ctk.CTkLabel(
            card, text=prod["name"], font=FONTS["title_sm"],
            text_color=COLORS["text_primary"], anchor="w", justify="left",
            wraplength=170
        )
        name_lbl.pack(fill="x", padx=10, pady=(2, 6))

        # Price and Add Button
        bottom_box = ctk.CTkFrame(card, fg_color="transparent")
        bottom_box.pack(fill="x", padx=10, pady=(4, 10))

        price = float(prod["selling_price"])
        ctk.CTkLabel(
            bottom_box, text=f"{self.currency} {price:,.2f}",
            font=FONTS["title_md"], text_color=COLORS["primary"]
        ).pack(side="left")

        btn_add = ctk.CTkButton(
            bottom_box, text="+ Add", width=60, height=30,
            font=FONTS["body_sm"], fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            command=lambda p=prod: self._add_to_cart(p)
        )
        btn_add.pack(side="right")

    def _render_product_row(self, parent, prod):
        row = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=8, height=44)
        row.pack(fill="x", pady=3, padx=2)

        name = prod["name"]
        cat = prod.get("category_name") or "General"
        code = prod.get("barcode") or prod.get("sku") or ""
        price = float(prod["selling_price"])
        stock = prod.get("current_stock", 0)

        ctk.CTkLabel(row, text=name[:30], font=FONTS["body_md"], text_color=COLORS["text_primary"], width=220, anchor="w").pack(side="left", padx=12)
        ctk.CTkLabel(row, text=code, font=FONTS["mono"], text_color=COLORS["text_muted"], width=110, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=cat, font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=90, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=f"{stock:g}", font=FONTS["body_md"], text_color=COLORS["text_secondary"], width=60).pack(side="left")
        ctk.CTkLabel(row, text=f"{self.currency} {price:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=100, anchor="e").pack(side="left", padx=10)

        ctk.CTkButton(
            row, text="+", width=36, height=30, font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=lambda p=prod: self._add_to_cart(p)
        ).pack(side="right", padx=10)

    def _add_to_cart(self, prod):
        self.controller.add_product(prod, 1.0)
        play_beep("beep")
        self._refresh_cart()

    def _refresh_cart(self):
        for w in self.cart_scroll.winfo_children():
            w.destroy()

        cart_items = list(self.controller.cart_items.values())

        if not cart_items:
            ctk.CTkLabel(
                self.cart_scroll, text="🛒 Cart is empty\nScan a barcode or click + Add",
                font=FONTS["body_md"], text_color=COLORS["text_muted"], justify="center"
            ).pack(pady=40)
        else:
            for itm in cart_items:
                self._render_cart_item_row(itm)

        summary = self.controller.get_summary()
        self.lbl_subtotal.configure(text=f"{self.currency} {summary['subtotal']:,.2f}")
        self.lbl_discount.configure(text=f"-{self.currency} {summary['discount_amount']:,.2f}")
        self.lbl_tax.configure(text=f"{self.currency} {summary['tax_amount']:,.2f}")
        self.lbl_grand_total.configure(text=f"{self.currency} {summary['grand_total']:,.2f}")
        self.btn_charge.configure(text=f"CHARGE {self.currency} {summary['grand_total']:,.2f} (F5)")

    def _render_cart_item_row(self, itm):
        pid = itm["product_id"]
        row = ctk.CTkFrame(self.cart_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
        row.pack(fill="x", pady=3, padx=2)

        # Left Info
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        ctk.CTkLabel(
            info, text=itm["product_name"][:20], font=FONTS["title_sm"],
            text_color=COLORS["text_primary"], anchor="w"
        ).pack(anchor="w")

        price_sub = f"{self.currency} {itm['unit_price']:,.2f}"
        if itm["discount"] > 0:
            price_sub += f" (-{itm['discount']:,.2f})"
        ctk.CTkLabel(
            info, text=price_sub, font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"], anchor="w"
        ).pack(anchor="w")

        # Quantity controls (+ / -)
        qty_box = ctk.CTkFrame(row, fg_color="transparent")
        qty_box.pack(side="left", padx=4)

        ctk.CTkButton(
            qty_box, text="−", width=26, height=26, font=FONTS["body_md"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=lambda p=pid: self._change_qty(p, -1)
        ).pack(side="left")

        ctk.CTkLabel(
            qty_box, text=f"{itm['quantity']:g}", width=32,
            font=FONTS["title_sm"], text_color=COLORS["text_primary"]
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            qty_box, text="+", width=26, height=26, font=FONTS["body_md"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=lambda p=pid: self._change_qty(p, 1)
        ).pack(side="left")

        # Line Total & Delete
        right_box = ctk.CTkFrame(row, fg_color="transparent")
        right_box.pack(side="right", padx=(4, 8))

        ctk.CTkLabel(
            right_box, text=f"{self.currency} {itm['total']:,.2f}",
            font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=75, anchor="e"
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            right_box, text="✕", width=24, height=24,
            fg_color="transparent", text_color=COLORS["danger"],
            hover_color=COLORS["danger_subtle"],
            command=lambda p=pid: self._remove_cart_item(p)
        ).pack(side="left")

    def _change_qty(self, pid, delta):
        self.controller.change_quantity(pid, delta)
        self._refresh_cart()

    def _remove_cart_item(self, pid):
        self.controller.remove_item(pid)
        self._refresh_cart()

    def _on_clear_cart(self):
        self.controller.clear_cart()
        self._refresh_cart()

    def _prompt_discount(self):
        # Dialog to input order-level discount
        dialog = ctk.CTkInputDialog(text="Enter overall discount amount or percentage (e.g. 10% or 50):", title="Order Discount")
        val_str = dialog.get_input()
        if val_str:
            val_str = val_str.strip()
            if val_str.endswith("%"):
                try:
                    pct = float(val_str[:-1])
                    self.controller.set_order_discount(pct, is_percentage=True)
                except ValueError:
                    pass
            else:
                try:
                    amt = float(val_str)
                    self.controller.set_order_discount(amt, is_percentage=False)
                except ValueError:
                    pass
            self._refresh_cart()

    def _on_hold_order(self):
        ok, msg = self.controller.hold_current_order()
        if ok:
            self._refresh_cart()

    def _on_recall_order(self):
        HoldOrdersDialog(self, on_recall=self._on_held_recalled)

    def _on_held_recalled(self, held_id):
        self.controller.recall_held_order(held_id)
        self._refresh_cart()

    def _on_checkout(self):
        if not self.controller.cart_items:
            return
        summary = self.controller.get_summary()
        PaymentDialog(
            self, total_amount=summary["grand_total"],
            customer=self.controller.selected_customer,
            on_complete=self._finalize_sale
        )

    def _finalize_sale(self, payment_result):
        ok, msg, order_details = self.controller.checkout(
            payment_method=payment_result["payment_method"],
            amount_paid=payment_result["amount_paid"],
            note=payment_result.get("note", "")
        )
        if ok:
            play_beep("success")
            self._refresh_cart()
            self._refresh_products()

            # Check auto-print setting
            auto_print = SettingsModel.get("auto_print", "0") == "1"
            if auto_print:
                ReceiptPrinter.print_receipt(order_details)
            else:
                # Open print preview dialog
                ReceiptPreviewDialog(self, order_details)

    def focus_search(self):
        self.entry_search.focus_set()
        self.entry_search.select_range(0, "end")
