"""
Design system, theme tokens, and typography for SwiftPOS.
Slate & Indigo Commercial POS Theme.
"""
import customtkinter as ctk

class ColorDict(dict):
    def __missing__(self, key):
        return ("#0F172A", "#E2E8F0")

class FontDict(dict):
    def __missing__(self, key):
        return ("Segoe UI", 13)

# Color Tokens: tuple format (light_mode_color, dark_mode_color)
COLORS = ColorDict({
    # App shell & surfaces
    "bg_main": ("#F8F9FB", "#0F1117"),
    "bg_surface": ("#FFFFFF", "#1A1D27"),
    "bg_surface_raised": ("#FFFFFF", "#222633"),
    "bg_card": ("#FFFFFF", "#1A1D27"),
    "bg_card_hover": ("#F8FAFC", "#262B3A"),
    "bg_hover": ("#F1F5F9", "#262B3A"),
    
    # Sidebar: ALWAYS dark slate (#1E293B) regardless of light/dark mode
    "bg_sidebar": ("#1E293B", "#0B0E14"),
    "sidebar_bg": ("#1E293B", "#0B0E14"),
    "sidebar_text": ("#94A3B8", "#94A3B8"),
    "sidebar_hover": ("#334155", "#1E2430"),
    "sidebar_active_bg": ("#334155", "#1E2430"),
    "sidebar_active_text": ("#FFFFFF", "#FFFFFF"),
    "sidebar_indicator": ("#6366F1", "#6366F1"),
    "sidebar_active_indicator": ("#6366F1", "#6366F1"), # 3px indigo left indicator

    # Input fields
    "bg_input": ("#F8F9FB", "#1A1D27"),
    "border_input": ("#E2E8F0", "#2A2F3D"),
    "border_input_focus": ("#6366F1", "#6366F1"),
    
    # Borders & Dividers
    "border": ("#E2E8F0", "#2A2F3D"),
    "border_subtle": ("#F1F5F9", "#1E2330"),

    # Typography colors
    "text_primary": ("#0F172A", "#E2E8F0"),
    "text_secondary": ("#475569", "#8892A6"),
    "text_muted": ("#94A3B8", "#5A6478"),
    "text_on_dark": ("#E2E8F0", "#E2E8F0"),
    "text_on_primary": ("#FFFFFF", "#FFFFFF"),

    # Accent (Indigo - reserved strictly for primary action & active states)
    "accent": ("#4F46E5", "#6366F1"),
    "primary": ("#4F46E5", "#6366F1"),
    "primary_hover": ("#4338CA", "#4F46E5"),
    "primary_subtle": ("#EEF2FF", "#1E1E38"),

    # Success (stock ok, payment complete)
    "success": ("#059669", "#10B981"),
    "success_hover": ("#047857", "#059669"),
    "success_subtle": ("#ECFDF5", "#063D2E"),

    # Warning (low stock, held orders)
    "warning": ("#D97706", "#F59E0B"),
    "warning_hover": ("#B45309", "#D97706"),
    "warning_subtle": ("#FFFBEB", "#382305"),

    # Danger (delete, void, refund, negative values)
    "danger": ("#DC2626", "#EF4444"),
    "danger_hover": ("#B91C1C", "#DC2626"),
    "danger_subtle": ("#FEF2F2", "#3B1111"),

    # Favorites gold
    "gold": ("#D97706", "#FBBF24")
})

# Typography Hierarchy (Segoe UI for system, Consolas for tabular digits)
FONTS = FontDict({
    "grand_total": ("Consolas", 28, "bold"),
    "title_xl": ("Segoe UI", 24, "bold"),
    "title_lg": ("Segoe UI", 18, "bold"),
    "title_md": ("Segoe UI", 14, "bold"),
    "title_sm": ("Segoe UI", 13, "bold"),
    "sidebar": ("Segoe UI", 12),
    "body_lg": ("Segoe UI", 13),
    "body_md": ("Segoe UI", 13),
    "body_sm": ("Segoe UI", 11),
    "mono": ("Consolas", 11),
    "mono_bold": ("Consolas", 12, "bold"),
    "mono_lg": ("Consolas", 15, "bold"),
    "stat_value": ("Consolas", 22, "bold")
})

# Spacing & Radii Design Tokens
RADII = {
    "card": 8,
    "panel": 8,
    "button": 6,
    "input": 6,
    "badge": 4,
    "pill": 16,
    "sidebar": 0
}

def _apply_component_patches():
    """Patches CustomTkinter SegmentedButton and Tabview for premium interactive styling."""
    if getattr(ctk.CTkSegmentedButton, "_swiftpos_patched", False):
        return
    ctk.CTkSegmentedButton._swiftpos_patched = True

    # 1. Patch dynamic text color switching on selection/unselection
    orig_select = ctk.CTkSegmentedButton._select_button_by_value
    orig_unselect = ctk.CTkSegmentedButton._unselect_button_by_value

    def custom_select(self, value):
        orig_select(self, value)
        if value in self._buttons_dict:
            # Active pill text is always high-contrast crisp white on Indigo background
            self._buttons_dict[value].configure(text_color=("#FFFFFF", "#FFFFFF"))

    def custom_unselect(self, value):
        orig_unselect(self, value)
        if value in self._buttons_dict:
            # Inactive tab text restores to elegant slate text
            self._buttons_dict[value].configure(text_color=self._sb_text_color)

    ctk.CTkSegmentedButton._select_button_by_value = custom_select
    ctk.CTkSegmentedButton._unselect_button_by_value = custom_unselect

    # 2. Modern Tabview proportions
    ctk.CTkTabview._button_height = 34
    ctk.CTkTabview._segmented_button_border_width = 2

    # 3. Patch Tabview.__init__ to supply clean fonts and corner radius
    orig_tabview_init = ctk.CTkTabview.__init__
    def custom_tabview_init(self, *args, **kwargs):
        if "segmented_button_font" not in kwargs or kwargs["segmented_button_font"] is None:
            kwargs["segmented_button_font"] = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        if "corner_radius" not in kwargs or kwargs["corner_radius"] is None:
            kwargs["corner_radius"] = 8
        orig_tabview_init(self, *args, **kwargs)
    ctk.CTkTabview.__init__ = custom_tabview_init

    # 4. Patch SegmentedButton.__init__ to supply clean fonts and corner radius
    orig_sb_init = ctk.CTkSegmentedButton.__init__
    def custom_sb_init(self, *args, **kwargs):
        if "font" not in kwargs or kwargs["font"] is None:
            kwargs["font"] = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        if "corner_radius" not in kwargs or kwargs["corner_radius"] is None:
            kwargs["corner_radius"] = 8
        orig_sb_init(self, *args, **kwargs)
    ctk.CTkSegmentedButton.__init__ = custom_sb_init


def apply_theme(mode: str = "light"):
    """Applies theme mode ('light' or 'dark') and configures Slate & Indigo theme tokens."""
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")

    # Overwrite ThemeManager dictionary entries with Slate & Indigo commercial theme tokens
    tm = ctk.ThemeManager.theme

    # 1. CTkSegmentedButton - modern slate track with vibrant indigo pill
    if "CTkSegmentedButton" in tm:
        tm["CTkSegmentedButton"]["fg_color"] = ["#F1F5F9", "#1E2430"]
        tm["CTkSegmentedButton"]["unselected_color"] = ["#F1F5F9", "#1E2430"]
        tm["CTkSegmentedButton"]["unselected_hover_color"] = ["#E2E8F0", "#2B3545"]
        tm["CTkSegmentedButton"]["selected_color"] = ["#4F46E5", "#6366F1"]
        tm["CTkSegmentedButton"]["selected_hover_color"] = ["#4338CA", "#4F46E5"]
        tm["CTkSegmentedButton"]["text_color"] = ["#475569", "#94A3B8"]
        tm["CTkSegmentedButton"]["text_color_disabled"] = ["#94A3B8", "#64748B"]
        tm["CTkSegmentedButton"]["corner_radius"] = 8
        tm["CTkSegmentedButton"]["border_width"] = 2

    # 2. CTkButton - primary indigo accent
    if "CTkButton" in tm:
        tm["CTkButton"]["fg_color"] = ["#4F46E5", "#6366F1"]
        tm["CTkButton"]["hover_color"] = ["#4338CA", "#4F46E5"]
        tm["CTkButton"]["text_color"] = ["#FFFFFF", "#FFFFFF"]
        tm["CTkButton"]["corner_radius"] = 6

    # 3. CTkOptionMenu & CTkComboBox
    if "CTkOptionMenu" in tm:
        tm["CTkOptionMenu"]["fg_color"] = ["#4F46E5", "#6366F1"]
        tm["CTkOptionMenu"]["button_color"] = ["#4338CA", "#4F46E5"]
        tm["CTkOptionMenu"]["button_hover_color"] = ["#3730A3", "#4338CA"]
        tm["CTkOptionMenu"]["text_color"] = ["#FFFFFF", "#FFFFFF"]
        tm["CTkOptionMenu"]["corner_radius"] = 6

    if "CTkComboBox" in tm:
        tm["CTkComboBox"]["border_color"] = ["#CBD5E1", "#334155"]
        tm["CTkComboBox"]["button_color"] = ["#E2E8F0", "#2A2F3D"]
        tm["CTkComboBox"]["button_hover_color"] = ["#CBD5E1", "#334155"]
        tm["CTkComboBox"]["fg_color"] = ["#FFFFFF", "#1A1D27"]
        tm["CTkComboBox"]["text_color"] = ["#0F172A", "#E2E8F0"]
        tm["CTkComboBox"]["corner_radius"] = 6
        tm["CTkComboBox"]["border_width"] = 1

    # 4. CTkEntry & CTkTextbox
    if "CTkEntry" in tm:
        tm["CTkEntry"]["border_color"] = ["#CBD5E1", "#334155"]
        tm["CTkEntry"]["fg_color"] = ["#FFFFFF", "#1A1D27"]
        tm["CTkEntry"]["text_color"] = ["#0F172A", "#E2E8F0"]
        tm["CTkEntry"]["placeholder_text_color"] = ["#94A3B8", "#5A6478"]
        tm["CTkEntry"]["corner_radius"] = 6
        tm["CTkEntry"]["border_width"] = 1

    if "CTkTextbox" in tm:
        tm["CTkTextbox"]["border_color"] = ["#CBD5E1", "#334155"]
        tm["CTkTextbox"]["fg_color"] = ["#FFFFFF", "#1A1D27"]
        tm["CTkTextbox"]["text_color"] = ["#0F172A", "#E2E8F0"]
        tm["CTkTextbox"]["corner_radius"] = 6
        tm["CTkTextbox"]["border_width"] = 1

    # 5. CTkSwitch & CTkCheckBox
    if "CTkSwitch" in tm:
        tm["CTkSwitch"]["progress_color"] = ["#4F46E5", "#6366F1"]
        tm["CTkSwitch"]["fg_color"] = ["#CBD5E1", "#334155"]
        tm["CTkSwitch"]["button_color"] = ["#FFFFFF", "#FFFFFF"]
        tm["CTkSwitch"]["button_hover_color"] = ["#F1F5F9", "#E2E8F0"]

    if "CTkCheckBox" in tm:
        tm["CTkCheckBox"]["fg_color"] = ["#4F46E5", "#6366F1"]
        tm["CTkCheckBox"]["border_color"] = ["#CBD5E1", "#334155"]
        tm["CTkCheckBox"]["hover_color"] = ["#4338CA", "#4F46E5"]
        tm["CTkCheckBox"]["checkmark_color"] = ["#FFFFFF", "#FFFFFF"]

    # 6. CTkProgressBar & CTkScrollbar
    if "CTkProgressBar" in tm:
        tm["CTkProgressBar"]["progress_color"] = ["#4F46E5", "#6366F1"]
        tm["CTkProgressBar"]["fg_color"] = ["#E2E8F0", "#2A2F3D"]

    if "CTkScrollbar" in tm:
        tm["CTkScrollbar"]["button_color"] = ["#CBD5E1", "#334155"]
        tm["CTkScrollbar"]["button_hover_color"] = ["#94A3B8", "#475569"]

    # 7. DropdownMenu
    if "DropdownMenu" in tm:
        tm["DropdownMenu"]["fg_color"] = ["#FFFFFF", "#1A1D27"]
        tm["DropdownMenu"]["hover_color"] = ["#F1F5F9", "#262B3A"]
        tm["DropdownMenu"]["text_color"] = ["#0F172A", "#E2E8F0"]

    # 8. Apply dynamic component patches
    _apply_component_patches()

