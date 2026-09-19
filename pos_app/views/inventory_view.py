import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.inventory_model import InventoryModel
from pos_app.models.purchase_model import PurchaseModel
from pos_app.models.supplier_model import SupplierModel
from pos_app.models.product_model import ProductModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.purchase_order_dialog import PurchaseOrderDialog

class InventoryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Valuation & Stock Health KPIs Row
        val = ProductModel.get_stock_valuation()
        low_count = ProductModel.get_low_stock_count()

        kpi_row = ctk.CTkFrame(container, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 15))

        self._create_kpi_card(
            kpi_row, "INVENTORY VALUE (COST)",
            f"{self.currency} {val.get('total_cost_value', 0):,.2f}",
            f"{val.get('total_items', 0)} Products ({val.get('total_units', 0):,g} units in stock)",
            COLORS["primary"]
        )

        self._create_kpi_card(
            kpi_row, "RETAIL VALUE (SELLING)",
            f"{self.currency} {val.get('total_retail_value', 0):,.2f}",
            "Expected gross sales from current stock",
            COLORS["success"]
        )

        low_col = COLORS["danger"] if low_count > 0 else COLORS["success"]
        self._create_kpi_card(
            kpi_row, "ITEMS NEEDING REORDER",
            f"{low_count} Products",
            "Products at or below minimum stock level",
            low_col
        )

        # 2. Main Tabs (Stock-In Purchases, Adjustments Log, Suppliers Directory)
        self.tabs = ctk.CTkTabview(container, fg_color=COLORS["bg_surface"])
        self.tabs.pack(fill="both", expand=True)

        self.tab_purchases = self.tabs.add("📦 Purchases / Stock-In")
        self.tab_adjustments = self.tabs.add("📋 Stock Adjustments Log")
        self.tab_suppliers = self.tabs.add("🏭 Suppliers Directory")

        self._build_purchases_tab()
        self._build_adjustments_tab()
        self._build_suppliers_tab()

    def _create_kpi_card(self, parent, title, val_str, sub_str, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_surface"], corner_radius=10)
        card.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(card, text=title, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(12, 2))
        ctk.CTkLabel(card, text=val_str, font=FONTS["stat_value"], text_color=color).pack(anchor="w", padx=15, pady=(0, 2))
        ctk.CTkLabel(card, text=sub_str, font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(0, 12))

    # --- Purchases Tab ---
    def _build_purchases_tab(self):
        top = ctk.CTkFrame(self.tab_purchases, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 10))

        ctk.CTkLabel(top, text="Stock-In Purchase History", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            top, text="➕ Receive Purchase / Stock-In", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=36, command=self._open_new_purchase
        ).pack(side="right")

        self.purchases_scroll = ctk.CTkScrollableFrame(self.tab_purchases, fg_color=COLORS["bg_input"], corner_radius=8)
        self.purchases_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._refresh_purchases()

    def _open_new_purchase(self):
        PurchaseOrderDialog(self, on_complete=self._refresh_purchases)

    def _refresh_purchases(self):
        for w in self.purchases_scroll.winfo_children():
            w.destroy()

        purchases = PurchaseModel.list_purchases(limit=50)
        if not purchases:
            ctk.CTkLabel(self.purchases_scroll, text="No purchase orders recorded yet.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for p in purchases:
            row = ctk.CTkFrame(self.purchases_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            sup = p.get("supplier_name") or "Direct Stock In"
            ctk.CTkLabel(row, text=f"PO #{p['id']:04d}  •  {sup}", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=240, anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=p.get("created_at", ""), font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=150, anchor="w").pack(side="left", padx=5)
            
            note_str = p.get("note") or ""
            ctk.CTkLabel(row, text=note_str[:30], font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=160, anchor="w").pack(side="left", padx=5)
            
            ctk.CTkLabel(row, text=f"{self.currency} {p['total_amount']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["success"], width=120, anchor="e").pack(side="right", padx=15)

    # --- Adjustments Tab ---
    def _build_adjustments_tab(self):
        top = ctk.CTkFrame(self.tab_adjustments, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 10))

        ctk.CTkLabel(top, text="Stock Adjustment Audit Trail", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left")

        self.adjust_scroll = ctk.CTkScrollableFrame(self.tab_adjustments, fg_color=COLORS["bg_input"], corner_radius=8)
        self.adjust_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._refresh_adjustments()

    def _refresh_adjustments(self):
        for w in self.adjust_scroll.winfo_children():
            w.destroy()

        adjustments = InventoryModel.list_adjustments(limit=60)
        if not adjustments:
            ctk.CTkLabel(self.adjust_scroll, text="No stock adjustments recorded.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for a in adjustments:
            row = ctk.CTkFrame(self.adjust_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            name = a.get("product_name", "Item")
            ctk.CTkLabel(row, text=name[:26], font=FONTS["body_md"], text_color=COLORS["text_primary"], width=220, anchor="w").pack(side="left", padx=10, pady=8)

            delta = float(a.get("quantity_change", 0))
            d_color = COLORS["success"] if delta > 0 else COLORS["danger"]
            ctk.CTkLabel(row, text=f"{delta:+g}", font=FONTS["title_sm"], text_color=d_color, width=70).pack(side="left", padx=5)

            ctk.CTkLabel(row, text=a.get("reason", ""), font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=130, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=a.get("created_at", ""), font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=140, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"User: {a.get('user_name', 'Admin')}", font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=120, anchor="e").pack(side="right", padx=10)

    # --- Suppliers Tab ---
    def _build_suppliers_tab(self):
        top = ctk.CTkFrame(self.tab_suppliers, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 10))

        ctk.CTkLabel(top, text="Supplier Vendors List", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            top, text="➕ Add Supplier", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=36, command=self._add_supplier
        ).pack(side="right")

        self.suppliers_scroll = ctk.CTkScrollableFrame(self.tab_suppliers, fg_color=COLORS["bg_input"], corner_radius=8)
        self.suppliers_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._refresh_suppliers()

    def _refresh_suppliers(self):
        for w in self.suppliers_scroll.winfo_children():
            w.destroy()

        suppliers = SupplierModel.list_all(limit=100)
        if not suppliers:
            ctk.CTkLabel(self.suppliers_scroll, text="No suppliers registered.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for s in suppliers:
            row = ctk.CTkFrame(self.suppliers_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=s["name"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=200, anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(row, text=s.get("phone") or "No phone", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=140, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=s.get("address") or "", font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=200, anchor="w").pack(side="left", padx=5)

            ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
                command=lambda sid=s["id"]: self._delete_supplier(sid)
            ).pack(side="right", padx=10)

    def _add_supplier(self):
        dialog = ctk.CTkInputDialog(text="Enter Supplier Name:", title="Add Supplier")
        name = dialog.get_input()
        if name and name.strip():
            phone_dlg = ctk.CTkInputDialog(text=f"Enter phone number for {name.strip()}:", title="Supplier Phone")
            phone = phone_dlg.get_input() or ""
            SupplierModel.create(name.strip(), phone.strip())
            self._refresh_suppliers()

    def _delete_supplier(self, sid):
        SupplierModel.delete(sid)
        self._refresh_suppliers()
