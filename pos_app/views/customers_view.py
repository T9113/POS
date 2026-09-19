import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.customer_model import CustomerModel
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.exporter import Exporter

class CustomersView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.selected_customer = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # Top Bar
        top_bar = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10, height=54)
        top_bar.pack(fill="x", pady=(0, 10))
        top_bar.pack_propagate(False)

        ctk.CTkLabel(top_bar, text="🔍", font=("Segoe UI", 13)).pack(side="left", padx=(14, 4))
        self.entry_search = ctk.CTkEntry(
            top_bar, placeholder_text="Search Customers (Name, Phone)...",
            height=36, font=FONTS["body_md"], width=280
        )
        self.entry_search.pack(side="left", padx=(0, 10), pady=9)
        self.entry_search.bind("<KeyRelease>", lambda e: self._refresh_list())

        ctk.CTkButton(
            top_bar, text="➕ Add Customer", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=36, text_color="#FFFFFF", command=self._add_customer_dialog
        ).pack(side="right", padx=14)

        # Split View: Left = Customer List, Right = Customer Details & History
        split_box = ctk.CTkFrame(container, fg_color="transparent")
        split_box.pack(fill="both", expand=True)

        # Left Column: Customer List
        self.list_panel = ctk.CTkFrame(split_box, width=380, fg_color=COLORS["bg_surface"], corner_radius=10)
        self.list_panel.pack(side="left", fill="both", padx=(0, 10))
        self.list_panel.pack_propagate(False)

        ctk.CTkLabel(self.list_panel, text="CUSTOMER DIRECTORY", font=FONTS["title_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(12, 6))
        self.customers_scroll = ctk.CTkScrollableFrame(self.list_panel, fg_color="transparent")
        self.customers_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # Right Column: Detail & Purchase History
        self.detail_panel = ctk.CTkFrame(split_box, fg_color=COLORS["bg_surface"], corner_radius=10)
        self.detail_panel.pack(side="left", fill="both", expand=True)
        self._render_empty_detail()

    def _render_empty_detail(self):
        for w in self.detail_panel.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.detail_panel, text="👈 Select a customer from the left directory\nto view their profile and purchase history.",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"], justify="center"
        ).pack(expand=True)

    def _refresh_list(self):
        for w in self.customers_scroll.winfo_children():
            w.destroy()

        query = self.entry_search.get().strip()
        customers = CustomerModel.list_all(search_query=query, limit=100)

        if not customers:
            ctk.CTkLabel(self.customers_scroll, text="No customers found.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for c in customers:
            card = ctk.CTkFrame(self.customers_scroll, fg_color=COLORS["bg_card"], corner_radius=8)
            card.pack(fill="x", pady=3, padx=2)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            ctk.CTkLabel(info, text=c["name"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=c.get("phone") or "No phone", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], anchor="w").pack(anchor="w")

            bal = float(c.get("balance", 0))
            if bal > 0:
                ctk.CTkLabel(
                    card, text=f"Due: {self.currency} {bal:,.2f}",
                    font=FONTS["title_sm"], text_color=COLORS["warning"]
                ).pack(side="right", padx=10)

            # Click handler to select
            card.bind("<Button-1>", lambda e, cust=c: self._select_customer(cust))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, cust=c: self._select_customer(cust))
                for gchild in child.winfo_children():
                    gchild.bind("<Button-1>", lambda e, cust=c: self._select_customer(cust))

    def _select_customer(self, cust):
        self.selected_customer = cust
        self._render_customer_detail(cust)

    def _render_customer_detail(self, cust):
        for w in self.detail_panel.winfo_children():
            w.destroy()

        # Customer Header Box
        hdr = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(15, 10))

        info_box = ctk.CTkFrame(hdr, fg_color="transparent")
        info_box.pack(side="left")

        ctk.CTkLabel(info_box, text=cust["name"], font=FONTS["title_lg"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(
            info_box,
            text=f"📞 {cust.get('phone') or 'N/A'}  •  ✉️ {cust.get('email') or 'N/A'}  •  📍 {cust.get('address') or 'N/A'}",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Balance Due Banner
        bal = float(cust.get("balance", 0))
        bal_box = ctk.CTkFrame(hdr, fg_color=COLORS["warning_subtle"] if bal > 0 else COLORS["success_subtle"], corner_radius=8)
        bal_box.pack(side="right", padx=10)
        ctk.CTkLabel(
            bal_box, text=f"Account Balance / Due: {self.currency} {bal:,.2f}",
            font=FONTS["title_sm"], text_color=COLORS["warning"] if bal > 0 else COLORS["success"]
        ).pack(padx=14, pady=8)

        # Action Buttons
        btn_bar = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="💵 Receive Payment / Clear Due", font=FONTS["body_sm"],
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            command=lambda: self._receive_customer_payment(cust)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_bar, text="📄 Export Statement (PDF)", font=FONTS["body_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=lambda: self._export_statement(cust)
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_bar, text="🗑️ Delete", font=FONTS["body_sm"],
            fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
            command=lambda: self._delete_customer(cust)
        ).pack(side="right")

        # Purchase History Header
        ctk.CTkLabel(
            self.detail_panel, text="Order Purchase History",
            font=FONTS["title_sm"], text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=20, pady=(10, 4))

        # Scrollable Orders
        history_scroll = ctk.CTkScrollableFrame(self.detail_panel, fg_color=COLORS["bg_input"], corner_radius=8)
        history_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        orders = CustomerModel.get_purchase_history(cust["id"])
        if not orders:
            ctk.CTkLabel(history_scroll, text="No purchases recorded for this customer.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for o in orders:
            row = ctk.CTkFrame(history_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=o["order_number"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=160, anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(row, text=o["created_at"], font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"Method: {o['payment_method'].capitalize()}", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{self.currency} {o['total']:,.2f}", font=FONTS["title_sm"], text_color=COLORS["primary"], width=110, anchor="e").pack(side="right", padx=15)

    def _add_customer_dialog(self):
        name_dlg = ctk.CTkInputDialog(text="Enter Customer Full Name:", title="Add Customer")
        name = name_dlg.get_input()
        if not name or not name.strip():
            return
        phone_dlg = ctk.CTkInputDialog(text=f"Enter phone number for {name}:", title="Customer Phone")
        phone = phone_dlg.get_input() or ""
        CustomerModel.create(name.strip(), phone.strip())
        self._refresh_list()

    def _receive_customer_payment(self, cust):
        bal = float(cust.get("balance", 0))
        dialog = ctk.CTkInputDialog(text=f"Current Due: {self.currency} {bal:,.2f}\nEnter payment amount to deduct from balance:", title="Receive Payment")
        val = dialog.get_input()
        if val:
            try:
                amt = float(val)
                CustomerModel.adjust_balance(cust["id"], -amt)
                cust["balance"] = max(0.0, bal - amt)
                self._select_customer(cust)
                self._refresh_list()
            except ValueError:
                pass

    def _delete_customer(self, cust):
        CustomerModel.delete(cust["id"])
        self._render_empty_detail()
        self._refresh_list()

    def _export_statement(self, cust):
        orders = CustomerModel.get_purchase_history(cust["id"])
        headers = ["Order #", "Date", "Payment Mode", "Status", "Amount Paid", "Total"]
        rows = [
            [o["order_number"], o["created_at"], o["payment_method"], o["status"], f"{self.currency} {o['amount_paid']:,.2f}", f"{self.currency} {o['total']:,.2f}"]
            for o in orders
        ]
        filename = f"statement_{cust['name'].replace(' ', '_')}.pdf"
        summary = [
            ("Customer Name", cust["name"]),
            ("Phone", cust.get("phone") or "N/A"),
            ("Outstanding Balance", f"{self.currency} {cust.get('balance', 0):,.2f}")
        ]
        path = Exporter.export_pdf(filename, f"Account Statement: {cust['name']}", headers, rows, summary)
        ctk.CTkInputDialog(text=f"Customer statement exported to:\n{path}", title="Statement Exported")
