"""Modelo de meta financeira (informativa: não altera o saldo)."""
import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from models.money import from_cents


@dataclass
class Goal:
    id: int
    name: str
    target_cents: int
    current_cents: int
    created_at: str
    deadline: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Goal":
        return cls(id=row["id"], name=row["name"], target_cents=row["target_cents"],
                   current_cents=row["current_cents"], created_at=row["created_at"],
                   deadline=row["deadline"])

    @property
    def target(self) -> Decimal:
        return from_cents(self.target_cents)

    @property
    def current(self) -> Decimal:
        return from_cents(self.current_cents)

    @property
    def remaining(self) -> Decimal:
        return max(self.target - self.current, Decimal("0.00"))

    @property
    def progress(self) -> float:
        """Progresso percentual limitado a 100."""
        if self.target_cents <= 0:
            return 0.0
        return min(100.0, self.current_cents * 100.0 / self.target_cents)

    @property
    def completed(self) -> bool:
        return self.current_cents >= self.target_cents

    @property
    def days_left(self) -> Optional[int]:
        if not self.deadline:
            return None
        return (date.fromisoformat(self.deadline) - date.today()).days

    @property
    def monthly_needed(self) -> Optional[Decimal]:
        """Quanto guardar por mês para atingir a meta no prazo."""
        days = self.days_left
        if days is None or days <= 0 or self.completed:
            return None
        months = max(1, math.ceil(days / 30))
        return (self.remaining / months).quantize(Decimal("0.01"))
