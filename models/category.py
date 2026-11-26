"""Modelo de categoria."""
from dataclasses import dataclass

INCOME = "receita"
EXPENSE = "despesa"
TYPES = (INCOME, EXPENSE)


@dataclass
class Category:
    id: int
    name: str
    type: str
    color: str = "#64748B"
    icon: str = ""
    usage: int = 0  # quantidade de movimentações vinculadas

    @classmethod
    def from_row(cls, row) -> "Category":
        keys = row.keys()
        return cls(
            id=row["id"], name=row["name"], type=row["type"],
            color=row["color"], icon=row["icon"] or "",
            usage=row["usage"] if "usage" in keys else 0,
        )

    @property
    def label(self) -> str:
        return f"{self.name} · {self.type.capitalize()}"
