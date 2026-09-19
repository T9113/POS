import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS

class ShortcutsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Keyboard Shortcuts Cheat Sheet")
        self.geometry("500x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 500) // 2)
        y = py + max(0, (ph - 420) // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="⌨️ Keyboard Shortcuts", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(10, 15))

        shortcuts = [
            ("F1", "New Sale (Start new blank transaction)"),
            ("F2", "Focus Search / Barcode scanner input"),
            ("F3", "Hold Order (Park current order)"),
            ("F4", "Recall Held Order (Open parked orders list)"),
            ("F5", "Payment / Checkout modal"),
            ("Escape", "Cancel / Close modal dialog"),
            ("Enter", "Confirm action / Scan product into cart"),
            ("Delete / Backspace", "Remove selected item from cart")
        ]

        table_frame = ctk.CTkFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        for key, desc in shortcuts:
            row = ctk.CTkFrame(table_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=6)

            badge = ctk.CTkLabel(
                row, text=key, font=FONTS["mono_bold"],
                fg_color=COLORS["primary"], text_color="#FFFFFF",
                corner_radius=6, width=65, height=28
            )
            badge.pack(side="left")

            ctk.CTkLabel(
                row, text=desc, font=FONTS["body_md"],
                text_color=COLORS["text_primary"]
            ).pack(side="left", padx=(15, 0))

        ctk.CTkButton(
            container, text="Got It (Esc)", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], height=38, font=FONTS["body_md"],
            command=self.destroy
        ).pack(fill="x", padx=15, pady=(0, 10))
