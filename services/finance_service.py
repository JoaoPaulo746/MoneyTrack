"""Regras de negócio do MoneyTrack (a interface só chama estas funções)."""
import calendar
import functools
import sqlite3
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from database import operations as ops
from models.category import Category
from models.goal import Goal
from models.money import from_cents, to_cents
from models.transaction import Transaction
from services import validation_service as vs


class BusinessError(Exception):
    """Violação de regra de negócio, com mensagem amigável."""


def _friendly_db_errors(func):
    """Converte erros do SQLite em mensagens compreensíveis."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.IntegrityError as exc:
            msg = str(exc)
            if "UNIQUE" in msg:
                raise BusinessError("Já existe uma categoria com esse nome para esse tipo.")
            if "FOREIGN KEY" in msg:
                raise BusinessError("Registro vinculado a outros dados; operação não permitida.")
            raise BusinessError(msg)
        except sqlite3.Error as exc:
            raise BusinessError(f"Erro no banco de dados: {exc}")
    return wrapper


# ---------------------------------------------------------------------- períodos
PERIODS = ["Este mês", "Mês anterior", "Últimos 3 meses", "Este ano", "Todo o período"]


def _last_day(d: date) -> date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def period_range(key: str, today: Optional[date] = None):
    """Retorna (data_inicial, data_final) em ISO; (None, None) = sem filtro."""
    today = today or date.today()
    first = today.replace(day=1)
    if key == "Este mês":
        return first.isoformat(), _last_day(first).isoformat()
    if key == "Mês anterior":
        prev_last = first - timedelta(days=1)
        return prev_last.replace(day=1).isoformat(), prev_last.isoformat()
    if key == "Últimos 3 meses":
        y, m = today.year, today.month - 2
        if m <= 0:
            m, y = m + 12, y - 1
        return date(y, m, 1).isoformat(), _last_day(first).isoformat()
    if key == "Este ano":
        return date(today.year, 1, 1).isoformat(), date(today.year, 12, 31).isoformat()
    return None, None


# -------------------------------------------------------------------- categorias
def list_categories(type_: Optional[str] = None) -> List[Category]:
    return ops.list_categories(type_)


@_friendly_db_errors
def create_category(name, type_, color, icon) -> int:
    d = vs.validate_category(name, type_, color, icon)
    return ops.insert_category(d["name"], d["type"], d["color"], d["icon"])


@_friendly_db_errors
def update_category(category_id, name, type_, color, icon) -> None:
    d = vs.validate_category(name, type_, color, icon)
    current = ops.get_category(category_id)
    if current is None:
        raise BusinessError("Categoria não encontrada.")
    if current.usage and current.type != d["type"]:
        raise BusinessError("Não é possível alterar o tipo de uma categoria que já possui movimentações.")
    ops.update_category(category_id, d["name"], d["type"], d["color"], d["icon"])


@_friendly_db_errors
def delete_category(category_id) -> None:
    n = ops.count_transactions_of_category(category_id)
    if n:
        raise BusinessError(
            f"Esta categoria possui {n} movimentação(ões) vinculada(s). "
            "Edite ou exclua essas movimentações antes de remover a categoria.")
    ops.delete_category(category_id)


# ------------------------------------------------------------------ movimentações
def _check_category(category_id: int, type_: str) -> None:
    cat = ops.get_category(category_id)
    if cat is None:
        raise BusinessError("Categoria não encontrada.")
    if cat.type != type_:
        raise BusinessError(f"A categoria '{cat.name}' é de {cat.type} e não pode ser usada em uma {type_}.")


@_friendly_db_errors
def add_transaction(description, amount_text, type_, category_id, date_text, notes="") -> int:
    d = vs.validate_transaction(description, amount_text, type_, category_id, date_text, notes)
    _check_category(d["category_id"], d["type"])
    return ops.insert_transaction(d["description"], to_cents(d["amount"]), d["type"],
                                  d["category_id"], d["transaction_date"], d["notes"])


@_friendly_db_errors
def update_transaction(tx_id, description, amount_text, type_, category_id, date_text, notes="") -> None:
    d = vs.validate_transaction(description, amount_text, type_, category_id, date_text, notes)
    _check_category(d["category_id"], d["type"])
    if ops.update_transaction(tx_id, d["description"], to_cents(d["amount"]), d["type"],
                              d["category_id"], d["transaction_date"], d["notes"]) == 0:
        raise BusinessError("Movimentação não encontrada.")


@_friendly_db_errors
def delete_transaction(tx_id) -> None:
    if ops.delete_transaction(tx_id) == 0:
        raise BusinessError("Movimentação não encontrada.")


def get_transaction(tx_id) -> Optional[Transaction]:
    return ops.get_transaction(tx_id)


def list_transactions(**filters) -> List[Transaction]:
    return ops.query_transactions(**filters)


# ------------------------------------------------------------------------ saldo
def summary(date_from=None, date_to=None) -> dict:
    """Resumo do período. Saldo = Receitas - Despesas, SEMPRE calculado do banco."""
    t = ops.totals(date_from, date_to)
    income, expense = from_cents(t["receita"]), from_cents(t["despesa"])
    return {"income": income, "expense": expense, "result": income - expense, "count": t["count"]}


def current_balance() -> Decimal:
    """Saldo atual = todas as receitas - todas as despesas registradas."""
    return summary()["result"]


# ------------------------------------------------------------------------- metas
def list_goals() -> List[Goal]:
    return ops.list_goals()


@_friendly_db_errors
def create_goal(name, target_text, current_text, deadline_text) -> int:
    d = vs.validate_goal(name, target_text, current_text, deadline_text, check_future=True)
    return ops.insert_goal(d["name"], to_cents(d["target"]), to_cents(d["current"]), d["deadline"])


@_friendly_db_errors
def update_goal(goal_id, name, target_text, current_text, deadline_text) -> None:
    d = vs.validate_goal(name, target_text, current_text, deadline_text, check_future=False)
    if ops.update_goal(goal_id, d["name"], to_cents(d["target"]), to_cents(d["current"]), d["deadline"]) == 0:
        raise BusinessError("Meta não encontrada.")


@_friendly_db_errors
def add_to_goal(goal_id, amount_text) -> Goal:
    """Soma um valor ao acumulado da meta. NÃO cria movimentação nem altera o saldo."""
    amount = vs.parse_money(amount_text, "Valor")
    goal = ops.get_goal(goal_id)
    if goal is None:
        raise BusinessError("Meta não encontrada.")
    ops.update_goal(goal_id, goal.name, goal.target_cents,
                    goal.current_cents + to_cents(amount), goal.deadline)
    return ops.get_goal(goal_id)


@_friendly_db_errors
def delete_goal(goal_id) -> None:
    if ops.delete_goal(goal_id) == 0:
        raise BusinessError("Meta não encontrada.")
