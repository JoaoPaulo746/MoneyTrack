"""Paleta e tipografia do MoneyTrack."""
NAVY = "#0B1F3A"        # identidade / menu lateral
NAVY_LIGHT = "#173A66"
BG = "#F3F5F9"          # fundo
CARD = "#FFFFFF"
BORDER = "#E3E8EF"
GREEN = "#16A34A"       # receitas / positivo
GREEN_DARK = "#15803D"
GREEN_BG = "#DCFCE7"
RED = "#DC2626"         # despesas / alerta
RED_DARK = "#B91C1C"
RED_BG = "#FEE2E2"
BLUE = "#2563EB"
TEXT = "#0F172A"
MUTED = "#6B7280"       # informação secundária

_fonts = {}


def font(size=13, weight="normal"):
    """Fonte CustomTkinter em cache (só pode ser criada após a janela principal existir)."""
    import customtkinter as ctk
    key = (size, weight)
    if key not in _fonts:
        _fonts[key] = ctk.CTkFont(size=size, weight=weight)
    return _fonts[key]
