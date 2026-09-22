"""
PySide6 Payment Dialog for OnesDev POS.
iPhone-style animated popup with OutBack elastic bounce easing, tender calculator,
split payments, customer Khata ledgering, and hardware receipt trigger.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QFrame, QButtonGroup, QRadioButton, QPushButton
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.utils.icon_helper import get_icon
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.product_model import ProductModel
from pos_app.utils.receipt_printer import ReceiptPrinter


class QtPaymentDialog(SmoothModalOverlay):
    """Elastic bounce modal payment dialog."""
    payment_completed = Signal(dict)

    def __init__(self, parent, cart_data: dict, customer: dict = None, on_complete=None):
        super().__init__(parent, target_width=520, target_height=560)
        self.cart_data = cart_data
        self.customer = customer
        self.on_complete = on_complete
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.total_amount = cart_data.get("grand_total", 0.0)

        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header Title
        title_row = QHBoxLayout()
        ico_title = QLabel(content)
        ico_title.setPixmap(get_icon("credit_card", color=COLORS["primary"], size=20).pixmap(20, 20))
        ico_title.setFixedSize(22, 22)
        title_row.addWidget(ico_title)

        lbl_title = QLabel("Complete Payment", content)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        title_row.addWidget(lbl_title)

        title_row.addStretch()

        btn_close = QPushButton("", content)
        btn_close.setIcon(get_icon("close", color=COLORS["text_muted"], size=14))
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; border: none; border-radius: 6px;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        # Customer ledger info if assigned
        if self.customer:
            cust_text = f"Customer: <b>{self.customer['name']}</b> (Due: {self.currency} {self.customer.get('balance', 0.0):,.2f})"
            lbl_cust = QLabel(cust_text, content)
            lbl_cust.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: {COLORS['bg_hover']}; padding: 6px 10px; border-radius: 6px;")
            layout.addWidget(lbl_cust)

        # Total Amount Due Banner
        banner = QFrame(content)
        banner.setStyleSheet(f"background-color: {COLORS['primary_subtle']}; border-radius: 10px; border: 1.5px solid #C7D2FE;")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)

        lbl_total_txt = QLabel("TOTAL PAYABLE AMOUNT", banner)
        lbl_total_txt.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['primary']}; letter-spacing: 0.5px;")
        banner_layout.addWidget(lbl_total_txt)

        self.lbl_grand_total = QLabel(f"{self.currency} {self.total_amount:,.2f}", banner)
        self.lbl_grand_total.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {COLORS['primary']}; font-family: Consolas, monospace;")
        banner_layout.addWidget(self.lbl_grand_total)
        layout.addWidget(banner)

        # Payment Mode Selector (Pills)
        lbl_method = QLabel("Select Payment Method:", content)
        lbl_method.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_method)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)

        self.btn_cash = AnimatedButton("Cash", content, variant="primary")
        self.btn_cash.setFixedHeight(36)
        self.btn_cash.clicked.connect(lambda: self._set_method("cash"))
        mode_row.addWidget(self.btn_cash)

        self.btn_split = AnimatedButton("Split Payment", content, variant="secondary")
        self.btn_split.setFixedHeight(36)
        self.btn_split.clicked.connect(lambda: self._set_method("split"))
        mode_row.addWidget(self.btn_split)

        self.btn_credit = AnimatedButton("Customer Khata / Due", content, variant="secondary")
        self.btn_credit.setFixedHeight(36)
        self.btn_credit.clicked.connect(lambda: self._set_method("credit"))
        mode_row.addWidget(self.btn_credit)
        layout.addLayout(mode_row)

        self.payment_method = "cash"

        # Cash Tendered & Change Frame
        self.cash_frame = QFrame(content)
        cash_layout = QVBoxLayout(self.cash_frame)
        cash_layout.setContentsMargins(0, 4, 0, 4)
        cash_layout.setSpacing(8)

        # Quick preset buttons
        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        for val in ["Exact", "500", "1000", "5000"]:
            btn_p = AnimatedButton(f"{val if val == 'Exact' else self.currency + ' ' + val}", self.cash_frame, variant="secondary")
            btn_p.setFixedHeight(28)
            btn_p.clicked.connect(lambda _, v=val: self._apply_tender_preset(v))
            preset_row.addWidget(btn_p)
        cash_layout.addLayout(preset_row)

        # Tender input & change output
        tender_row = QHBoxLayout()
        lbl_t = QLabel("Tendered:", self.cash_frame)
        lbl_t.setStyleSheet("font-weight: 600; font-size: 12px;")
        tender_row.addWidget(lbl_t)

        self.txt_tendered = QLineEdit(self.cash_frame)
        self.txt_tendered.setText(f"{self.total_amount:.2f}")
        self.txt_tendered.setFixedHeight(36)
        self.txt_tendered.textChanged.connect(self._calculate_change)
        tender_row.addWidget(self.txt_tendered)

        lbl_c = QLabel("Change Due:", self.cash_frame)
        lbl_c.setStyleSheet("font-weight: 600; font-size: 12px;")
        tender_row.addWidget(lbl_c)

        self.lbl_change = QLabel(f"{self.currency} 0.00", self.cash_frame)
        self.lbl_change.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['success']}; font-family: Consolas, monospace;")
        tender_row.addWidget(self.lbl_change)
        cash_layout.addLayout(tender_row)

        layout.addWidget(self.cash_frame)

        # Auto print checkbox
        self.chk_print = QCheckBox("Print receipt upon completing payment", content)
        self.chk_print.setChecked(SettingsModel.get("auto_print", "0") == "1")
        self.chk_print.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(self.chk_print)

        # Error / Status label
        self.lbl_msg = QLabel("", content)
        self.lbl_msg.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.lbl_msg)

        # Action button
        self.btn_confirm = AnimatedButton(f"Confirm Payment ({self.currency} {self.total_amount:,.2f})", content, variant="success", icon_name="check", icon_color="#FFFFFF", icon_size=16)
        self.btn_confirm.setFixedHeight(46)
        self.btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 15px;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success_hover']};
            }}
        """)
        self.btn_confirm.clicked.connect(self._process_payment)
        layout.addWidget(self.btn_confirm)

        self.set_content_widget(content)

    def _set_method(self, method: str):
        self.payment_method = method
        self.btn_cash.setStyleSheet(self._pill_style(method == "cash"))
        self.btn_split.setStyleSheet(self._pill_style(method == "split"))
        self.btn_credit.setStyleSheet(self._pill_style(method == "credit"))

        if method == "cash":
            self.cash_frame.show()
            self.txt_tendered.setText(f"{self.total_amount:.2f}")
        elif method == "credit":
            if not self.customer:
                self.lbl_msg.setText("Customer selection is required for Credit / Khata.")
            else:
                self.lbl_msg.setText("")
            self.cash_frame.hide()
        elif method == "split":
            self.cash_frame.show()
            self.txt_tendered.setText(f"{self.total_amount / 2:.2f}")

        self._calculate_change()

    def _pill_style(self, active: bool) -> str:
        if active:
            return f"""
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                border-radius: 8px;
                padding: 6px 12px;
                border: none;
            """
        return f"""
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_primary']};
            font-weight: 600;
            font-size: 12px;
            border-radius: 8px;
            padding: 6px 12px;
            border: 1px solid {COLORS['border']};
        """

    def _apply_tender_preset(self, val: str):
        if val == "Exact":
            self.txt_tendered.setText(f"{self.total_amount:.2f}")
        else:
            self.txt_tendered.setText(val)
        self._calculate_change()

    def _calculate_change(self):
        try:
            val = float(self.txt_tendered.text() or 0.0)
            diff = val - self.total_amount
            if diff >= 0:
                self.lbl_change.setText(f"{self.currency} {diff:,.2f}")
                self.lbl_change.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['success']}; font-family: Consolas, monospace;")
            else:
                self.lbl_change.setText(f"Short {self.currency} {abs(diff):,.2f}")
                self.lbl_change.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['danger']}; font-family: Consolas, monospace;")
        except ValueError:
            self.lbl_change.setText(f"{self.currency} 0.00")

    def _process_payment(self):
        if self.payment_method == "credit" and not self.customer:
            self.lbl_msg.setText("Please select a customer first to assign credit ledger!")
            return

        if self.payment_method == "credit":
            tendered = 0.0
            change_due = 0.0
            payment_status = "credit"
        elif self.payment_method in ("cash", "split"):
            try:
                tendered = float(self.txt_tendered.text() or 0.0)
                if self.payment_method == "cash" and tendered < self.total_amount:
                    self.lbl_msg.setText(f"Tendered amount is less than total {self.currency} {self.total_amount:,.2f}!")
                    return
            except ValueError:
                self.lbl_msg.setText("Invalid tendered amount entered.")
                return
            change_due = max(0.0, tendered - self.total_amount)
            payment_status = "paid" if tendered >= self.total_amount else "partial"
        else:
            tendered = self.total_amount
            change_due = 0.0
            payment_status = "paid"

        # Prepare payload and save order
        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1
        cust_id = self.customer["id"] if self.customer else None

        items = self.cart_data.get("items", [])
        subtotal = float(self.cart_data.get("subtotal", self.total_amount))
        discount = float(self.cart_data.get("discount", 0.0))
        tax = float(self.cart_data.get("tax", 0.0))

        order_res = OrderModel.create_order(
            customer_id=cust_id,
            user_id=user_id,
            items=items,
            subtotal=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            total=self.total_amount,
            amount_paid=tendered,
            change_due=change_due,
            payment_method=self.payment_method,
            payment_status=payment_status
        )

        if not order_res or not order_res.get("success"):
            self.lbl_msg.setText("Failed to record order into database.")
            return

        order_dict = order_res.get("order") or {}

        # Print receipt if requested
        if self.chk_print.isChecked():
            ReceiptPrinter.print_receipt(order_dict, width=SettingsModel.get("receipt_width", "80mm"))

        self.payment_completed.emit(order_dict)
        if self.on_complete:
            self.on_complete(order_dict)

        self.hide_animated()
