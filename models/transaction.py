"""Modelo de movimentação financeira."""
from dataclasses import dataclass
from decimal import Decimal

from models.money import from_cents


@dataclass
class Transaction:
    id: int
    description: str
    amount_cents: int
    type: str
    category_id: int
    transaction_date: str  # ISO: AAAA-MM-DD
    notes: str = ""
    category_name: str = ""
    category_color: str = "#64748B"
    category_icon: str = ""

    @classmethod
    def from_row(cls, row) -> "Transaction":
        keys = row.keys()
        return cls(
            id=row["id"], description=row["description"],
            amount_cents=row["amount_cents"], type=row["type"],
            category_id=row["category_id"],
            transaction_date=row["transaction_date"], notes=row["notes"] or "",
            category_name=row["category_name"] if "category_name" in keys else "",
            category_color=row["category_color"] if "category_color" in keys else "#64748B",
            category_icon=row["category_icon"] if "category_icon" in keys else "",
        )

    @property
    def amount(self) -> Decimal:
        return from_cents(self.amount_cents)
