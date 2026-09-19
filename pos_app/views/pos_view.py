import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS, RADII
from pos_app.controllers.pos_controller import POSController
from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.payment_dialog import PaymentDialog
from pos_app.views.dialogs.hold_orders_dialog import HoldOrdersDialog
from pos_app.views.dialogs.receipt_preview_dialog import ReceiptPreviewDialog
from pos_app.views.dialogs.quick_add_product_dialog import QuickAddProductDialog
from pos_app.views.dialogs.price_override_dialog import PriceOverrideDialog
from pos_app.views.dialogs.quick_return_dialog import QuickReturnDialog
from pos_app.utils.sound import play_beep
from pos_app.utils.receipt_printer import ReceiptPrinter

class POSView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.controller = POSController()
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.active_category_id = None
        self.view_mode = "grid"
        self.all_customers = []
        self.last_scanned_name = "Ready for items"

        self._build_layout()
        self._load_categories()
        self._load_customers()
        self._refresh_favorites()
        self._refresh_products()
        self._refresh_cart()

    def _build_layout(self):
        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=12, pady=12)

        # 1. Right Cart Panel (Fixed 360px width, surface raised)
        self.cart_panel = ctk.CTkFrame(main_box, width=360, fg_color=COLORS["bg_surface_raised"], corner_radius=RADII["panel"])
        self.cart_panel.pack(side="right", fill="both", padx=(10, 0))
        self.cart_panel.pack_propagate(False)
        self._build_cart_panel()

        # 2. Left / Center Product Explorer Panel
        self.center_panel = ctk.CTkFrame(main_box, fg_color="transparent")
        self.center_panel.pack(side="left", fill="both", expand=True)
        self._build_center_panel()

    def _build_center_panel(self):
        # Top Search Toolbar
        toolbar = ctk.CTkFrame(self.center_panel, fg_color=COLORS["bg_surface"], corner_radius=RADII["panel"], height=52)
        toolbar.pack(fill="x", pady=(0, 8))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text="🔍", font=("Segoe UI", 13), text_color=COLORS["text_secondary"]).pack(side="left", padx=(12, 4))
        self.entry_search = ctk.CTkEntry(
            toolbar, placeholder_text="Scan barcode or search products by name, SKU (F2)...",
            font=FONTS["body_md"], height=36, border_width=1, border_color=COLORS["border_input"],
            fg_color=COLORS["bg_input"]
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=8)
        self.entry_search.bind("<KeyRelease>", self._on_search_type)
        self.entry_search.bind("<Return>", self._on_barcode_enter)

        # Quick Return Shortcut Button (Feature U)
        ctk.CTkButton(
            toolbar, text="Quick Return", width=95, height=32,
            font=FONTS["body_sm"], fg_color=COLORS["danger_subtle"],
            text_color=COLORS["danger"], hover_color=COLORS["danger"],
            command=self._open_quick_return
        ).pack(side="right", padx=(0, 10))

        # View Mode Toggle (Grid vs List)
        self.btn_view_mode = ctk.CTkSegmentedButton(
            toolbar, values=["Grid", "List"], command=self._toggle_view_mode,
            height=30, font=FONTS["body_sm"]
        )
        self.btn_view_mode.set("Grid")
        self.btn_view_mode.pack(side="right", padx=(0, 8))

        # Horizontal Category Pills Bar
        self.pills_bar = ctk.CTkScrollableFrame(self.center_panel, height=44, fg_color="transparent", orientation="horizontal")
        self.pills_bar.pack(fill="x", pady=(0, 8))

        # Favorites Bar (Feature M)
        self.fav_container = ctk.CTkFrame(self.center_panel, fg_color=COLORS["bg_surface"], corner_radius=RADII["card"], height=48)
        self.fav_container.pack(fill="x", pady=(0, 8))
        self.fav_container.pack_propagate(False)

        fav_label_box = ctk.CTkFrame(self.fav_container, fg_color="transparent")
        fav_label_box.pack(side="left", padx=(10, 6))
        ctk.CTkLabel(fav_label_box, text="Favorites:", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack()

        self.fav_scroll = ctk.CTkScrollableFrame(self.fav_container, fg_color="transparent", orientation="horizontal")
        self.fav_scroll.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Customer Display / Status Message Bar (Feature O)
        self.display_bar = ctk.CTkFrame(self.center_panel, fg_color=COLORS["primary_subtle"], corner_radius=RADII["badge"], height=32)
        self.display_bar.pack(fill="x", pady=(0, 8))
        self.display_bar.pack_propagate(False)

        self.lbl_customer_display = ctk.CTkLabel(
            self.display_bar, text="Customer Display: Ready for transaction",
            font=FONTS["body_sm"], text_color=COLORS["primary"]
        )
        self.lbl_customer_display.pack(side="left", padx=12)

        # Product Scrollable Grid / List
        self.products_scroll = ctk.CTkScrollableFrame(self.center_panel, fg_color="transparent")
        self.products_scroll.pack(fill="both", expand=True)

    def _build_cart_panel(self):
        # Top Header: Order #, Customer selector, Clear (F1)
        top_row = ctk.CTkFrame(self.cart_panel, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(top_row, text="Order", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left")

        ctk.CTkButton(
            top_row, text="Clear (F1)", width=65, height=28,
            fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
            hover_color=COLORS["danger"], font=FONTS["body_sm"],
            command=self._on_clear_cart
        ).pack(side="right")

        # Customer dropdown
        cust_row = ctk.CTkFrame(self.cart_panel, fg_color="transparent")
        cust_row.pack(fill="x", padx=12, pady=(2, 6))

        self.opt_customer = ctk.CTkOptionMenu(
            cust_row, values=["Walk-in Customer"],
            command=self._on_customer_change, height=32, font=FONTS["body_sm"]
        )
        self.opt_customer.pack(fill="x")

        # Customer Loyalty Points Indicator & Redeem Button (Feature R)
        self.loyalty_bar = ctk.CTkFrame(self.cart_panel, fg_color=COLORS["primary_subtle"], corner_radius=RADII["badge"], height=28)
        self.lbl_cust_loyalty = ctk.CTkLabel(self.loyalty_bar, text="Loyalty: 0 pts", font=FONTS["body_sm"], text_color=COLORS["primary"])
        self.lbl_cust_loyalty.pack(side="left", padx=8)

        self.btn_redeem_pts = ctk.CTkButton(
            self.loyalty_bar, text="Redeem Pts", width=75, height=22,
            font=FONTS["body_sm"], fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            command=self._prompt_redeem_points
        )
        self.btn_redeem_pts.pack(side="right", padx=6)

        # Cart Table Column Header
        cart_th = ctk.CTkFrame(self.cart_panel, fg_color=COLORS["bg_input"], corner_radius=RADII["badge"], height=28)
        cart_th.pack(fill="x", padx=12, pady=(4, 4))
        cart_th.pack_propagate(False)

        ctk.CTkLabel(cart_th, text="Item", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=130, anchor="w").pack(side="left", padx=(8, 0))
        ctk.CTkLabel(cart_th, text="Qty", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=60).pack(side="left")
        ctk.CTkLabel(cart_th, text="Total", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=80, anchor="e").pack(side="right", padx=8)

        # Scrollable Cart Items
        self.cart_scroll = ctk.CTkScrollableFrame(self.cart_panel, fg_color=COLORS["bg_input"], corner_radius=RADII["card"])
        self.cart_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # Cart Summary Box
        sum_box = ctk.CTkFrame(self.cart_panel, fg_color=COLORS["bg_card"], corner_radius=RADII["card"])
        sum_box.pack(fill="x", padx=12, pady=(0, 6))

        self.lbl_subtotal = self._create_sum_row(sum_box, "Subtotal", f"{self.currency} 0.00")
        
        # Discount row with clickable button
        d_row = ctk.CTkFrame(sum_box, fg_color="transparent")
        d_row.pack(fill="x", padx=10, pady=1)
        ctk.CTkButton(
            d_row, text="Discount", font=FONTS["body_sm"],
            fg_color="transparent", text_color=COLORS["primary"],
            hover_color=COLORS["bg_card_hover"], width=55, height=20,
            command=self._prompt_discount
        ).pack(side="left")
        self.lbl_discount = ctk.CTkLabel(d_row, text=f"-{self.currency} 0.00", font=FONTS["mono"], text_color=COLORS["text_secondary"])
        self.lbl_discount.pack(side="right")

        self.lbl_tax = self._create_sum_row(sum_box, "Tax", f"{self.currency} 0.00")

        # Grand Total
        ctk.CTkFrame(sum_box, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=3)
        gt_row = ctk.CTkFrame(sum_box, fg_color="transparent")
        gt_row.pack(fill="x", padx=10, pady=(2, 6))

        ctk.CTkLabel(gt_row, text="Total", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        self.lbl_grand_total = ctk.CTkLabel(gt_row, text=f"{self.currency} 0.00", font=FONTS["grand_total"], text_color=COLORS["primary"])
        self.lbl_grand_total.pack(side="right")

        # Action Buttons (Hold, Recall)
        act_row = ctk.CTkFrame(self.cart_panel, fg_color="transparent")
        act_row.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkButton(
            act_row, text="Hold (F3)", height=34, font=FONTS["body_sm"],
            fg_color=COLORS["warning_subtle"], text_color=COLORS["warning"],
            hover_color=COLORS["warning"], command=self._on_hold_order
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            act_row, text="Recall (F4)", height=34, font=FONTS["body_sm"],
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"],
            command=self._on_recall_order
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Big Main Charge Button (52px height, indigo-600 bg, full width)
        self.btn_charge = ctk.CTkButton(
            self.cart_panel, text=f"Charge {self.currency} 0.00 (F5)",
            height=52, font=FONTS["mono_lg"], fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            corner_radius=RADII["button"], command=self._on_checkout
        )
        self.btn_charge.pack(fill="x", padx=12, pady=(0, 12))

    def _create_sum_row(self, parent, label: str, val: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=1)
        ctk.CTkLabel(row, text=label, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(side="left")
        lbl = ctk.CTkLabel(row, text=val, font=FONTS["mono"], text_color=COLORS["text_secondary"])
        lbl.pack(side="right")
        return lbl

    def _load_categories(self):
        for w in self.pills_bar.winfo_children():
            w.destroy()

        categories = CategoryModel.list_all(active_only=True)

        def _make_pill(title, cat_id):
            is_active = self.active_category_id == cat_id
            bg_col = COLORS["primary_subtle"] if is_active else COLORS["bg_surface"]
            txt_col = COLORS["primary"] if is_active else COLORS["text_secondary"]
            b_width = 1 if is_active else 1
            b_color = COLORS["primary"] if is_active else COLORS["border"]

            btn = ctk.CTkButton(
                self.pills_bar, text=title, font=FONTS["body_sm"],
                height=30, corner_radius=RADII["pill"],
                fg_color=bg_col, text_color=txt_col,
                border_width=b_width, border_color=b_color,
                hover_color=COLORS["primary_subtle"],
                command=lambda cid=cat_id: self._select_category(cid)
            )
            btn.pack(side="left", padx=3)

        _make_pill("All Items", None)
        for cat in categories:
            _make_pill(cat["name"], cat["id"])

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
            self.loyalty_bar.pack_forget()
        else:
            idx = self.opt_customer.cget("values").index(choice) - 1
            if 0 <= idx < len(self.all_customers):
                cust = self.all_customers[idx]
                self.controller.set_customer(cust)
                pts = float(cust.get("loyalty_points", 0))
                self.lbl_cust_loyalty.configure(text=f"Loyalty: {pts:g} pts")
                self.loyalty_bar.pack(fill="x", padx=12, pady=(0, 4), after=self.opt_customer.master)

    def _prompt_redeem_points(self):
        cust = self.controller.selected_customer
        if not cust:
            return
        pts = float(cust.get("loyalty_points", 0))
        if pts <= 0:
            return
        dialog = ctk.CTkInputDialog(text=f"Available Points: {pts:g}\nEnter points to redeem (1 pt = {self.currency} 1 discount):", title="Redeem Loyalty Points")
        val_str = dialog.get_input()
        if val_str:
            try:
                p_num = float(val_str)
                ok, msg = self.controller.redeem_loyalty_points(p_num)
                if ok:
                    self._refresh_cart()
            except ValueError:
                pass

    def _refresh_favorites(self):
        for w in self.fav_scroll.winfo_children():
            w.destroy()

        favs = ProductModel.get_favorites(limit=12)
        if not favs:
            ctk.CTkLabel(self.fav_scroll, text="No favorites pinned yet. Right-click or star products in catalog.", font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(side="left", padx=5)
            return

        for f in favs:
            price = float(f["selling_price"])
            btn = ctk.CTkButton(
                self.fav_scroll, text=f"★ {f['name'][:16]} ({self.currency} {price:g})",
                font=FONTS["body_sm"], height=28, corner_radius=RADII["badge"],
                fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"],
                hover_color=COLORS["primary_subtle"],
                command=lambda p=f: self._add_to_cart(p)
            )
            btn.pack(side="left", padx=3)

    def _on_search_type(self, event=None):
        self._refresh_products()

    def _on_barcode_enter(self, event=None):
        code = self.entry_search.get().strip()
        if not code:
            return

        prod = ProductModel.get_by_barcode_or_sku(code)
        if prod:
            self.controller.add_product(prod, 1.0)
            play_beep("beep")
            self._update_customer_display(prod["name"], float(prod["selling_price"]))
            self.entry_search.delete(0, "end")
            self._refresh_cart()
            self._refresh_products()
        else:
            # Barcode not found -> Trigger Quick-Add Dialog (Feature L)
            self._open_quick_add(code)

    def _open_quick_add(self, barcode: str):
        QuickAddProductDialog(self, barcode=barcode, on_product_added=self._on_quick_added)

    def _on_quick_added(self, product: dict):
        self.entry_search.delete(0, "end")
        self._add_to_cart(product)
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
                self.products_scroll, text="No products found.\nTry a different search term or scan a new barcode.",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"], justify="center"
            ).pack(pady=40)
            return

        if self.view_mode == "grid":
            grid_frame = ctk.CTkFrame(self.products_scroll, fg_color="transparent")
            grid_frame.pack(fill="both", expand=True)

            cols = 4 # 4 columns commercial layout
            for i in range(cols):
                grid_frame.columnconfigure(i, weight=1, uniform="col")

            for idx, prod in enumerate(products):
                r = idx // cols
                c = idx % cols
                self._render_product_card(grid_frame, prod, r, c)
        else:
            for prod in products:
                self._render_product_row(self.products_scroll, prod)

    def _render_product_card(self, parent, prod, row, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=RADII["card"], border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        # Top indicator bar: Category tag + Stock badge
        stock = float(prod.get("current_stock", 0))
        min_s = float(prod.get("min_stock", 5))
        stock_color = COLORS["danger"] if stock <= min_s else COLORS["text_secondary"]
        stock_text = f"{stock:g} {prod.get('unit', 'pc')}"

        top_info = ctk.CTkFrame(card, fg_color="transparent")
        top_info.pack(fill="x", padx=8, pady=(8, 2))

        cat_tag = prod.get("category_name") or "General"
        ctk.CTkLabel(top_info, text=cat_tag[:12], font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(top_info, text=stock_text, font=FONTS["body_sm"], text_color=stock_color).pack(side="right")

        # Product Name (Sentence case, no decorative emojis)
        name_lbl = ctk.CTkLabel(
            card, text=prod["name"], font=FONTS["body_md"],
            text_color=COLORS["text_primary"], anchor="w", justify="left",
            wraplength=140
        )
        name_lbl.pack(fill="x", padx=8, pady=(2, 6))

        # Price and Add action
        bot = ctk.CTkFrame(card, fg_color="transparent")
        bot.pack(fill="x", padx=8, pady=(2, 8))

        price = float(prod["selling_price"])
        ctk.CTkLabel(
            bot, text=f"{self.currency} {price:,.2f}",
            font=FONTS["mono_bold"], text_color=COLORS["primary"]
        ).pack(side="left")

        # Star toggle for favorite (Feature M)
        is_fav = prod.get("is_favorite") == 1
        btn_fav = ctk.CTkButton(
            bot, text="★" if is_fav else "☆", width=24, height=24,
            font=FONTS["body_md"], fg_color="transparent",
            text_color=COLORS["gold"] if is_fav else COLORS["text_muted"],
            hover_color=COLORS["bg_card_hover"],
            command=lambda p=prod: self._toggle_favorite(p)
        )
        btn_fav.pack(side="right", padx=(2, 0))

        btn_add = ctk.CTkButton(
            bot, text="+", width=32, height=26,
            font=FONTS["body_md"], fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            corner_radius=RADII["button"], command=lambda p=prod: self._add_to_cart(p)
        )
        btn_add.pack(side="right")

        # Clicking whole card adds to cart
        card.bind("<Button-1>", lambda e, p=prod: self._add_to_cart(p))
        name_lbl.bind("<Button-1>", lambda e, p=prod: self._add_to_cart(p))

    def _render_product_row(self, parent, prod):
        row = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=RADII["button"], height=40)
        row.pack(fill="x", pady=2, padx=2)

        name = prod["name"]
        cat = prod.get("category_name") or "General"
        price = float(prod["selling_price"])
        stock = prod.get("current_stock", 0)

        ctk.CTkLabel(row, text=name[:26], font=FONTS["body_md"], text_color=COLORS["text_primary"], width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(row, text=cat[:14], font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=f"{stock:g} in stock", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=80).pack(side="left")
        ctk.CTkLabel(row, text=f"{self.currency} {price:,.2f}", font=FONTS["mono_bold"], text_color=COLORS["primary"], width=100, anchor="e").pack(side="left", padx=8)

        ctk.CTkButton(
            row, text="+", width=32, height=26, font=FONTS["body_md"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=lambda p=prod: self._add_to_cart(p)
        ).pack(side="right", padx=8)

    def _toggle_favorite(self, prod):
        ProductModel.toggle_favorite(prod["id"])
        self._refresh_favorites()
        self._refresh_products()

    def _add_to_cart(self, prod):
        self.controller.add_product(prod, 1.0)
        play_beep("beep")
        self._update_customer_display(prod["name"], float(prod["selling_price"]))
        self._refresh_cart()

    def _update_customer_display(self, item_name: str, price: float):
        summary = self.controller.get_summary()
        self.lbl_customer_display.configure(
            text=f"Latest Item: {item_name} ({self.currency} {price:,.2f})  |  Cart Total: {self.currency} {summary['grand_total']:,.2f}"
        )

    def _refresh_cart(self):
        for w in self.cart_scroll.winfo_children():
            w.destroy()

        cart_items = list(self.controller.cart_items.values())

        if not cart_items:
            ctk.CTkLabel(
                self.cart_scroll, text="Cart is empty\nScan barcode or click + to add items",
                font=FONTS["body_sm"], text_color=COLORS["text_muted"], justify="center"
            ).pack(pady=35)
        else:
            for itm in cart_items:
                self._render_cart_item_row(itm)

        summary = self.controller.get_summary()
        self.lbl_subtotal.configure(text=f"{self.currency} {summary['subtotal']:,.2f}")
        self.lbl_discount.configure(text=f"-{self.currency} {summary['discount_amount']:,.2f}")
        self.lbl_tax.configure(text=f"{self.currency} {summary['tax_amount']:,.2f}")
        self.lbl_grand_total.configure(text=f"{self.currency} {summary['grand_total']:,.2f}")
        self.btn_charge.configure(text=f"Charge {self.currency} {summary['grand_total']:,.2f} (F5)")

    def _render_cart_item_row(self, itm):
        pid = itm["product_id"]
        row = ctk.CTkFrame(self.cart_scroll, fg_color=COLORS["bg_card"], corner_radius=RADII["badge"])
        row.pack(fill="x", pady=2, padx=2)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=6, pady=4)

        ctk.CTkLabel(
            info, text=itm["product_name"][:18], font=FONTS["body_md"],
            text_color=COLORS["text_primary"], anchor="w"
        ).pack(anchor="w")

        price_sub = f"{self.currency} {itm['unit_price']:,.2f}"
        if itm.get("price_override"):
            price_sub += " [Override]"
        ctk.CTkLabel(
            info, text=price_sub, font=FONTS["mono"],
            text_color=COLORS["text_secondary"], anchor="w"
        ).pack(anchor="w")

        # Quantity controls
        qty_box = ctk.CTkFrame(row, fg_color="transparent")
        qty_box.pack(side="left", padx=2)

        ctk.CTkButton(
            qty_box, text="−", width=22, height=22, font=FONTS["body_sm"],
            fg_color=COLORS["bg_main"], text_color=COLORS["text_primary"],
            command=lambda p=pid: self._change_qty(p, -1)
        ).pack(side="left")

        ctk.CTkLabel(
            qty_box, text=f"{itm['quantity']:g}", width=28,
            font=FONTS["mono_bold"], text_color=COLORS["text_primary"]
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            qty_box, text="+", width=22, height=22, font=FONTS["body_sm"],
            fg_color=COLORS["bg_main"], text_color=COLORS["text_primary"],
            command=lambda p=pid: self._change_qty(p, 1)
        ).pack(side="left")

        # Total and Override button
        right_box = ctk.CTkFrame(row, fg_color="transparent")
        right_box.pack(side="right", padx=(2, 6))

        ctk.CTkLabel(
            right_box, text=f"{self.currency} {itm['total']:,.2f}",
            font=FONTS["mono_bold"], text_color=COLORS["text_primary"], width=68, anchor="e"
        ).pack(side="left", padx=(0, 2))

        # Price Override Button (Feature N)
        ctk.CTkButton(
            right_box, text="✎", width=20, height=20,
            fg_color="transparent", text_color=COLORS["primary"],
            hover_color=COLORS["primary_subtle"],
            command=lambda item=itm: self._open_price_override(item)
        ).pack(side="left")

        # Remove Item Button
        ctk.CTkButton(
            right_box, text="✕", width=20, height=20,
            fg_color="transparent", text_color=COLORS["danger"],
            hover_color=COLORS["danger_subtle"],
            command=lambda p=pid: self._remove_cart_item(p)
        ).pack(side="left")

    def _open_price_override(self, item):
        PriceOverrideDialog(self, item, on_override=self._apply_price_override)

    def _apply_price_override(self, product_id, new_price, reason):
        self.controller.override_item_price(product_id, new_price, reason)
        self._refresh_cart()

    def _open_quick_return(self):
        QuickReturnDialog(self, on_returned=self._refresh_products)

    def _change_qty(self, pid, delta):
        self.controller.change_quantity(pid, delta)
        self._refresh_cart()

    def _remove_cart_item(self, pid):
        self.controller.remove_item(pid)
        self._refresh_cart()

    def _on_clear_cart(self):
        self.controller.clear_cart()
        self._refresh_cart()
        self.lbl_customer_display.configure(text="Customer Display: Cart reset")

    def _prompt_discount(self):
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
            self.lbl_customer_display.configure(text="Customer Display: Order placed on hold")

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
            self.lbl_customer_display.configure(text=f"Sale Complete! Thank you for shopping.")

            auto_print = SettingsModel.get("auto_print", "0") == "1"
            if auto_print:
                ReceiptPrinter.print_receipt(order_details)
            else:
                ReceiptPreviewDialog(self, order_details)

    def focus_search(self):
        self.entry_search.focus_set()
        self.entry_search.select_range(0, "end")
