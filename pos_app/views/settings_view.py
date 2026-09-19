import tkinter.filedialog as fd
import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS, apply_theme
from pos_app.models.settings_model import SettingsModel
from pos_app.models.user_model import UserModel
from pos_app.controllers.settings_controller import SettingsController
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.receipt_printer import ReceiptPrinter
from pos_app.utils.i18n import set_language

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, on_theme_change=None):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.on_theme_change = on_theme_change
        self.settings = SettingsModel.get_all()
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # Tabs: Business Profile, Taxes & Currency, Receipt & Printer, Users, Backup & Reset
        self.tabs = ctk.CTkTabview(container, fg_color=COLORS["bg_surface"])
        self.tabs.pack(fill="both", expand=True)

        self.tab_biz = self.tabs.add("🏢 Business Profile")
        self.tab_tax = self.tabs.add("💰 Taxes & Currency")
        self.tab_print = self.tabs.add("🖨️ Receipt & Printer")
        self.tab_users = self.tabs.add("👥 User Roles")
        self.tab_data = self.tabs.add("💾 Backup & Reset")

        self._build_biz_tab()
        self._build_tax_tab()
        self._build_print_tab()
        self._build_users_tab()
        self._build_data_tab()

    # --- 1. Business Profile Tab ---
    def _build_biz_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_biz, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(scroll, text="Store Identity & Contact Details", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 15))

        # Store Name
        ctk.CTkLabel(scroll, text="Business Name *", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_biz_name = ctk.CTkEntry(scroll, height=38, font=FONTS["body_lg"])
        self.entry_biz_name.pack(fill="x", pady=(2, 10))
        self.entry_biz_name.insert(0, self.settings.get("business_name", ""))

        # Address
        ctk.CTkLabel(scroll, text="Store Address", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_biz_addr = ctk.CTkEntry(scroll, height=38, font=FONTS["body_lg"])
        self.entry_biz_addr.pack(fill="x", pady=(2, 10))
        self.entry_biz_addr.insert(0, self.settings.get("business_address", ""))

        # Phone and Email (Row)
        pe_row = ctk.CTkFrame(scroll, fg_color="transparent")
        pe_row.pack(fill="x", pady=(0, 10))

        p_col = ctk.CTkFrame(pe_row, fg_color="transparent")
        p_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(p_col, text="Phone Number", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_biz_phone = ctk.CTkEntry(p_col, height=38)
        self.entry_biz_phone.pack(fill="x", pady=(2, 0))
        self.entry_biz_phone.insert(0, self.settings.get("business_phone", ""))

        e_col = ctk.CTkFrame(pe_row, fg_color="transparent")
        e_col.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(e_col, text="Email Address", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_biz_email = ctk.CTkEntry(e_col, height=38)
        self.entry_biz_email.pack(fill="x", pady=(2, 0))
        self.entry_biz_email.insert(0, self.settings.get("business_email", ""))

        # Tax Registration Number
        ctk.CTkLabel(scroll, text="Tax / NTN Registration Number", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_biz_tax_num = ctk.CTkEntry(scroll, height=38)
        self.entry_biz_tax_num.pack(fill="x", pady=(2, 20))
        self.entry_biz_tax_num.insert(0, self.settings.get("tax_number", ""))

        # Save Button
        ctk.CTkButton(
            scroll, text="Save Business Profile", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=42, text_color="#FFFFFF", command=self._save_biz_profile
        ).pack(anchor="w")

    def _save_biz_profile(self):
        updates = {
            "business_name": self.entry_biz_name.get().strip(),
            "business_address": self.entry_biz_addr.get().strip(),
            "business_phone": self.entry_biz_phone.get().strip(),
            "business_email": self.entry_biz_email.get().strip(),
            "tax_number": self.entry_biz_tax_num.get().strip()
        }
        SettingsController.save_settings(updates)
        ctk.CTkInputDialog(text="Business profile settings updated.", title="Settings Saved")

    # --- 2. Taxes & Currency Tab ---
    def _build_tax_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_tax, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(scroll, text="Currency Configuration", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 10))

        curr_row = ctk.CTkFrame(scroll, fg_color="transparent")
        curr_row.pack(fill="x", pady=(0, 15))

        c1 = ctk.CTkFrame(curr_row, fg_color="transparent")
        c1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(c1, text="Currency Symbol", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_curr_sym = ctk.CTkEntry(c1, height=38)
        self.entry_curr_sym.pack(fill="x", pady=(2, 0))
        self.entry_curr_sym.insert(0, self.settings.get("currency_symbol", "Rs"))

        c2 = ctk.CTkFrame(curr_row, fg_color="transparent")
        c2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(c2, text="Symbol Position", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.opt_curr_pos = ctk.CTkOptionMenu(c2, values=["Before Amount (e.g. Rs 500)", "After Amount (e.g. 500 Rs)"], height=38)
        self.opt_curr_pos.pack(fill="x", pady=(2, 0))
        pos_val = "After Amount (e.g. 500 Rs)" if self.settings.get("currency_position") == "after" else "Before Amount (e.g. Rs 500)"
        self.opt_curr_pos.set(pos_val)

        ctk.CTkLabel(scroll, text="Sales Tax / VAT Settings", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(10, 10))

        # Enable Tax Switch
        self.switch_tax_var = ctk.StringVar(value="1" if self.settings.get("enable_tax") == "1" else "0")
        self.switch_tax = ctk.CTkSwitch(
            scroll, text="Enable Sales Tax / VAT on Transactions",
            variable=self.switch_tax_var, onvalue="1", offvalue="0",
            font=FONTS["body_lg"]
        )
        self.switch_tax.pack(anchor="w", pady=(0, 15))

        tax_row = ctk.CTkFrame(scroll, fg_color="transparent")
        tax_row.pack(fill="x", pady=(0, 15))

        t1 = ctk.CTkFrame(tax_row, fg_color="transparent")
        t1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(t1, text="Tax Label / Name", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_tax_name = ctk.CTkEntry(t1, height=38)
        self.entry_tax_name.pack(fill="x", pady=(2, 0))
        self.entry_tax_name.insert(0, self.settings.get("tax_name", "VAT"))

        t2 = ctk.CTkFrame(tax_row, fg_color="transparent")
        t2.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(t2, text="Tax Rate (%)", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_tax_rate = ctk.CTkEntry(t2, height=38)
        self.entry_tax_rate.pack(fill="x", pady=(2, 0))
        self.entry_tax_rate.insert(0, self.settings.get("tax_percentage", "0"))

        t3 = ctk.CTkFrame(tax_row, fg_color="transparent")
        t3.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(t3, text="Pricing Mode", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.opt_tax_mode = ctk.CTkOptionMenu(t3, values=["Exclusive (Added on top)", "Inclusive (Included in price)"], height=38)
        self.opt_tax_mode.pack(fill="x", pady=(2, 0))
        mode_val = "Inclusive (Included in price)" if self.settings.get("tax_type") == "inclusive" else "Exclusive (Added on top)"
        self.opt_tax_mode.set(mode_val)

        # Save Button
        ctk.CTkButton(
            scroll, text="Save Currency & Tax Settings", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=42, text_color="#FFFFFF", command=self._save_tax_settings
        ).pack(anchor="w")

    def _save_tax_settings(self):
        curr_pos = "after" if "After" in self.opt_curr_pos.get() else "before"
        tax_mode = "inclusive" if "Inclusive" in self.opt_tax_mode.get() else "exclusive"
        updates = {
            "currency_symbol": self.entry_curr_sym.get().strip() or "Rs",
            "currency_position": curr_pos,
            "enable_tax": self.switch_tax_var.get(),
            "tax_name": self.entry_tax_name.get().strip() or "VAT",
            "tax_percentage": self.entry_tax_rate.get().strip() or "0",
            "tax_type": tax_mode
        }
        SettingsController.save_settings(updates)
        ctk.CTkInputDialog(text="Currency and tax settings updated.", title="Settings Saved")

    # --- 3. Receipt & Printer Tab ---
    def _build_print_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_print, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(scroll, text="Thermal Receipt Formatting", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 10))

        # Receipt Width & Auto-print
        rw_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        rw_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(rw_frame, text="Paper Width:", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(side="left", padx=(0, 10))
        self.opt_width = ctk.CTkSegmentedButton(rw_frame, values=["80mm (Standard)", "58mm (Compact)"], height=36)
        self.opt_width.set("80mm (Standard)" if self.settings.get("receipt_width") == "80mm" else "58mm (Compact)")
        self.opt_width.pack(side="left")

        self.switch_autoprint_var = ctk.StringVar(value=self.settings.get("auto_print", "0"))
        self.switch_autoprint = ctk.CTkSwitch(
            scroll, text="Automatically Print Receipt on Sale Complete",
            variable=self.switch_autoprint_var, onvalue="1", offvalue="0",
            font=FONTS["body_md"]
        )
        self.switch_autoprint.pack(anchor="w", pady=(0, 15))

        # Header and Footer text
        ctk.CTkLabel(scroll, text="Receipt Header Line (Greetings)", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_rcpt_header = ctk.CTkEntry(scroll, height=38)
        self.entry_rcpt_header.pack(fill="x", pady=(2, 10))
        self.entry_rcpt_header.insert(0, self.settings.get("receipt_header", ""))

        ctk.CTkLabel(scroll, text="Receipt Footer Notes (Policy / Thank You)", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w")
        self.entry_rcpt_footer = ctk.CTkEntry(scroll, height=38)
        self.entry_rcpt_footer.pack(fill="x", pady=(2, 15))
        self.entry_rcpt_footer.insert(0, self.settings.get("receipt_footer", ""))

        # Hardware Printer Selection
        ctk.CTkLabel(scroll, text="Hardware Printer Connection", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", pady=(10, 10))

        printers = ReceiptPrinter.get_printers()
        pr_row = ctk.CTkFrame(scroll, fg_color="transparent")
        pr_row.pack(fill="x", pady=(0, 15))

        self.opt_printer = ctk.CTkOptionMenu(pr_row, values=printers, height=38, font=FONTS["body_md"])
        self.opt_printer.pack(side="left", fill="x", expand=True, padx=(0, 10))
        active_pr = self.settings.get("printer_name", printers[0])
        if active_pr in printers:
            self.opt_printer.set(active_pr)

        ctk.CTkButton(
            pr_row, text="Test Print", height=38, font=FONTS["body_md"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=self._test_printer
        ).pack(side="right")

        # Save Button
        ctk.CTkButton(
            scroll, text="Save Receipt & Printer Settings", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=42, text_color="#FFFFFF", command=self._save_print_settings
        ).pack(anchor="w")

    def _test_printer(self):
        sample_order = {
            "order_number": "TEST-0001",
            "customer_name": "Test Customer",
            "cashier_name": "Admin",
            "created_at": "2026-09-20 12:00:00",
            "items": [{"product_name": "Sample Test Item", "quantity": 1, "unit_price": 100, "total": 100}],
            "subtotal": 100, "discount_amount": 0, "tax_amount": 0, "total": 100,
            "amount_paid": 100, "change_due": 0, "payment_method": "cash"
        }
        sel_pr = self.opt_printer.get()
        ok, msg = ReceiptPrinter.print_receipt(sample_order, printer_name=sel_pr)
        ctk.CTkInputDialog(text=msg, title="Printer Test Result")

    def _save_print_settings(self):
        width = "58mm" if "58mm" in self.opt_width.get() else "80mm"
        updates = {
            "receipt_width": width,
            "auto_print": self.switch_autoprint_var.get(),
            "receipt_header": self.entry_rcpt_header.get().strip(),
            "receipt_footer": self.entry_rcpt_footer.get().strip(),
            "printer_name": self.opt_printer.get()
        }
        SettingsController.save_settings(updates)
        ctk.CTkInputDialog(text="Receipt and printer settings updated.", title="Settings Saved")

    # --- 4. User Roles Tab ---
    def _build_users_tab(self):
        top = ctk.CTkFrame(self.tab_users, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top, text="User Management (Admin & Cashier Roles)", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            top, text="➕ Add User", font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            height=36, command=self._add_user_dialog
        ).pack(side="right")

        self.users_scroll = ctk.CTkScrollableFrame(self.tab_users, fg_color=COLORS["bg_input"], corner_radius=8)
        self.users_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._refresh_users_list()

    def _refresh_users_list(self):
        for w in self.users_scroll.winfo_children():
            w.destroy()

        users = UserModel.list_all()
        for u in users:
            row = ctk.CTkFrame(self.users_scroll, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            role_col = COLORS["primary"] if u["role"] == "Admin" else COLORS["success"]
            ctk.CTkLabel(row, text=u["role"].upper(), font=FONTS["title_sm"], text_color=role_col, width=80, anchor="w").pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=u["username"], font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=130, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=u["full_name"], font=FONTS["body_md"], text_color=COLORS["text_secondary"], width=200, anchor="w").pack(side="left", padx=5)

            status_str = "Active" if u["is_active"] else "Inactive"
            ctk.CTkLabel(row, text=status_str, font=FONTS["body_sm"], text_color=COLORS["success"] if u["is_active"] else COLORS["danger"], width=80).pack(side="left")

            if u["username"].lower() != "admin":
                ctk.CTkButton(
                    row, text="Deactivate" if u["is_active"] else "Activate",
                    width=90, height=28, font=FONTS["body_sm"],
                    fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
                    command=lambda uid=u["id"], act=u["is_active"]: self._toggle_user_active(uid, act)
                ).pack(side="right", padx=15)

    def _add_user_dialog(self):
        u_dlg = ctk.CTkInputDialog(text="Enter Username:", title="Add User")
        username = u_dlg.get_input()
        if not username or not username.strip():
            return
        p_dlg = ctk.CTkInputDialog(text=f"Enter password for {username.strip()}:", title="Password")
        password = p_dlg.get_input()
        if not password or not password.strip():
            return
        n_dlg = ctk.CTkInputDialog(text=f"Enter Full Name for {username.strip()}:", title="Full Name")
        fullname = n_dlg.get_input() or username.strip()

        r_dlg = ctk.CTkInputDialog(text="Enter Role (Admin or Cashier):", title="Role")
        role_input = (r_dlg.get_input() or "Cashier").strip().capitalize()
        role = "Admin" if role_input == "Admin" else "Cashier"

        UserModel.create(username.strip(), password.strip(), fullname.strip(), role)
        self._refresh_users_list()

    def _toggle_user_active(self, uid, current_active):
        u = UserModel.get_by_id(uid)
        if u:
            new_state = 0 if current_active else 1
            UserModel.update(uid, u["full_name"], u["role"], new_state)
            self._refresh_users_list()

    # --- 5. Backup & Reset Tab ---
    def _build_data_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_data, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # Database Backup Card
        b_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        b_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(b_card, text="💾 Database Backup", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(15, 4))
        ctk.CTkLabel(
            b_card, text="Creates a standalone, date-stamped copy of pos_data.db that can be archived or copied to a USB drive.",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 10))

        b_btns = ctk.CTkFrame(b_card, fg_color="transparent")
        b_btns.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            b_btns, text="Backup Database Now", height=38, font=FONTS["title_sm"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._do_backup
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            b_btns, text="Restore Database from Backup", height=38, font=FONTS["title_sm"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            command=self._do_restore
        ).pack(side="left")

        # Data Maintenance / Reset Card
        r_card = ctk.CTkFrame(scroll, fg_color=COLORS["danger_subtle"], corner_radius=10)
        r_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(r_card, text="⚠️ Danger Zone: Data Reset", font=FONTS["title_md"], text_color=COLORS["danger"]).pack(anchor="w", padx=15, pady=(15, 4))
        ctk.CTkLabel(
            r_card, text="These actions permanently erase data. Admin password confirmation is required.",
            font=FONTS["body_md"], text_color=COLORS["danger"]
        ).pack(anchor="w", padx=15, pady=(0, 10))

        r_btns = ctk.CTkFrame(r_card, fg_color="transparent")
        r_btns.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            r_btns, text="Clear Sales History Only (Keep Catalog)", height=38,
            font=FONTS["title_sm"], fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
            text_color="#FFFFFF", command=self._do_clear_sales
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            r_btns, text="Factory Reset (Wipe Everything)", height=38,
            font=FONTS["title_sm"], fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color="#FFFFFF", command=self._do_factory_reset
        ).pack(side="left")

    def _do_backup(self):
        ok, msg = SettingsController.backup_database()
        ctk.CTkInputDialog(text=msg, title="Backup Result")

    def _do_restore(self):
        filepath = fd.askopenfilename(
            title="Select Database Backup to Restore",
            filetypes=[("SQLite Database", "*.db *.safety_bak"), ("All files", "*.*")]
        )
        if filepath:
            ok, msg = SettingsController.restore_database(filepath)
            ctk.CTkInputDialog(text=msg, title="Restore Result")

    def _verify_admin_password(self) -> bool:
        pwd_dlg = ctk.CTkInputDialog(text="Enter Admin password to confirm dangerous operation:", title="Confirm Password")
        pwd = pwd_dlg.get_input()
        if not pwd:
            return False
        admin = UserModel.get_by_username("admin")
        from pos_app.utils.security import verify_password
        return admin and verify_password(admin["password_hash"], pwd)

    def _do_clear_sales(self):
        if not self._verify_admin_password():
            ctk.CTkInputDialog(text="Incorrect admin password. Action aborted.", title="Access Denied")
            return
        ok, msg = SettingsController.clear_sales_history()
        ctk.CTkInputDialog(text=msg, title="Sales Cleared")

    def _do_factory_reset(self):
        if not self._verify_admin_password():
            ctk.CTkInputDialog(text="Incorrect admin password. Action aborted.", title="Access Denied")
            return
        ok, msg = SettingsController.factory_reset()
        ctk.CTkInputDialog(text=msg, title="Factory Reset")
