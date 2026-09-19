import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.utils.receipt_printer import ReceiptPrinter

class ReceiptPreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, order: dict):
        super().__init__(parent)
        self.order = order
        self.title(f"Receipt - Order #{order.get('order_number', '')}")
        self.geometry("450x640")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 450) // 2)
        y = py + max(0, (ph - 640) // 2)
        self.geometry(f"+{x}+{y}")

        self.receipt_text = ReceiptPrinter.format_receipt_text(order)
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        top_bar = ctk.CTkFrame(container, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 10))

        ctk.CTkLabel(top_bar, text="Receipt Preview", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(side="left")
        
        # Receipt Textbox (Monospace)
        self.txt_receipt = ctk.CTkTextbox(
            container, font=FONTS["mono"], fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"], corner_radius=8, wrap="none"
        )
        self.txt_receipt.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.txt_receipt.insert("1.0", self.receipt_text)
        self.txt_receipt.configure(state="disabled")

        # Status feedback label
        self.lbl_status = ctk.CTkLabel(container, text="", font=FONTS["body_sm"], text_color=COLORS["text_secondary"])
        self.lbl_status.pack(padx=15, pady=(0, 5))

        # Bottom Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Close (Esc)", fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], height=40, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="Copy Text", fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"], height=40, font=FONTS["body_md"],
            command=self._copy_to_clipboard
        ).pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            btn_bar, text="🖨️ Print Receipt", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            height=40, font=FONTS["title_sm"], command=self._print
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.receipt_text)
        self.lbl_status.configure(text="Receipt copied to clipboard!", text_color=COLORS["success"])

    def _print(self):
        ok, msg = ReceiptPrinter.print_receipt(self.order)
        if ok:
            self.lbl_status.configure(text=msg, text_color=COLORS["success"])
        else:
            self.lbl_status.configure(text=msg, text_color=COLORS["warning"])
