"""
PySide6 End of Day (EOD) Dialog for OnesDev POS.
Calculates expected cash, accepts actual cash count, records the difference,
and saves the day's closing report.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QPushButton, QFrame
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.models.eod_model import EODModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.icon_helper import get_icon


class QtEODDialog(SmoothModalOverlay):
    """End of Day cash reconciliation and closing wizard."""
    eod_completed = Signal()

    def __init__(self, parent, on_complete=None):
        super().__init__(parent, target_width=500, target_height=520)
        self.on_complete = on_complete
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.eod_data = EODModel.get_eod_calculation_for_today()
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header
        title_row = QHBoxLayout()
        ico = QLabel(content)
        ico.setPixmap(get_icon("sunset", color=COLORS["warning"], size=20).pixmap(20, 20))
        ico.setFixedSize(22, 22)
        title_row.addWidget(ico)

        lbl_title = QLabel("End of Day Closing", content)
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

        # Summary Card
        summary_card = QFrame(content)
        summary_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary_subtle']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        s_layout = QVBoxLayout(summary_card)
        s_layout.setSpacing(8)

        lbl_date = QLabel(f"Report Date: <b>{self.eod_data['date']}</b>", summary_card)
        lbl_date.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']}; background: transparent; border: none;")
        s_layout.addWidget(lbl_date)

        metrics_row = QHBoxLayout()
        self._add_metric(metrics_row, summary_card, "Total Orders", str(self.eod_data["total_orders"]))
        self._add_metric(metrics_row, summary_card, "Total Sales", f"{self.currency} {self.eod_data['total_sales']:,.2f}")
        self._add_metric(metrics_row, summary_card, "Cash Refunds", f"{self.currency} {self.eod_data['cash_refunds']:,.2f}")
        s_layout.addLayout(metrics_row)

        layout.addWidget(summary_card)

        # Expected cash
        exp_frame = QFrame(content)
        exp_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['success_subtle']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        exp_l = QHBoxLayout(exp_frame)
        lbl_exp_title = QLabel("Expected Cash in Drawer:", exp_frame)
        lbl_exp_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text_primary']}; background: transparent; border: none;")
        exp_l.addWidget(lbl_exp_title)
        exp_l.addStretch()
        lbl_exp_val = QLabel(f"{self.currency} {self.eod_data['expected_cash']:,.2f}", exp_frame)
        lbl_exp_val.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['success']}; font-family: Consolas, monospace; background: transparent; border: none;")
        exp_l.addWidget(lbl_exp_val)
        layout.addWidget(exp_frame)

        # Actual cash input
        lbl_actual = QLabel("Actual Cash Counted:", content)
        lbl_actual.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_actual)

        self.txt_actual = QLineEdit(content)
        self.txt_actual.setPlaceholderText(f"Enter the actual cash amount in the drawer")
        self.txt_actual.setFixedHeight(42)
        self.txt_actual.setStyleSheet(f"font-size: 16px; font-weight: bold; padding: 0 12px;")
        self.txt_actual.setText(f"{self.eod_data['expected_cash']:.2f}")
        self.txt_actual.textChanged.connect(self._update_difference)
        layout.addWidget(self.txt_actual)

        # Difference display
        self.lbl_diff = QLabel(f"Difference: {self.currency} 0.00", content)
        self.lbl_diff.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['success']};")
        self.lbl_diff.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lbl_diff)

        # Notes
        lbl_notes = QLabel("Closing Notes (optional):", content)
        lbl_notes.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_notes)

        self.txt_notes = QTextEdit(content)
        self.txt_notes.setFixedHeight(50)
        self.txt_notes.setPlaceholderText("Any discrepancies, unusual events, or notes for the day...")
        self.txt_notes.setStyleSheet(f"border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 6px; font-size: 13px;")
        layout.addWidget(self.txt_notes)

        # Confirm
        self.btn_close_day = AnimatedButton("Close Day & Save Report", content, variant="primary", icon_name="check", icon_color="#FFFFFF", icon_size=16)
        self.btn_close_day.setFixedHeight(44)
        self.btn_close_day.clicked.connect(self._save_eod)
        layout.addWidget(self.btn_close_day)

        self.set_content_widget(content)

    def _add_metric(self, row_layout, parent, title, value):
        w = QWidget(parent)
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)
        lbl_t = QLabel(title, w)
        lbl_t.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; font-weight: 600; background: transparent; border: none;")
        l.addWidget(lbl_t)
        lbl_v = QLabel(value, w)
        lbl_v.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['text_primary']}; background: transparent; border: none;")
        l.addWidget(lbl_v)
        row_layout.addWidget(w)

    def _update_difference(self):
        try:
            actual = float(self.txt_actual.text() or 0)
        except ValueError:
            actual = 0
        diff = actual - self.eod_data["expected_cash"]
        if abs(diff) < 0.01:
            color = COLORS["success"]
            text = f"Difference: {self.currency} 0.00 (Balanced)"
        elif diff > 0:
            color = COLORS["info"]
            text = f"Difference: +{self.currency} {diff:,.2f} (Overage)"
        else:
            color = COLORS["danger"]
            text = f"Difference: -{self.currency} {abs(diff):,.2f} (Shortage)"
        self.lbl_diff.setText(text)
        self.lbl_diff.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color};")

    def _save_eod(self):
        try:
            actual = float(self.txt_actual.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid cash amount.")
            return

        notes = self.txt_notes.toPlainText().strip()
        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        EODModel.save_report(
            user_id=user_id,
            expected_cash=self.eod_data["expected_cash"],
            actual_cash=actual,
            notes=notes,
            total_sales=self.eod_data["total_sales"],
            total_orders=self.eod_data["total_orders"]
        )

        self.eod_completed.emit()
        if self.on_complete:
            self.on_complete()

        QMessageBox.information(self, "Day Closed", "End of Day report saved successfully.")
        self.hide_animated()
