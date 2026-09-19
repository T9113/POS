"""
Design system, theme tokens, and typography for SwiftPOS.
"""
import customtkinter as ctk

# Color Tokens (tuple format for CustomTkinter: (light_color, dark_color))
COLORS = {
    "bg_main": ("#F1F5F9", "#0B132B"),
    "bg_surface": ("#FFFFFF", "#1C2541"),
    "bg_sidebar": ("#FFFFFF", "#0B132B"),
    "bg_card": ("#FFFFFF", "#1E293B"),
    "bg_input": ("#F8FAFC", "#0F172A"),
    "bg_hover": ("#E2E8F0", "#334155"),
    "border": ("#CBD5E1", "#334155"),
    
    "primary": ("#2563EB", "#3B82F6"),
    "primary_hover": ("#1D4ED8", "#2563EB"),
    "primary_subtle": ("#EFF6FF", "#172554"),
    
    "success": ("#10B981", "#10B981"),
    "success_hover": ("#059669", "#059669"),
    "success_subtle": ("#ECFDF5", "#064E3B"),

    "danger": ("#EF4444", "#EF4444"),
    "danger_hover": ("#DC2626", "#DC2626"),
    "danger_subtle": ("#FEF2F2", "#450A0A"),

    "warning": ("#F59E0B", "#F59E0B"),
    "warning_hover": ("#D97706", "#D97706"),
    "warning_subtle": ("#FFFBEB", "#451A03"),

    "text_primary": ("#0F172A", "#F8FAFC"),
    "text_secondary": ("#475569", "#94A3B8"),
    "text_muted": ("#94A3B8", "#64748B"),
    "text_on_primary": ("#FFFFFF", "#FFFFFF")
}

# Typography Definitions
FONTS = {
    "title_xl": ("Segoe UI", 24, "bold"),
    "title_lg": ("Segoe UI", 18, "bold"),
    "title_md": ("Segoe UI", 15, "bold"),
    "title_sm": ("Segoe UI", 13, "bold"),
    "body_lg": ("Segoe UI", 13),
    "body_md": ("Segoe UI", 12),
    "body_sm": ("Segoe UI", 10),
    "mono": ("Consolas", 11),
    "mono_bold": ("Consolas", 12, "bold"),
    "stat_value": ("Segoe UI", 22, "bold")
}

def apply_theme(mode: str = "dark"):
    """Set global appearance mode ('dark' or 'light')."""
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")
