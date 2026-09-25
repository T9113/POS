"""
PySide6 Settings View for OnesDev POS.
Configuration for Business Profile, Taxes, Currency, Receipt Printers,
User Management, Desktop Shortcuts, and Database Backup / Factory Reset.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QCheckBox, QComboBox, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog,
    QScrollArea, QFrame, QFormLayout
)

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard
from pos_app.models.settings_model import SettingsModel
from pos_app.models.user_model import UserModel
from pos_app.controllers.settings_controller import SettingsController
from pos_app.utils.receipt_printer import ReceiptPrinter
from pos_app.utils.shortcut_helper import create_desktop_shortcut
from pos_app.utils.security import verify_password
from pos_app.views.dialogs.qt_category_dialog import QtCategoryManagerDialog
from pos_app.utils.license_manager import LicenseManager
from pos_app.utils.icon_helper import get_icon


class QtSettingsView(QWidget):
    """Configuration and Administration Center."""
    settings_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsModel.get_all()
        self.category_dialog = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['bg_surface']};
                border-radius: 12px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {COLORS['bg_main']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 13px;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['bg_surface']};
                color: {COLORS['primary']};
                border-top: 3px solid {COLORS['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLORS['bg_hover']};
            }}
        """)

        # 1. Business Profile
        self.tab_biz = QWidget()
        self._build_biz_tab()
        self.tabs.addTab(self.tab_biz, get_icon("building", COLORS["text_secondary"], 16), "Business Profile")

        # 2. Taxes & Currency
        self.tab_tax = QWidget()
        self._build_tax_tab()
        self.tabs.addTab(self.tab_tax, get_icon("dollar", COLORS["text_secondary"], 16), "Taxes && Currency")

        # 3. Receipt & Printer
        self.tab_print = QWidget()
        self._build_print_tab()
        self.tabs.addTab(self.tab_print, get_icon("printer", COLORS["text_secondary"], 16), "Receipt && Printer")

        # 4. User Roles
        self.tab_users = QWidget()
        self._build_users_tab()
        self.tabs.addTab(self.tab_users, get_icon("user", COLORS["text_secondary"], 16), "User Accounts")

        # 5. Backup & Reset
        self.tab_data = QWidget()
        self._build_data_tab()
        self.tabs.addTab(self.tab_data, get_icon("database", COLORS["text_secondary"], 16), "Backup && Reset")

        main_layout.addWidget(self.tabs)

    # --- 1. Business Profile Tab ---
    def _build_biz_tab(self):
        layout = QVBoxLayout(self.tab_biz)
        layout.setContentsMargins(24, 20, 24, 20)

        scroll = QScrollArea(self.tab_biz)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(14)

        lbl_sec = QLabel("Store Identity & Contact Details", container)
        lbl_sec.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_sec)

        form = QFormLayout()
        form.setSpacing(12)

        self.txt_biz_name = QLineEdit(container)
        self.txt_biz_name.setText(self.settings.get("business_name", ""))
        self.txt_biz_name.setFixedHeight(38)
        form.addRow("Business Name *:", self.txt_biz_name)

        self.txt_biz_addr = QLineEdit(container)
        self.txt_biz_addr.setText(self.settings.get("business_address", ""))
        self.txt_biz_addr.setFixedHeight(38)
        form.addRow("Store Address:", self.txt_biz_addr)

        self.txt_biz_phone = QLineEdit(container)
        self.txt_biz_phone.setText(self.settings.get("business_phone", ""))
        self.txt_biz_phone.setFixedHeight(38)
        form.addRow("Phone Number:", self.txt_biz_phone)

        self.txt_biz_email = QLineEdit(container)
        self.txt_biz_email.setText(self.settings.get("business_email", ""))
        self.txt_biz_email.setFixedHeight(38)
        form.addRow("Email Address:", self.txt_biz_email)

        self.txt_biz_tax = QLineEdit(container)
        self.txt_biz_tax.setText(self.settings.get("tax_number", ""))
        self.txt_biz_tax.setFixedHeight(38)
        form.addRow("Tax / NTN Number:", self.txt_biz_tax)

        c_layout.addLayout(form)

        btn_save = AnimatedButton("Save Business Profile", container, variant="primary", icon_name="check")
        btn_save.setFixedHeight(40)
        btn_save.setFixedWidth(220)
        btn_save.clicked.connect(self._save_biz_profile)
        c_layout.addWidget(btn_save)

        # System & Desktop Tools
        line = QFrame(container)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']};")
        c_layout.addWidget(line)

        lbl_tools = QLabel("Desktop & System Tools", container)
        lbl_tools.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_tools)

        tools_row = QHBoxLayout()
        btn_shortcut = AnimatedButton("Create Desktop Shortcut", container, variant="secondary", icon_name="lightning")
        btn_shortcut.setFixedHeight(38)
        btn_shortcut.clicked.connect(self._create_shortcut)
        tools_row.addWidget(btn_shortcut)

        btn_cats = AnimatedButton("Manage Product Categories", container, variant="secondary", icon_name="tag")
        btn_cats.setFixedHeight(38)
        btn_cats.clicked.connect(self._open_category_manager)
        tools_row.addWidget(btn_cats)

        tools_row.addStretch()
        c_layout.addLayout(tools_row)

        # Software License & Machine Binding Section
        line_lic = QFrame(container)
        line_lic.setFrameShape(QFrame.Shape.HLine)
        line_lic.setStyleSheet(f"background-color: {COLORS['border']};")
        c_layout.addWidget(line_lic)

        lbl_lic_t = QLabel("Software License & Machine Binding", container)
        lbl_lic_t.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_lic_t)

        lic_info = LicenseManager.get_license_info()
        lic_card = QFrame(container)
        lic_card.setObjectName("LicenseCard")
        lic_card.setStyleSheet(f"""
            QFrame#LicenseCard {{
                background-color: {COLORS['bg_hover']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        lic_layout = QVBoxLayout(lic_card)
        lic_layout.setContentsMargins(14, 12, 14, 12)
        lic_layout.setSpacing(6)

        st_col = COLORS['success'] if lic_info['is_activated'] else COLORS['danger']
        st_txt = "Active / Valid License" if lic_info['is_activated'] else "Unregistered / Trial"
        lbl_st = QLabel(f"Status: <b style='color:{st_col};'>{st_txt}</b>", lic_card)
        lbl_st.setStyleSheet("font-size: 13px;")
        lic_layout.addWidget(lbl_st)

        lbl_mach = QLabel(f"Machine ID: <b>{lic_info['machine_id']}</b>", lic_card)
        lbl_mach.setStyleSheet("font-size: 13px; font-family: Consolas, monospace;")
        lic_layout.addWidget(lbl_mach)

        lbl_cli = QLabel(f"Licensed To: <b>{lic_info['client_name']}</b> ({lic_info['license_type']})", lic_card)
        lbl_cli.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        lic_layout.addWidget(lbl_cli)

        c_layout.addWidget(lic_card)

        c_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _save_biz_profile(self):
        updates = {
            "business_name": self.txt_biz_name.text().strip(),
            "business_address": self.txt_biz_addr.text().strip(),
            "business_phone": self.txt_biz_phone.text().strip(),
            "business_email": self.txt_biz_email.text().strip(),
            "tax_number": self.txt_biz_tax.text().strip()
        }
        SettingsController.save_settings(updates)
        self.settings.update(updates)
        self.settings_updated.emit()
        QMessageBox.information(self, "Success", "Business profile updated successfully.")

    def _create_shortcut(self):
        ok, path = create_desktop_shortcut()
        if ok:
            QMessageBox.information(self, "Shortcut Created", f"Desktop shortcut created successfully:\n\n{path}")
        else:
            QMessageBox.warning(self, "Shortcut Notice", f"{path}")

    def _open_category_manager(self):
        top_window = self.window()
        if not self.category_dialog:
            self.category_dialog = QtCategoryManagerDialog(top_window)
        self.category_dialog.show_animated()

    # --- 2. Taxes & Currency Tab ---
    def _build_tax_tab(self):
        layout = QVBoxLayout(self.tab_tax)
        layout.setContentsMargins(24, 20, 24, 20)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(16)

        lbl_sec = QLabel("Currency & Valuation Settings", container)
        lbl_sec.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_sec)

        curr_form = QFormLayout()
        curr_form.setSpacing(12)

        self.txt_curr_sym = QLineEdit(container)
        self.txt_curr_sym.setText(self.settings.get("currency_symbol", "Rs"))
        self.txt_curr_sym.setFixedHeight(38)
        curr_form.addRow("Currency Symbol:", self.txt_curr_sym)

        self.cmb_curr_pos = QComboBox(container)
        self.cmb_curr_pos.addItems(["Before Amount (e.g. Rs 500)", "After Amount (e.g. 500 Rs)"])
        self.cmb_curr_pos.setFixedHeight(38)
        if self.settings.get("currency_position") == "after":
            self.cmb_curr_pos.setCurrentIndex(1)
        curr_form.addRow("Symbol Position:", self.cmb_curr_pos)

        c_layout.addLayout(curr_form)

        line = QFrame(container)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']};")
        c_layout.addWidget(line)

        lbl_tax = QLabel("Sales Tax / VAT Settings", container)
        lbl_tax.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_tax)

        self.chk_tax_enable = QCheckBox("Enable Sales Tax / VAT calculation on checkout", container)
        self.chk_tax_enable.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_primary']};")
        self.chk_tax_enable.setChecked(self.settings.get("enable_tax") == "1")
        c_layout.addWidget(self.chk_tax_enable)

        tax_form = QFormLayout()
        tax_form.setSpacing(12)

        self.txt_tax_name = QLineEdit(container)
        self.txt_tax_name.setText(self.settings.get("tax_name", "VAT"))
        self.txt_tax_name.setFixedHeight(38)
        tax_form.addRow("Tax Label / Name:", self.txt_tax_name)

        self.txt_tax_rate = QLineEdit(container)
        self.txt_tax_rate.setText(self.settings.get("tax_percentage", "0"))
        self.txt_tax_rate.setFixedHeight(38)
        tax_form.addRow("Tax Rate (%):", self.txt_tax_rate)

        self.cmb_tax_type = QComboBox(container)
        self.cmb_tax_type.addItems(["Exclusive (Added on top)", "Inclusive (Included in shelf price)"])
        self.cmb_tax_type.setFixedHeight(38)
        if self.settings.get("tax_type") == "inclusive":
            self.cmb_tax_type.setCurrentIndex(1)
        tax_form.addRow("Pricing Mode:", self.cmb_tax_type)

        c_layout.addLayout(tax_form)

        btn_save_tax = AnimatedButton("Save Currency && Tax Settings", container, variant="primary", icon_name="check")
        btn_save_tax.setFixedHeight(40)
        btn_save_tax.setFixedWidth(260)
        btn_save_tax.clicked.connect(self._save_tax_settings)
        c_layout.addWidget(btn_save_tax)

        c_layout.addStretch()
        layout.addWidget(container)

    def _save_tax_settings(self):
        curr_pos = "after" if self.cmb_curr_pos.currentIndex() == 1 else "before"
        tax_type = "inclusive" if self.cmb_tax_type.currentIndex() == 1 else "exclusive"
        updates = {
            "currency_symbol": self.txt_curr_sym.text().strip() or "Rs",
            "currency_position": curr_pos,
            "enable_tax": "1" if self.chk_tax_enable.isChecked() else "0",
            "tax_name": self.txt_tax_name.text().strip() or "VAT",
            "tax_percentage": self.txt_tax_rate.text().strip() or "0",
            "tax_type": tax_type
        }
        SettingsController.save_settings(updates)
        self.settings.update(updates)
        self.settings_updated.emit()
        QMessageBox.information(self, "Success", "Currency and tax settings updated successfully.")

    # --- 3. Receipt & Printer Tab ---
    def _build_print_tab(self):
        layout = QVBoxLayout(self.tab_print)
        layout.setContentsMargins(24, 20, 24, 20)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(14)

        lbl_sec = QLabel("Receipt Customization & Layout", container)
        lbl_sec.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_sec)

        p_form = QFormLayout()
        p_form.setSpacing(12)

        self.cmb_width = QComboBox(container)
        self.cmb_width.addItems(["80mm (Standard POS)", "58mm (Compact Mobile POS)"])
        self.cmb_width.setFixedHeight(38)
        if self.settings.get("receipt_width") == "58mm":
            self.cmb_width.setCurrentIndex(1)
        p_form.addRow("Paper Width:", self.cmb_width)

        self.chk_autoprint = QCheckBox("Automatically print receipt immediately upon completing sale", container)
        self.chk_autoprint.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_primary']};")
        self.chk_autoprint.setChecked(self.settings.get("auto_print") == "1")
        p_form.addRow("Auto-Print:", self.chk_autoprint)

        self.txt_rcpt_header = QLineEdit(container)
        self.txt_rcpt_header.setText(self.settings.get("receipt_header", ""))
        self.txt_rcpt_header.setFixedHeight(38)
        p_form.addRow("Header Greeting:", self.txt_rcpt_header)

        self.txt_rcpt_footer = QLineEdit(container)
        self.txt_rcpt_footer.setText(self.settings.get("receipt_footer", ""))
        self.txt_rcpt_footer.setFixedHeight(38)
        p_form.addRow("Footer Note / Policy:", self.txt_rcpt_footer)

        c_layout.addLayout(p_form)

        line = QFrame(container)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']};")
        c_layout.addWidget(line)

        lbl_pr = QLabel("Thermal Hardware Connection", container)
        lbl_pr.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        c_layout.addWidget(lbl_pr)

        pr_row = QHBoxLayout()
        self.cmb_printers = QComboBox(container)
        self.cmb_printers.setFixedHeight(38)
        available_printers = ReceiptPrinter.get_printers()
        self.cmb_printers.addItems(available_printers)
        cur_pr = self.settings.get("printer_name", "")
        idx = self.cmb_printers.findText(cur_pr)
        if idx >= 0:
            self.cmb_printers.setCurrentIndex(idx)
        pr_row.addWidget(self.cmb_printers, stretch=1)

        btn_test_pr = AnimatedButton("Test Print", container, variant="secondary", icon_name="printer")
        btn_test_pr.setFixedHeight(38)
        btn_test_pr.clicked.connect(self._test_printer)
        pr_row.addWidget(btn_test_pr)
        c_layout.addLayout(pr_row)

        btn_save_pr = AnimatedButton("Save Receipt Settings", container, variant="primary", icon_name="check")
        btn_save_pr.setFixedHeight(40)
        btn_save_pr.setFixedWidth(240)
        btn_save_pr.clicked.connect(self._save_print_settings)
        c_layout.addWidget(btn_save_pr)

        c_layout.addStretch()
        layout.addWidget(container)

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
        sel_pr = self.cmb_printers.currentText()
        ok, msg = ReceiptPrinter.print_receipt(sample_order, printer_name=sel_pr)
        QMessageBox.information(self, "Printer Test Result", msg)

    def _save_print_settings(self):
        width = "58mm" if self.cmb_width.currentIndex() == 1 else "80mm"
        updates = {
            "receipt_width": width,
            "auto_print": "1" if self.chk_autoprint.isChecked() else "0",
            "receipt_header": self.txt_rcpt_header.text().strip(),
            "receipt_footer": self.txt_rcpt_footer.text().strip(),
            "printer_name": self.cmb_printers.currentText()
        }
        SettingsController.save_settings(updates)
        self.settings.update(updates)
        self.settings_updated.emit()
        QMessageBox.information(self, "Success", "Receipt and printer settings updated successfully.")

    # --- 4. User Roles Tab ---
    def _build_users_tab(self):
        layout = QVBoxLayout(self.tab_users)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        lbl_sec = QLabel("User Management & Access Control", self.tab_users)
        lbl_sec.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        top_row.addWidget(lbl_sec)

        btn_add = AnimatedButton("+ Add User", self.tab_users, variant="primary")
        btn_add.setFixedHeight(36)
        btn_add.setToolTip("Create new user login")
        btn_add.clicked.connect(self._add_user_dialog)
        top_row.addWidget(btn_add)
        layout.addLayout(top_row)

        self.table_users = QTableWidget(self.tab_users)
        self.table_users.setColumnCount(5)
        self.table_users.setHorizontalHeaderLabels(["Role", "Username", "Full Name", "Status", "Action"])
        self.table_users.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_users.verticalHeader().setVisible(False)
        self.table_users.setAlternatingRowColors(True)
        self.table_users.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 12px;
                padding: 8px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.table_users)
        self._refresh_users_list()

    def _refresh_users_list(self):
        users = UserModel.list_all()
        self.table_users.setRowCount(len(users))

        for r, u in enumerate(users):
            # Role
            item_role = QTableWidgetItem(u["role"].upper())
            item_role.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_users.setItem(r, 0, item_role)

            # Username
            self.table_users.setItem(r, 1, QTableWidgetItem(u["username"]))

            # Full Name
            self.table_users.setItem(r, 2, QTableWidgetItem(u["full_name"]))

            # Status
            status_text = "Active" if u["is_active"] else "Inactive"
            item_st = QTableWidgetItem(status_text)
            item_st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_users.setItem(r, 3, item_st)

            # Actions: reset password for everyone, activate/deactivate for non-root users
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(4, 2, 4, 2)
            act_layout.setSpacing(6)

            btn_pwd = QPushButton("Change Password")
            btn_pwd.setFixedSize(128, 28)
            btn_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_pwd.setStyleSheet(self._user_action_style(COLORS['primary_subtle'], COLORS['primary']))
            btn_pwd.clicked.connect(lambda _, uid=u["id"], uname=u["username"]: self._change_password(uid, uname))
            act_layout.addWidget(btn_pwd)

            if u["username"].lower() != "admin":
                btn_toggle = QPushButton("Deactivate" if u["is_active"] else "Activate")
                btn_toggle.setFixedSize(92, 28)
                btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_toggle.setStyleSheet(self._user_action_style(
                    COLORS['danger_subtle'] if u['is_active'] else COLORS['success_subtle'],
                    COLORS['danger'] if u['is_active'] else COLORS['success']
                ))
                btn_toggle.clicked.connect(lambda _, uid=u["id"], act=u["is_active"]: self._toggle_user(uid, act))
                act_layout.addWidget(btn_toggle)

            act_layout.addStretch()
            self.table_users.setCellWidget(r, 4, act_widget)
        self.table_users.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table_users.setColumnWidth(4, 250)
        self.table_users.verticalHeader().setDefaultSectionSize(40)

    def _user_action_style(self, hover_bg: str, hover_fg: str) -> str:
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: {hover_fg};
            }}
        """

    def _change_password(self, uid, username):
        pwd, ok = QInputDialog.getText(self, "Change Password", f"New password for '{username}' (min 4 characters):", QLineEdit.EchoMode.Password)
        if not ok:
            return
        pwd = pwd.strip()
        if len(pwd) < 4:
            QMessageBox.warning(self, "Password Too Short", "Password must be at least 4 characters.")
            return
        confirm, ok = QInputDialog.getText(self, "Change Password", "Confirm new password:", QLineEdit.EchoMode.Password)
        if not ok:
            return
        if confirm.strip() != pwd:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match. Nothing was changed.")
            return
        u = UserModel.get_by_id(uid)
        if u:
            UserModel.update(uid, u["full_name"], u["role"], u["is_active"], password=pwd)
            QMessageBox.information(self, "Password Updated", f"Password for '{username}' has been changed.")

    def _toggle_user(self, uid, current_active):
        u = UserModel.get_by_id(uid)
        if u:
            new_state = 0 if current_active else 1
            UserModel.update(uid, u["full_name"], u["role"], new_state)
            self._refresh_users_list()

    def _add_user_dialog(self):
        uname, ok = QInputDialog.getText(self, "Add User", "Enter Username:")
        if not ok or not uname.strip():
            return
        if UserModel.get_by_username(uname.strip()):
            QMessageBox.warning(self, "Username Taken", f"A user named '{uname.strip()}' already exists.")
            return
        pwd, ok = QInputDialog.getText(self, "Add User", f"Enter Password for {uname.strip()} (min 4 characters):", QLineEdit.EchoMode.Password)
        if not ok:
            return
        if len(pwd.strip()) < 4:
            QMessageBox.warning(self, "Password Too Short", "Password must be at least 4 characters.")
            return
        fname, ok = QInputDialog.getText(self, "Add User", f"Enter Full Name for {uname.strip()}:")
        if not ok:
            return
        fullname = fname.strip() or uname.strip()

        roles = ["Cashier", "Admin"]
        role, ok = QInputDialog.getItem(self, "Add User", "Select Role:", roles, 0, False)
        if not ok:
            return

        UserModel.create(uname.strip(), pwd.strip(), fullname, role)
        self._refresh_users_list()
        QMessageBox.information(self, "Success", f"User '{uname.strip()}' created successfully.")

    # --- 5. Backup & Reset Tab ---
    def _build_data_tab(self):
        layout = QVBoxLayout(self.tab_data)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Backup Card
        b_card = DropShadowCard(self.tab_data, corner_radius=12)
        b_layout = QVBoxLayout(b_card)
        b_layout.setContentsMargins(20, 18, 20, 18)
        b_layout.setSpacing(8)

        lbl_b_title = QLabel("Standalone Database Backup & Restore", b_card)
        lbl_b_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        b_layout.addWidget(lbl_b_title)

        lbl_b_desc = QLabel(
            "Creates a timestamped snapshot of pos_data.db that can be stored on a USB drive or cloud drive.",
            b_card
        )
        lbl_b_desc.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        b_layout.addWidget(lbl_b_desc)

        b_btns = QHBoxLayout()
        btn_bk = AnimatedButton("Backup Database Now", b_card, variant="primary", icon_name="upload")
        btn_bk.setFixedHeight(38)
        btn_bk.clicked.connect(self._do_backup)
        b_btns.addWidget(btn_bk)

        btn_res = AnimatedButton("Restore Database from File", b_card, variant="secondary", icon_name="download")
        btn_res.setFixedHeight(38)
        btn_res.clicked.connect(self._do_restore)
        b_btns.addWidget(btn_res)

        b_btns.addStretch()
        b_layout.addLayout(b_btns)
        layout.addWidget(b_card)

        # Danger Zone Card
        d_card = QFrame(self.tab_data)
        d_card.setObjectName("DangerZone")
        d_card.setStyleSheet(f"""
            QFrame#DangerZone {{
                background-color: {COLORS['danger_subtle']};
                border: 1px solid #FECACA;
                border-radius: 12px;
            }}
        """)
        d_layout = QVBoxLayout(d_card)
        d_layout.setContentsMargins(20, 18, 20, 18)
        d_layout.setSpacing(8)

        lbl_d_title = QLabel("Danger Zone: Maintenance & Data Reset", d_card)
        lbl_d_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['danger']};")
        d_layout.addWidget(lbl_d_title)

        lbl_d_desc = QLabel(
            "These actions permanently delete records. Admin master password is required to execute.",
            d_card
        )
        lbl_d_desc.setStyleSheet(f"font-size: 13px; color: {COLORS['danger']};")
        d_layout.addWidget(lbl_d_desc)

        d_btns = QHBoxLayout()
        btn_clear_sales = AnimatedButton("Clear Sales History (Keep Products)", d_card, variant="danger")
        btn_clear_sales.setFixedHeight(38)
        btn_clear_sales.clicked.connect(self._do_clear_sales)
        d_btns.addWidget(btn_clear_sales)

        btn_reset = AnimatedButton("Factory Reset (Wipe Everything)", d_card, variant="danger")
        btn_reset.setFixedHeight(38)
        btn_reset.clicked.connect(self._do_factory_reset)
        d_btns.addWidget(btn_reset)

        d_btns.addStretch()
        d_layout.addLayout(d_btns)
        layout.addWidget(d_card)

        layout.addStretch()

    def _do_backup(self):
        ok, msg = SettingsController.backup_database()
        if ok:
            QMessageBox.information(self, "Backup Successful", msg)
        else:
            QMessageBox.warning(self, "Backup Failed", msg)

    def _do_restore(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Database Backup to Restore", "", "SQLite Database (*.db *.safety_bak);;All Files (*.*)"
        )
        if filepath:
            ok, msg = SettingsController.restore_database(filepath)
            if ok:
                QMessageBox.information(self, "Restore Completed", msg)
                self.settings = SettingsModel.get_all()
                self.settings_updated.emit()
            else:
                QMessageBox.warning(self, "Restore Error", msg)

    def _verify_admin_password(self) -> bool:
        pwd, ok = QInputDialog.getText(self, "Security Check", "Enter Admin password to proceed:", QLineEdit.EchoMode.Password)
        if not ok or not pwd:
            return False
        admin = UserModel.get_by_username("admin")
        return bool(admin and verify_password(admin["password_hash"], pwd))

    def _do_clear_sales(self):
        if not self._verify_admin_password():
            QMessageBox.warning(self, "Access Denied", "Incorrect Admin password.")
            return
        ok, msg = SettingsController.clear_sales_history()
        QMessageBox.information(self, "Sales Cleared", msg)
        self.settings_updated.emit()

    def _do_factory_reset(self):
        if not self._verify_admin_password():
            QMessageBox.warning(self, "Access Denied", "Incorrect Admin password.")
            return
        ok, msg = SettingsController.factory_reset()
        QMessageBox.information(self, "Factory Reset", msg)
        self.settings_updated.emit()
