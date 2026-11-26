"""Utilitários monetários.

Os valores são guardados no banco como INTEIROS em centavos (sem erro de ponto
flutuante) e manipulados no código com `Decimal`.
"""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def to_cents(value: Decimal) -> int:
    """Converte Decimal (reais) para centavos inteiros."""
    return int((value.quantize(CENT, rounding=ROUND_HALF_UP) * 100).to_integral_value())


def from_cents(cents) -> Decimal:
    """Converte centavos inteiros para Decimal (reais)."""
    return (Decimal(int(cents)) / Decimal(100)).quantize(CENT)


def format_brl(value) -> str:
    """Formata Decimal/int/float como moeda brasileira: R$ 1.234,56."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    value = value.quantize(CENT, rounding=ROUND_HALF_UP)
    sign = "-" if value < 0 else ""
    txt = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}R$ {txt}"


def format_cents(cents) -> str:
    return format_brl(from_cents(cents))
