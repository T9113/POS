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

def apply_theme(mode: str = "light"):
    """Applies theme mode ('light' or 'dark')."""
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")
