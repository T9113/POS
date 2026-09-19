import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.settings_model import SettingsModel
from pos_app.utils.i18n import t

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, on_login_success=None):
        super().__init__(parent, fg_color=COLORS["bg_main"])
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        # Center Card
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=16, width=440, height=520)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # Header branding
        biz_name = SettingsModel.get("business_name", "OnesDev POS Store")

        ctk.CTkLabel(
            card, text="🛒", font=("Segoe UI", 42)
        ).pack(pady=(35, 5))

        ctk.CTkLabel(
            card, text="OnesDev POS", font=FONTS["title_xl"],
            text_color=COLORS["primary"]
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            card, text=f"{biz_name}  •  Desktop POS System",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 25))

        # Form Fields
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=35)

        ctk.CTkLabel(
            form_frame, text=t("username"), font=FONTS["title_sm"],
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 3))

        self.entry_username = ctk.CTkEntry(
            form_frame, height=44, font=FONTS["body_lg"],
            placeholder_text="e.g. admin"
        )
        self.entry_username.pack(fill="x", pady=(0, 15))
        self.entry_username.insert(0, "admin")

        ctk.CTkLabel(
            form_frame, text=t("password"), font=FONTS["title_sm"],
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 3))

        self.entry_password = ctk.CTkEntry(
            form_frame, height=44, font=FONTS["body_lg"],
            placeholder_text="••••••••", show="•"
        )
        self.entry_password.pack(fill="x", pady=(0, 10))
        self.entry_password.insert(0, "admin")

        self.lbl_error = ctk.CTkLabel(
            form_frame, text="", font=FONTS["body_sm"],
            text_color=COLORS["danger"]
        )
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        # Login Button
        self.btn_login = ctk.CTkButton(
            form_frame, text=t("login"), font=FONTS["title_sm"],
            height=46, fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            command=self._do_login
        )
        self.btn_login.pack(fill="x", pady=(0, 15))

        # Demo Credentials Hint
        hint_card = ctk.CTkFrame(card, fg_color=COLORS["bg_input"], corner_radius=8)
        hint_card.pack(fill="x", padx=35, pady=(5, 10))

        ctk.CTkLabel(
            hint_card,
            text="Default Credentials:\nAdmin: admin / admin  |  Cashier: cashier / cashier",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"], justify="center"
        ).pack(pady=8)

        # Bind Enter key
        self.entry_password.bind("<Return>", lambda e: self._do_login())
        self.entry_username.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.lbl_error.configure(text="Please enter both username and password.")
            return

        ok, msg = AuthController.login(username, password)
        if ok:
            self.lbl_error.configure(text="")
            if self.on_login_success:
                self.on_login_success()
        else:
            self.lbl_error.configure(text=msg)
