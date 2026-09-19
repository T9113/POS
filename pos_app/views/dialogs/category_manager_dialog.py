import customtkinter as ctk
from pos_app.views.theme import COLORS, FONTS
from pos_app.models.category_model import CategoryModel

class CategoryManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_changed=None):
        super().__init__(parent)
        self.on_changed = on_changed
        self.title("Category Management")
        self.geometry("540x600")
        self.transient(parent)
        self.grab_set()

        self.editing_cat_id = None

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + max(0, (pw - 540) // 2)
        y = py + max(0, (ph - 600) // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_surface"], corner_radius=12)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 8))
        ctk.CTkLabel(hdr, text="📁 Category Management", font=FONTS["title_md"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(
            hdr, text="Create, rename, re-order, and manage product categories.",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Add / Edit Form Box
        self.form_box = ctk.CTkFrame(container, fg_color=COLORS["bg_input"], corner_radius=8)
        self.form_box.pack(fill="x", padx=16, pady=(0, 12))

        self.lbl_form_title = ctk.CTkLabel(
            self.form_box, text="Add New Category",
            font=FONTS["title_sm"], text_color=COLORS["primary"]
        )
        self.lbl_form_title.pack(anchor="w", padx=12, pady=(10, 6))

        inputs_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        inputs_row.pack(fill="x", padx=12, pady=(0, 10))

        self.entry_name = ctk.CTkEntry(
            inputs_row, placeholder_text="Category Name (e.g. Beverages, Snacks)",
            height=36, font=FONTS["body_md"]
        )
        self.entry_name.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_name.bind("<Return>", lambda e: self._save_category())

        self.entry_order = ctk.CTkEntry(
            inputs_row, placeholder_text="Sort (0, 1...)",
            width=80, height=36, font=FONTS["body_md"]
        )
        self.entry_order.pack(side="left", padx=(0, 8))
        self.entry_order.insert(0, "0")

        self.btn_save = ctk.CTkButton(
            inputs_row, text="➕ Add", width=80, height=36,
            font=FONTS["title_sm"], fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], text_color="#FFFFFF",
            command=self._save_category
        )
        self.btn_save.pack(side="left")

        self.btn_cancel_edit = ctk.CTkButton(
            inputs_row, text="Cancel", width=65, height=36,
            font=FONTS["body_sm"], fg_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"],
            command=self._reset_form
        )
        # Hidden initially
        self.btn_cancel_edit.pack_forget()

        self.lbl_error = ctk.CTkLabel(self.form_box, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self.lbl_error.pack(anchor="w", padx=12, pady=(0, 4))

        # Categories List
        list_header = ctk.CTkFrame(container, fg_color=COLORS["bg_input"], corner_radius=6, height=34)
        list_header.pack(fill="x", padx=16, pady=(0, 4))
        list_header.pack_propagate(False)

        ctk.CTkLabel(list_header, text="Category Name", font=FONTS["title_sm"], text_color=COLORS["text_primary"], width=210, anchor="w").pack(side="left", padx=12)
        ctk.CTkLabel(list_header, text="Order", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=60, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(list_header, text="Status", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=70, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(list_header, text="Actions", font=FONTS["title_sm"], text_color=COLORS["text_secondary"], width=100, anchor="e").pack(side="right", padx=12)

        self.cats_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.cats_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Bottom Close Button
        btn_close = ctk.CTkButton(
            container, text="Done (Close)", font=FONTS["body_md"],
            fg_color=COLORS["bg_hover"], text_color=COLORS["text_primary"],
            height=38, command=self.destroy
        )
        btn_close.pack(fill="x", padx=16, pady=(0, 10))

        self._refresh_list()

    def _refresh_list(self):
        for w in self.cats_scroll.winfo_children():
            w.destroy()

        cats = CategoryModel.list_all(active_only=False)
        if not cats:
            ctk.CTkLabel(
                self.cats_scroll, text="No categories found. Add your first category above.",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"]
            ).pack(pady=30)
            return

        for c in cats:
            row = ctk.CTkFrame(self.cats_scroll, fg_color=COLORS["bg_card"], corner_radius=6, height=42)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            is_active = bool(c.get("is_active", 1))
            name_color = COLORS["text_primary"] if is_active else COLORS["text_muted"]

            ctk.CTkLabel(row, text=c["name"], font=FONTS["body_lg"], text_color=name_color, width=210, anchor="w").pack(side="left", padx=12)
            ctk.CTkLabel(row, text=str(c.get("sort_order", 0)), font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=60, anchor="w").pack(side="left", padx=5)

            status_txt = "Active" if is_active else "Inactive"
            status_col = COLORS["success"] if is_active else COLORS["danger"]
            ctk.CTkLabel(row, text=status_txt, font=FONTS["body_sm"], text_color=status_col, width=70, anchor="w").pack(side="left", padx=5)

            # Action buttons
            actions_box = ctk.CTkFrame(row, fg_color="transparent")
            actions_box.pack(side="right", padx=10)

            # Edit
            ctk.CTkButton(
                actions_box, text="✏️", width=30, height=28,
                font=("Segoe UI", 11), fg_color=COLORS["bg_hover"],
                text_color=COLORS["text_primary"],
                command=lambda cat=c: self._start_edit(cat)
            ).pack(side="left", padx=2)

            # Delete / Deactivate
            if is_active:
                ctk.CTkButton(
                    actions_box, text="✕", width=30, height=28,
                    font=("Segoe UI", 11, "bold"), fg_color=COLORS["danger_subtle"],
                    text_color=COLORS["danger"],
                    command=lambda cid=c["id"]: self._delete_category(cid)
                ).pack(side="left", padx=2)

    def _start_edit(self, cat: dict):
        self.editing_cat_id = cat["id"]
        self.lbl_form_title.configure(text=f"Edit Category: {cat['name']}")
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, cat["name"])
        self.entry_order.delete(0, "end")
        self.entry_order.insert(0, str(cat.get("sort_order", 0)))
        self.btn_save.configure(text="💾 Save")
        self.btn_cancel_edit.pack(side="left", padx=(4, 0))
        self.entry_name.focus()

    def _reset_form(self):
        self.editing_cat_id = None
        self.lbl_form_title.configure(text="Add New Category")
        self.entry_name.delete(0, "end")
        self.entry_order.delete(0, "end")
        self.entry_order.insert(0, "0")
        self.btn_save.configure(text="➕ Add")
        self.btn_cancel_edit.pack_forget()
        self.lbl_error.configure(text="")

    def _save_category(self):
        name = self.entry_name.get().strip()
        if not name:
            self.lbl_error.configure(text="Category name cannot be empty.")
            return

        try:
            sort_order = int(self.entry_order.get().strip() or "0")
        except ValueError:
            sort_order = 0

        self.lbl_error.configure(text="")

        if self.editing_cat_id is not None:
            CategoryModel.update(self.editing_cat_id, name=name, sort_order=sort_order, is_active=1)
        else:
            CategoryModel.create(name=name, sort_order=sort_order)

        self._reset_form()
        self._refresh_list()
        if self.on_changed:
            self.on_changed()

    def _delete_category(self, cat_id: int):
        CategoryModel.delete(cat_id)
        self._refresh_list()
        if self.on_changed:
            self.on_changed()
