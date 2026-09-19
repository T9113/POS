from datetime import datetime
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.expense_model import ExpenseModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController

class ExpensesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Total Expenses KPI Banner
        total_exp = ExpenseModel.get_total_expenses()
        kpi_card = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10, height=75)
        kpi_card.pack(fill="x", pady=(0, 10))
        kpi_card.pack_propagate(False)

        ctk.CTkLabel(kpi_card, text="TOTAL OPERATING EXPENSES", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=20, pady=(12, 2))
        self.lbl_kpi = ctk.CTkLabel(kpi_card, text=f"{self.currency} {total_exp:,.2f}", font=FONTS["stat_value"], text_color=COLORS["warning"])
        self.lbl_kpi.pack(anchor="w", padx=20, pady=(0, 12))

        # 2. Add Expense Card + Filter Toolbar
        mid_box = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10)
        mid_box.pack(fill="x", pady=(0, 10))

        add_hdr = ctk.CTkFrame(mid_box, fg_color="transparent")
        add_hdr.pack(fill="x", padx=15, pady=(12, 6))
        ctk.CTkLabel(add_hdr, text="➕ Record Shop Expense", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left")

        input_row = ctk.CTkFrame(mid_box, fg_color="transparent")
        input_row.pack(fill="x", padx=15, pady=(0, 12))

        # Category
        self.opt_cat = ctk.CTkOptionMenu(input_row, values=ExpenseModel.CATEGORIES, height=36, font=FONTS["body_md"], width=180)
        self.opt_cat.pack(side="left", padx=(0, 6))

        # Amount
        self.entry_amount = ctk.CTkEntry(input_row, placeholder_text=f"Amount ({self.currency})", height=36, width=130, font=FONTS["body_md"])
        self.entry_amount.pack(side="left", padx=4)

        # Description
        self.entry_desc = ctk.CTkEntry(input_row, placeholder_text="Description / Notes...", height=36, font=FONTS["body_md"])
        self.entry_desc.pack(side="left", fill="x", expand=True, padx=4)

        # Add Button
        ctk.CTkButton(
            input_row, text="Add Expense", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=36, text_color="#FFFFFF", command=self._add_expense
        ).pack(side="left", padx=(6, 0))

        # 3. Expenses Table
        table_card = ctk.CTkFrame(container, fg_color=COLORS["bg_surface"], corner_radius=10)
        table_card.pack(fill="both", expand=True)

        th = ctk.CTkFrame(table_card, fg_color=COLORS["bg_input"], corner_radius=6, height=36)
        th.pack(fill="x", padx=10, pady=(10, 4))
        th.pack_propagate(False)

        ctk.CTkLabel(th, text="Date", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=110, anchor="w").pack(side="left", padx=(12, 5))
        ctk.CTkLabel(th, text="Category", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=160, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(th, text="Description", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=260, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(th, text="Recorded By", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=120, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(th, text="Amount", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=120, anchor="e").pack(side="right", padx=15)

        self.expenses_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.expenses_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 10))

    def _add_expense(self):
        amt_str = self.entry_amount.get().strip()
        desc = self.entry_desc.get().strip()
        cat = self.opt_cat.get()

        if not amt_str:
            return

        try:
            amt = float(amt_str)
            if amt <= 0:
                return
        except ValueError:
            return

        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1
        today = datetime.now().strftime("%Y-%m-%d")

        ExpenseModel.create(cat, amt, desc, today, user_id)

        self.entry_amount.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self._refresh_list()

    def _refresh_list(self):
        for w in self.expenses_scroll.winfo_children():
            w.destroy()

        expenses = ExpenseModel.list_all(limit=100)
        total_exp = ExpenseModel.get_total_expenses()
        self.lbl_kpi.configure(text=f"{self.currency} {total_exp:,.2f}")

        if not expenses:
            ctk.CTkLabel(self.expenses_scroll, text="No expenses recorded yet.", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for e in expenses:
            row = ctk.CTkFrame(self.expenses_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=e["date"], font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=110, anchor="w").pack(side="left", padx=(12, 5), pady=8)
            ctk.CTkLabel(row, text=e["category"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=160, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=e.get("description") or "-", font=FONTS["body_md"], text_color=COLORS["text_secondary"], width=260, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=e.get("user_name") or "Admin", font=FONTS["body_sm"], text_color=COLORS["text_muted"], width=120, anchor="w").pack(side="left", padx=5)

            amt = float(e["amount"])
            ctk.CTkLabel(row, text=f"{self.currency} {amt:,.2f}", font=FONTS["title_sm"], text_color=COLORS["warning"], width=120, anchor="e").pack(side="right", padx=15)

            ctk.CTkButton(
                row, text="✕", width=26, height=26,
                fg_color=COLORS["danger_subtle"], text_color=COLORS["danger"],
                command=lambda eid=e["id"]: self._delete_expense(eid)
            ).pack(side="right", padx=(0, 5))

    def _delete_expense(self, eid):
        ExpenseModel.delete(eid)
        self._refresh_list()
