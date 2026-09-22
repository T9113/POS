"""
PySide6 Receipt Preview & Thermal Printer Dialog for OnesDev POS.
Provides real-time preview of 80mm and 58mm receipts with direct Windows thermal printing,
printer selection, and clipboard export.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QComboBox, QFileDialog, QApplication, QMessageBox, QFrame
)

from pos_app.qt_theme import COLORS, AnimatedButton, SmoothModalOverlay
from pos_app.utils.icon_helper import get_icon
from pos_app.utils.receipt_printer import ReceiptPrinter
from pos_app.models.settings_model import SettingsModel


class QtReceiptPreviewDialog(SmoothModalOverlay):
    """Elastic bounce modal for Previewing & Printing Receipts."""

    def __init__(self, parent, order: dict):
        super().__init__(parent, target_width=520, target_height=680)
        self.order = order
        self.current_width = SettingsModel.get("receipt_width", "80mm")
        self._build_dialog_ui()

    def _build_dialog_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header Title
        title_row = QHBoxLayout()
        ico_title = QLabel(content)
        ico_title.setPixmap(get_icon("printer", color=COLORS["primary"], size=20).pixmap(20, 20))
        ico_title.setFixedSize(22, 22)
        title_row.addWidget(ico_title)

        order_num = self.order.get("order_number", "N/A")
        lbl_title = QLabel(f"Receipt - {order_num}", content)
        lbl_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {COLORS['text_primary']};")
        title_row.addWidget(lbl_title)

        title_row.addStretch()

        btn_close = QPushButton("", content)
        btn_close.setIcon(get_icon("close", color=COLORS["text_muted"], size=14))
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; border: none; border-radius: 6px;")
        btn_close.clicked.connect(self.hide_animated)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        # Width Selector & Printer Selector Row
        opt_row = QHBoxLayout()
        opt_row.setSpacing(8)

        lbl_w = QLabel("Format:", content)
        lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        opt_row.addWidget(lbl_w)

        self.btn_80mm = QPushButton("80mm Standard", content)
        self.btn_80mm.setFixedHeight(30)
        self.btn_80mm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_80mm.clicked.connect(lambda: self._set_paper_width("80mm"))
        opt_row.addWidget(self.btn_80mm)

        self.btn_58mm = QPushButton("58mm Compact", content)
        self.btn_58mm.setFixedHeight(30)
        self.btn_58mm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_58mm.clicked.connect(lambda: self._set_paper_width("58mm"))
        opt_row.addWidget(self.btn_58mm)

        opt_row.addStretch()

        lbl_p = QLabel("Printer:", content)
        lbl_p.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};")
        opt_row.addWidget(lbl_p)

        self.cmb_printers = QComboBox(content)
        self.cmb_printers.setFixedHeight(30)
        self.cmb_printers.setMinimumWidth(160)
        available = ReceiptPrinter.get_printers()
        self.cmb_printers.addItems(available)
        cur_pr = SettingsModel.get("printer_name", "")
        idx = self.cmb_printers.findText(cur_pr)
        if idx >= 0:
            self.cmb_printers.setCurrentIndex(idx)
        opt_row.addWidget(self.cmb_printers)

        layout.addLayout(opt_row)

        # Receipt Container (Styled like clean thermal paper)
        self.txt_receipt = QPlainTextEdit(content)
        self.txt_receipt.setReadOnly(True)
        self.txt_receipt.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #FAFAFA;
                color: #0F172A;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.3;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout.addWidget(self.txt_receipt, stretch=1)

        # Status / Feedback label
        self.lbl_status = QLabel("", content)
        self.lbl_status.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(self.lbl_status)

        # Bottom Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_copy = AnimatedButton("Copy Receipt", content, variant="secondary", icon_name="copy", icon_size=14)
        btn_copy.setFixedHeight(38)
        btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(btn_copy)

        btn_save = AnimatedButton("Save Text", content, variant="secondary", icon_name="download", icon_size=14)
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save_to_file)
        btn_row.addWidget(btn_save)

        btn_row.addStretch()

        self.btn_print = AnimatedButton("Print to Hardware", content, variant="primary", icon_name="printer", icon_color="#FFFFFF", icon_size=15)
        self.btn_print.setFixedHeight(38)
        self.btn_print.clicked.connect(self._print_hardware)
        btn_row.addWidget(self.btn_print)

        layout.addLayout(btn_row)
        self.set_content_widget(content)

        # Initialize content
        self._update_style_buttons()
        self._refresh_receipt_text()

    def _set_paper_width(self, width: str):
        self.current_width = width
        self._update_style_buttons()
        self._refresh_receipt_text()

    def _update_style_buttons(self):
        active_style = f"""
            background-color: {COLORS['primary']};
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11px;
            border-radius: 6px;
            padding: 4px 10px;
            border: none;
        """
        inactive_style = f"""
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_secondary']};
            font-weight: 600;
            font-size: 11px;
            border-radius: 6px;
            padding: 4px 10px;
            border: 1px solid {COLORS['border']};
        """
        self.btn_80mm.setStyleSheet(active_style if self.current_width == "80mm" else inactive_style)
        self.btn_58mm.setStyleSheet(active_style if self.current_width == "58mm" else inactive_style)

    def _refresh_receipt_text(self):
        txt = ReceiptPrinter.format_receipt_text(self.order, width=self.current_width)
        self.txt_receipt.setPlainText(txt)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_receipt.toPlainText())
        self.lbl_status.setText("Receipt copied to clipboard!")
        self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: bold;")

    def _save_to_file(self):
        order_num = self.order.get("order_number", "receipt")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt", f"{order_num}.txt", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.txt_receipt.toPlainText())
                self.lbl_status.setText(f"Receipt saved to {file_path}")
                self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: bold;")
            except Exception as e:
                self.lbl_status.setText(f"Failed to save file: {e}")
                self.lbl_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: bold;")

    def _print_hardware(self):
        selected_printer = self.cmb_printers.currentText()
        ok, msg = ReceiptPrinter.print_receipt(
            self.order,
            printer_name=selected_printer,
            width=self.current_width
        )
        if ok:
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: bold;")
        else:
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: bold;")
