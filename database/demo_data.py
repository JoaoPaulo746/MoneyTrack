"""Dados de demonstração — gravados SOMENTE no banco separado (moneytrack_demo.db)."""
import random
from datetime import date

from database import operations as ops
from database.connection import db_session
from models.money import to_cents
from decimal import Decimal


def _month_shift(today: date, back: int) -> tuple:
    y, m = today.year, today.month - back
    while m <= 0:
        m, y = m + 12, y - 1
    return y, m


def seed_demo_data() -> None:
    """Gera ~4 meses de movimentações realistas (sempre as mesmas, seed fixa)."""
    rnd = random.Random(2026)
    cats = {(c.name, c.type): c.id for c in ops.list_categories()}
    today = date.today()

    def add(desc, value, type_, cat, y, m, d, notes=""):
        d = min(d, 28)
        if date(y, m, d) > today and (y, m) == (today.year, today.month):
            d = max(1, min(d, today.day))        # não cria movimentos após hoje
        ops.insert_transaction(desc, to_cents(Decimal(str(value))), type_,
                               cats[(cat, type_)], date(y, m, d).isoformat(), notes)

    for back in range(3, -1, -1):
        y, m = _month_shift(today, back)
        add("Salário - estágio", 1600, "receita", "Salário", y, m, 5)
        if back != 2:
            add("Projeto freelance", rnd.choice([250, 320, 400]), "receita", "Freelance", y, m, 18)
        add("Aluguel / contribuição moradia", 450, "despesa", "Moradia", y, m, 8)
        add("Mensalidade curso", 180, "despesa", "Educação", y, m, 10)
        add("Streaming", 39.9, "despesa", "Assinaturas", y, m, 12)
        for i in range(4):
            add(rnd.choice(["Supermercado", "Lanchonete", "Padaria", "Almoço"]),
                round(rnd.uniform(35, 140) + (60 if back == 0 else 0), 2),
                "despesa", "Alimentação", y, m, 3 + i * 7)
        for i in range(3):
            add("Transporte (ônibus/app)", round(rnd.uniform(20, 70), 2), "despesa", "Transporte", y, m, 4 + i * 9)
        add(rnd.choice(["Cinema", "Show", "Jogos", "Passeio"]),
            round(rnd.uniform(40, 120) + (90 if back == 0 else 0), 2), "despesa", "Lazer", y, m, 20)
        if back in (0, 2):
            add("Roupas", round(rnd.uniform(90, 220), 2), "despesa", "Compras", y, m, 22)
        if back == 1:
            add("Consulta / farmácia", 95.5, "despesa", "Saúde", y, m, 15)

    with db_session() as conn:
        conn.executemany(
            "INSERT INTO goals (name, target_cents, current_cents, deadline) VALUES (?, ?, ?, ?)",
            [("Comprar um computador", 450000, 135000, date(today.year + 1, 6, 30).isoformat()),
             ("Reserva de emergência", 300000, 60000, None),
             ("Viagem de formatura", 200000, 200000, date(today.year + 1, 1, 31).isoformat())])
