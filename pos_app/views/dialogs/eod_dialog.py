import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.eod_model import EODModel
from pos_app.models.settings_model import SettingsModel
from pos_app.models.activity_model import ActivityModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.controllers.settings_controller import SettingsController

class EODDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_close_complete=None):
        super().__init__(parent)
        self.on_close_complete = on_close_complete
        self.title("End of Day (EOD) Closing Wizard")
        self.geometry("540x640")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 540) // 2)
        y = py + max(0, (ph - 640) // 2)
        self.geometry(f"+{x}+{y}")

        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.eod_data = EODModel.get_eod_calculation_for_today()
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=8)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="End of Day Register Close", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(10, 2))
        ctk.CTkLabel(
            container, text=f"Date: {self.eod_data['date']}  •  Cash Drawer Reconciliation",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # 1. Summary Metrics Box
        summary_box = ctk.CTkFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        summary_box.pack(fill="x", padx=15, pady=(0, 15))

        self._row(summary_box, "Total Today's Orders:", f"{self.eod_data['total_orders']}")
        self._row(summary_box, "Total Today's Revenue:", f"{self.currency} {self.eod_data['total_sales']:,.2f}")
        self._row(summary_box, "Expected Cash in Drawer:", f"{self.currency} {self.eod_data['expected_cash']:,.2f}", bold=True)

        # 2. Actual Cash Counted Input
        ctk.CTkLabel(container, text="Actual Cash Counted in Drawer *", font=FONTS["title_sm"], text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 4))
        self.entry_actual = ctk.CTkEntry(
            container, height=44, font=FONTS["mono_bold"],
            placeholder_text=f"e.g. {self.eod_data['expected_cash']:g}"
        )
        self.entry_actual.pack(fill="x", padx=15, pady=(0, 10))
        self.entry_actual.bind("<KeyRelease>", self._on_cash_changed)
        self.entry_actual.focus_set()

        # Variance / Difference Box
        self.diff_box = ctk.CTkFrame(container, fg_color=COLORS["bg_surface_raised"], corner_radius=8, height=48)
        self.diff_box.pack(fill="x", padx=15, pady=(0, 15))
        self.diff_box.pack_propagate(False)

        ctk.CTkLabel(self.diff_box, text="Cash Variance (Difference):", font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(side="left", padx=12)
        self.lbl_diff = ctk.CTkLabel(self.diff_box, text=f"{self.currency} 0.00 (Balanced)", font=FONTS["mono_bold"], text_color=COLORS["success"])
        self.lbl_diff.pack(side="right", padx=12)

        # 3. Notes
        ctk.CTkLabel(container, text="Closing Notes / Remarks (Optional):", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(0, 4))
        self.entry_notes = ctk.CTkEntry(container, height=36, placeholder_text="e.g. Petty cash withdrawn, safe transfer...")
        self.entry_notes.pack(fill="x", padx=15, pady=(0, 15))

        # 4. Auto Backup Checkbox
        self.chk_backup_var = ctk.StringVar(value="1")
        self.chk_backup = ctk.CTkCheckBox(
            container, text="Automatically backup database to backups/ folder",
            variable=self.chk_backup_var, onvalue="1", offvalue="0",
            font=FONTS["body_md"]
        )
        self.chk_backup.pack(anchor="w", padx=15, pady=(0, 20))

        # Bottom Buttons
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Cancel (Esc)", fg_color=COLORS["border"],
            text_color=COLORS["text_primary"], height=46, font=FONTS["body_md"],
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_bar, text="Finalize Day Close", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            height=46, font=FONTS["title_sm"], command=self._finalize_eod
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _row(self, parent, label: str, value: str, bold: bool = False):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=5)
        f = FONTS["title_sm"] if bold else FONTS["body_md"]
        c = COLORS["text_primary"] if bold else COLORS["text_secondary"]
        ctk.CTkLabel(r, text=label, font=f, text_color=c).pack(side="left")
        ctk.CTkLabel(r, text=value, font=FONTS["mono_bold"] if bold else FONTS["mono"], text_color=COLORS["primary"] if bold else COLORS["text_primary"]).pack(side="right")

    def _on_cash_changed(self, event=None):
        val_str = self.entry_actual.get().strip()
        try:
            actual = float(val_str) if val_str else 0.0
            expected = self.eod_data["expected_cash"]
            diff = actual - expected
            if abs(diff) < 0.01:
                self.lbl_diff.configure(text=f"{self.currency} 0.00 (Balanced)", text_color=COLORS["success"])
            elif diff > 0:
                self.lbl_diff.configure(text=f"+{self.currency} {diff:,.2f} (Over)", text_color=COLORS["success"])
            else:
                self.lbl_diff.configure(text=f"{self.currency} {diff:,.2f} (Short)", text_color=COLORS["danger"])
        except ValueError:
            self.lbl_diff.configure(text="Invalid amount", text_color=COLORS["danger"])

    def _finalize_eod(self):
        val_str = self.entry_actual.get().strip()
        try:
            actual = float(val_str) if val_str else self.eod_data["expected_cash"]
        except ValueError:
            return

        expected = self.eod_data["expected_cash"]
        diff = actual - expected
        notes = self.entry_notes.get().strip()

        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        report_id = EODModel.save_eod_report(
            user_id=user_id,
            total_sales=self.eod_data["total_sales"],
            total_orders=self.eod_data["total_orders"],
            expected_cash=expected,
            actual_cash=actual,
            difference=diff,
            notes=notes
        )

        ActivityModel.log(user_id, "EOD_CLOSE", f"Completed Day Close. Actual: {actual}, Expected: {expected}, Diff: {diff}")

        # Trigger auto backup if selected
        if self.chk_backup_var.get() == "1":
            SettingsController.backup_database()

        self.destroy()
        if self.on_close_complete:
            self.on_close_complete(report_id)
