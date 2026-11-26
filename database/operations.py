"""Operações de banco (CRUD). Todas as consultas são PARAMETRIZADAS (sem SQL Injection)."""
from typing import List, Optional

import pandas as pd

from database.connection import db_session, get_connection
from models.category import Category
from models.goal import Goal
from models.transaction import Transaction

_TX_SELECT = """
    SELECT t.id, t.description, t.amount_cents, t.type, t.category_id,
           t.transaction_date, t.notes,
           c.name AS category_name, c.color AS category_color, c.icon AS category_icon
    FROM transactions t
    JOIN categories c ON c.id = t.category_id
"""

# Lista branca: o nome da coluna de ordenação nunca vem direto do usuário.
_ORDER_COLUMNS = {"date": "t.transaction_date", "amount": "t.amount_cents"}


def _period_clauses(date_from, date_to, clauses, params):
    if date_from:
        clauses.append("t.transaction_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("t.transaction_date <= ?")
        params.append(date_to)


# ----------------------------------------------------------------- categorias
def list_categories(type_: Optional[str] = None) -> List[Category]:
    sql = """SELECT c.id, c.name, c.type, c.color, c.icon, COUNT(t.id) AS usage
             FROM categories c LEFT JOIN transactions t ON t.category_id = c.id"""
    params: list = []
    if type_:
        sql += " WHERE c.type = ?"
        params.append(type_)
    sql += " GROUP BY c.id ORDER BY c.name COLLATE NOCASE"
    with db_session() as conn:
        return [Category.from_row(r) for r in conn.execute(sql, params)]


def get_category(category_id: int) -> Optional[Category]:
    with db_session() as conn:
        row = conn.execute(
            """SELECT c.id, c.name, c.type, c.color, c.icon,
                      (SELECT COUNT(*) FROM transactions WHERE category_id = c.id) AS usage
               FROM categories c WHERE c.id = ?""", (category_id,)).fetchone()
    return Category.from_row(row) if row else None


def insert_category(name, type_, color, icon) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, type, color, icon) VALUES (?, ?, ?, ?)",
            (name, type_, color, icon))
        return cur.lastrowid


def update_category(category_id, name, type_, color, icon) -> None:
    with db_session() as conn:
        conn.execute(
            "UPDATE categories SET name = ?, type = ?, color = ?, icon = ? WHERE id = ?",
            (name, type_, color, icon, category_id))


def delete_category(category_id) -> None:
    with db_session() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def count_transactions_of_category(category_id) -> int:
    with db_session() as conn:
        return conn.execute("SELECT COUNT(*) FROM transactions WHERE category_id = ?",
                            (category_id,)).fetchone()[0]


# --------------------------------------------------------------- movimentações
def insert_transaction(description, amount_cents, type_, category_id, tx_date, notes="") -> int:
    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO transactions
               (description, amount_cents, type, category_id, transaction_date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (description, amount_cents, type_, category_id, tx_date, notes))
        return cur.lastrowid


def update_transaction(tx_id, description, amount_cents, type_, category_id, tx_date, notes="") -> int:
    with db_session() as conn:
        cur = conn.execute(
            """UPDATE transactions
               SET description = ?, amount_cents = ?, type = ?, category_id = ?,
                   transaction_date = ?, notes = ?
               WHERE id = ?""",
            (description, amount_cents, type_, category_id, tx_date, notes, tx_id))
        return cur.rowcount


def delete_transaction(tx_id) -> int:
    with db_session() as conn:
        return conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,)).rowcount


def get_transaction(tx_id) -> Optional[Transaction]:
    with db_session() as conn:
        row = conn.execute(_TX_SELECT + " WHERE t.id = ?", (tx_id,)).fetchone()
    return Transaction.from_row(row) if row else None


def query_transactions(search=None, type_=None, category_id=None, date_from=None,
                       date_to=None, order_by="date", descending=True,
                       limit=None) -> List[Transaction]:
    clauses: list = []
    params: list = []
    if search:
        escaped = search.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses.append("PYLOWER(t.description) LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")
    if type_:
        clauses.append("t.type = ?")
        params.append(type_)
    if category_id:
        clauses.append("t.category_id = ?")
        params.append(category_id)
    _period_clauses(date_from, date_to, clauses, params)

    sql = _TX_SELECT
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    column = _ORDER_COLUMNS.get(order_by, "t.transaction_date")
    direction = "DESC" if descending else "ASC"
    sql += f" ORDER BY {column} {direction}, t.id {direction}"
    if limit:
        sql += " LIMIT ?"
        params.append(int(limit))
    with db_session() as conn:
        return [Transaction.from_row(r) for r in conn.execute(sql, params)]


def totals(date_from=None, date_to=None) -> dict:
    """Soma de receitas e despesas (em centavos) direto do banco."""
    clauses: list = []
    params: list = []
    _period_clauses(date_from, date_to, clauses, params)
    sql = "SELECT t.type AS type, COALESCE(SUM(t.amount_cents), 0) AS total, COUNT(*) AS n FROM transactions t"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " GROUP BY t.type"
    result = {"receita": 0, "despesa": 0, "count": 0}
    with db_session() as conn:
        for row in conn.execute(sql, params):
            result[row["type"]] = row["total"]
            result["count"] += row["n"]
    return result


def transactions_dataframe(date_from=None, date_to=None) -> pd.DataFrame:
    """Movimentações em um DataFrame do Pandas (base das análises)."""
    clauses: list = []
    params: list = []
    _period_clauses(date_from, date_to, clauses, params)
    sql = """SELECT t.id, t.description, t.amount_cents, t.type, t.transaction_date,
                    c.name AS category, c.color AS color
             FROM transactions t JOIN categories c ON c.id = t.category_id"""
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY t.transaction_date, t.id"
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


# ----------------------------------------------------------------------- metas
def list_goals() -> List[Goal]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM goals ORDER BY created_at DESC, id DESC").fetchall()
    return [Goal.from_row(r) for r in rows]


def get_goal(goal_id) -> Optional[Goal]:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return Goal.from_row(row) if row else None


def insert_goal(name, target_cents, current_cents, deadline) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO goals (name, target_cents, current_cents, deadline) VALUES (?, ?, ?, ?)",
            (name, target_cents, current_cents, deadline))
        return cur.lastrowid


def update_goal(goal_id, name, target_cents, current_cents, deadline) -> int:
    with db_session() as conn:
        return conn.execute(
            """UPDATE goals SET name = ?, target_cents = ?, current_cents = ?, deadline = ?
               WHERE id = ?""", (name, target_cents, current_cents, deadline, goal_id)).rowcount


def delete_goal(goal_id) -> int:
    with db_session() as conn:
        return conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,)).rowcount
