import sys
from datetime import datetime
from pos_app.models.settings_model import SettingsModel

class ReceiptPrinter:
    @staticmethod
    def get_printers():
        """Returns list of available Windows printers."""
        printers = []
        if sys.platform == "win32":
            try:
                import win32print
                # EnumPrinters flags: PRINTER_ENUM_LOCAL (2) | PRINTER_ENUM_CONNECTIONS (4)
                raw_printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                printers = [p[2] for p in raw_printers]
            except Exception:
                pass
        return printers or ["Default Windows Printer"]

    @staticmethod
    def format_receipt_text(order: dict, width: str = "80mm") -> str:
        """
        Formats order details into a clean receipt string for thermal printers or screen preview.
        Supports 58mm (32 columns) and 80mm (42 columns).
        """
        settings = SettingsModel.get_all()
        biz_name = settings.get("business_name", "SwiftPOS Retail Store")
        biz_addr = settings.get("business_address", "")
        biz_phone = settings.get("business_phone", "")
        biz_tax = settings.get("tax_number", "")
        header_note = settings.get("receipt_header", "")
        footer_note = settings.get("receipt_footer", "Thank you for shopping!\nPlease come again.")
        currency = settings.get("currency_symbol", "Rs")

        col_w = 42 if width == "80mm" else 32
        sep_double = "=" * col_w
        sep_single = "-" * col_w

        lines = [
            sep_double,
            biz_name.center(col_w),
        ]
        if biz_addr:
            lines.append(biz_addr.center(col_w))
        if biz_phone:
            lines.append(f"Phone: {biz_phone}".center(col_w))
        if biz_tax:
            lines.append(f"Tax Reg: {biz_tax}".center(col_w))
        if header_note:
            lines.append(header_note.center(col_w))

        lines.append(sep_double)

        created_at = order.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")
        except Exception:
            date_str = str(created_at)[:10]
            time_str = str(created_at)[11:16]

        lines.append(f"Date: {date_str}   Time: {time_str}")
        lines.append(f"Order#: {order.get('order_number', 'N/A')}  Cashier: {order.get('cashier_name', 'Admin')}")
        customer_name = order.get("customer_name") or "Walk-in"
        lines.append(f"Customer: {customer_name}")
        lines.append(sep_single)

        # Header for columns: Item, Qty, Price, Total
        if col_w == 42:
            lines.append(f"{'Item':<18}{'Qty':>4}{'Price':>10}{'Total':>10}")
        else:
            lines.append(f"{'Item':<14}{'Qty':>3}{'Total':>15}")
        lines.append(sep_single)

        for item in order.get("items", []):
            name = item.get("product_name", "Item")
            qty = float(item.get("quantity", 1))
            price = float(item.get("unit_price", 0))
            total = float(item.get("total", 0))
            qty_str = f"{qty:g}"

            if col_w == 42:
                short_name = name[:17]
                lines.append(f"{short_name:<18}{qty_str:>4}{price:>10,.2f}{total:>10,.2f}")
            else:
                short_name = name[:13]
                lines.append(f"{short_name:<14}{qty_str:>3}{total:>15,.2f}")

        lines.append(sep_single)

        # Totals
        subtotal = float(order.get("subtotal", 0))
        discount = float(order.get("discount_amount", 0))
        tax = float(order.get("tax_amount", 0))
        total_val = float(order.get("total", 0))
        paid = float(order.get("amount_paid", 0))
        change = float(order.get("change_due", 0))

        lines.append(f"{'Subtotal:':<22}{currency:>4} {subtotal:>14,.2f}")
        if discount > 0:
            lines.append(f"{'Discount:':<22}{'-' + currency:>4} {discount:>14,.2f}")
        if tax > 0:
            lines.append(f"{'Tax:':<22}{currency:>4} {tax:>14,.2f}")

        lines.append(sep_double)
        lines.append(f"{'TOTAL:':<22}{currency:>4} {total_val:>14,.2f}")
        lines.append(sep_double)

        pay_method = order.get("payment_method", "cash").capitalize()
        lines.append(f"{f'Paid ({pay_method}):':<22}{currency:>4} {paid:>14,.2f}")
        if change > 0:
            lines.append(f"{'Change Due:':<22}{currency:>4} {change:>14,.2f}")

        lines.append(sep_single)
        for footer_line in footer_note.split("\n"):
            lines.append(footer_line.center(col_w))
        lines.append(sep_double)
        lines.append("\n\n")

        return "\n".join(lines)

    @staticmethod
    def print_receipt(order: dict, printer_name: str = None) -> tuple[bool, str]:
        """
        Sends raw ESC/POS formatted receipt to thermal printer via win32print.
        Returns (success: bool, message: str)
        """
        width = SettingsModel.get("receipt_width", "80mm")
        receipt_text = ReceiptPrinter.format_receipt_text(order, width)

        if sys.platform != "win32":
            return False, "Printing only supported on Windows."

        target_printer = printer_name or SettingsModel.get("printer_name", "Default")

        try:
            import win32print
            if target_printer == "Default" or not target_printer:
                target_printer = win32print.GetDefaultPrinter()

            # ESC/POS commands: Initialize (\x1b@), Cut paper (\x1dV\x00)
            esc_init = b"\x1b@"
            esc_cut = b"\x1dV\x00"
            raw_data = esc_init + receipt_text.encode("utf-8", errors="replace") + esc_cut

            h_printer = win32print.OpenPrinter(target_printer)
            try:
                h_job = win32print.StartDocPrinter(h_printer, 1, ("SwiftPOS Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(h_printer)
                    win32print.WritePrinter(h_printer, raw_data)
                    win32print.EndPagePrinter(h_printer)
                finally:
                    win32print.EndDocPrinter(h_printer)
            finally:
                win32print.ClosePrinter(h_printer)

            return True, f"Printed successfully to {target_printer}"
        except Exception as e:
            return False, f"Could not print to hardware printer: {e}"
