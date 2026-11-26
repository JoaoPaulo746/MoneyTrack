"""Análise financeira com Pandas/NumPy: indicadores, séries para gráficos e insights."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

import numpy as np
import pandas as pd

from database import operations as ops
from models.money import format_cents, from_cents

MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]
MIN_RECORDS = 3  # mínimo de registros para gerar análises


@dataclass
class Insight:
    kind: str   # "positive" | "negative" | "info"
    text: str


# ------------------------------------------------------------------ utilitários
def month_label(period: str) -> str:
    """'2026-11' -> 'novembro de 2026'."""
    y, m = period.split("-")
    return f"{MONTHS[int(m) - 1]} de {y}"


def _prev_month(period: str) -> str:
    y, m = map(int, period.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def load_dataframe(date_from=None, date_to=None) -> pd.DataFrame:
    """Carrega as movimentações do banco em um DataFrame com colunas auxiliares."""
    df = ops.transactions_dataframe(date_from, date_to)
    df["date"] = pd.to_datetime(df["transaction_date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    df["signed_cents"] = np.where(df["type"] == "receita", df["amount_cents"], -df["amount_cents"])
    return df


# ------------------------------------------------------------ séries p/ gráficos
def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Receitas, despesas, resultado e saldo acumulado por mês (em centavos)."""
    cols = ["receita", "despesa", "resultado", "acumulado"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    pivot = df.pivot_table(index="month", columns="type", values="amount_cents",
                           aggfunc="sum", fill_value=0)
    for col in ("receita", "despesa"):
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[["receita", "despesa"]].sort_index()
    full = pd.period_range(pivot.index.min(), pivot.index.max(), freq="M").strftime("%Y-%m")
    pivot = pivot.reindex(full, fill_value=0)       # inclui meses sem movimentação
    pivot["resultado"] = pivot["receita"] - pivot["despesa"]
    pivot["acumulado"] = pivot["resultado"].cumsum()
    return pivot.astype("int64")


def expenses_by_category(df: pd.DataFrame) -> pd.DataFrame:
    exp = df[df["type"] == "despesa"]
    if exp.empty:
        return pd.DataFrame(columns=["category", "color", "amount_cents"])
    grouped = exp.groupby(["category", "color"], as_index=False)["amount_cents"].sum()
    return grouped.sort_values("amount_cents", ascending=False).reset_index(drop=True)


def daily_balance(df: pd.DataFrame) -> pd.Series:
    """Saldo acumulado ao longo do tempo (em centavos), um ponto por dia com movimento."""
    if df.empty:
        return pd.Series(dtype="int64")
    return df.groupby("date")["signed_cents"].sum().sort_index().cumsum()


def category_month_comparison(df: pd.DataFrame, months: int = 3) -> pd.DataFrame:
    """Despesas por categoria nos últimos N meses (linhas = categorias, colunas = meses)."""
    exp = df[df["type"] == "despesa"]
    if exp.empty:
        return pd.DataFrame()
    last = sorted(exp["month"].unique())[-months:]
    pivot = exp[exp["month"].isin(last)].pivot_table(
        index="category", columns="month", values="amount_cents", aggfunc="sum", fill_value=0)
    pivot["_total"] = pivot.sum(axis=1)
    return pivot.sort_values("_total", ascending=False).drop(columns="_total").head(8)


def reference_month(df: pd.DataFrame, today: Optional[date] = None) -> Optional[str]:
    """Mês atual, se tiver dados; senão o último mês com movimentações."""
    if df.empty:
        return None
    today = today or date.today()
    current = f"{today.year}-{today.month:02d}"
    months = set(df["month"].unique())
    return current if current in months else max(months)


def period_comparison(df_all: pd.DataFrame, today: Optional[date] = None) -> Optional[dict]:
    """Mês de referência x mês anterior (receitas, despesas e resultado, em centavos)."""
    ref = reference_month(df_all, today)
    if ref is None:
        return None
    monthly = monthly_summary(df_all)
    prev = _prev_month(ref)

    def row(m):
        if m in monthly.index:
            r = monthly.loc[m]
            return {"receita": int(r["receita"]), "despesa": int(r["despesa"]), "resultado": int(r["resultado"])}
        return {"receita": 0, "despesa": 0, "resultado": 0}

    return {"atual_label": month_label(ref), "anterior_label": month_label(prev),
            "atual": row(ref), "anterior": row(prev)}


# --------------------------------------------------------------- indicadores
def indicators(df_period: pd.DataFrame, df_all: pd.DataFrame, today: Optional[date] = None) -> dict:
    """Indicadores do período selecionado (variação mensal usa o histórico completo)."""
    income = int(df_period.loc[df_period["type"] == "receita", "amount_cents"].sum())
    expense = int(df_period.loc[df_period["type"] == "despesa", "amount_cents"].sum())

    monthly = monthly_summary(df_period)
    avg_expense = from_cents(int(round(monthly["despesa"].mean()))) if not monthly.empty else Decimal("0.00")

    cats = expenses_by_category(df_period)
    top_category = None
    if not cats.empty:
        top = cats.iloc[0]
        top_category = {"name": top["category"], "amount": from_cents(top["amount_cents"]),
                        "percent": top["amount_cents"] * 100.0 / expense}

    biggest = None
    exp_rows = df_period[df_period["type"] == "despesa"]
    if not exp_rows.empty:
        r = exp_rows.loc[exp_rows["amount_cents"].idxmax()]
        biggest = {"description": r["description"], "amount": from_cents(r["amount_cents"]),
                   "date": r["transaction_date"], "category": r["category"]}

    variation = None
    ref = reference_month(df_all, today)
    if ref is not None:
        m_all = monthly_summary(df_all)
        prev = _prev_month(ref)
        if prev in m_all.index and ref in m_all.index and m_all.loc[prev, "despesa"] > 0:
            variation = (m_all.loc[ref, "despesa"] - m_all.loc[prev, "despesa"]) * 100.0 / m_all.loc[prev, "despesa"]

    return {
        "income": from_cents(income), "expense": from_cents(expense),
        "avg_monthly_expense": avg_expense,
        "top_category": top_category,
        "committed_percent": (expense * 100.0 / income) if income > 0 else None,
        "variation_vs_previous": variation,
        "biggest_expense": biggest,
        "saved": from_cents(income - expense),
    }


# ------------------------------------------------------------ análises automáticas
def generate_insights(df_all: pd.DataFrame, today: Optional[date] = None) -> List[Insight]:
    """Interpreta os dados reais e produz observações em linguagem natural."""
    if len(df_all) < MIN_RECORDS:
        return [Insight("info", "Ainda não há dados suficientes para gerar análises. "
                                f"Cadastre pelo menos {MIN_RECORDS} movimentações para ver observações automáticas.")]
    ref = reference_month(df_all, today)
    label = month_label(ref)
    cur = df_all[df_all["month"] == ref]
    prev_key = _prev_month(ref)
    prev = df_all[df_all["month"] == prev_key]

    income = int(cur.loc[cur["type"] == "receita", "amount_cents"].sum())
    expense = int(cur.loc[cur["type"] == "despesa", "amount_cents"].sum())
    out: List[Insight] = []

    # 1) Participação da maior categoria
    cats = expenses_by_category(cur)
    if not cats.empty and expense > 0:
        top = cats.iloc[0]
        pct = top["amount_cents"] * 100.0 / expense
        out.append(Insight("info", f"Seus gastos com {top['category'].lower()} representam "
                                   f"{pct:.0f}% das despesas de {label}."))

    # 2) Variação das despesas vs. mês anterior
    prev_expense = int(prev.loc[prev["type"] == "despesa", "amount_cents"].sum())
    if prev_expense > 0:
        change = (expense - prev_expense) * 100.0 / prev_expense
        if abs(change) < 0.5:
            out.append(Insight("info", "Suas despesas ficaram estáveis em comparação ao mês anterior."))
        elif change > 0:
            out.append(Insight("negative", f"Suas despesas aumentaram {change:.0f}% em comparação ao mês anterior."))
        else:
            out.append(Insight("positive", f"Suas despesas diminuíram {abs(change):.0f}% em comparação ao mês anterior."))
    else:
        out.append(Insight("info", "Ainda não há despesas no mês anterior para comparação."))

    # 3) Resultado do período
    result = income - expense
    if result > 0:
        out.append(Insight("positive", f"Você teve um resultado financeiro positivo em {label}: "
                                       f"sobraram {format_cents(result)}."))
    elif result < 0:
        out.append(Insight("negative", f"Seu resultado financeiro em {label} foi negativo: você gastou "
                                       f"{format_cents(abs(result))} a mais do que recebeu."))
    else:
        out.append(Insight("info", f"Suas receitas e despesas de {label} ficaram equilibradas."))

    # 4) Comprometimento da renda
    if income > 0:
        committed = expense * 100.0 / income
        kind = "negative" if committed >= 80 else ("positive" if committed <= 60 else "info")
        extra = " Tente reduzir gastos para ganhar mais margem." if committed >= 80 else ""
        out.append(Insight(kind, f"{committed:.0f}% da sua receita de {label} foi comprometida com despesas.{extra}"))

    # 5) Categoria com maior crescimento
    cur_cat = cur[cur["type"] == "despesa"].groupby("category")["amount_cents"].sum()
    prev_cat = prev[prev["type"] == "despesa"].groupby("category")["amount_cents"].sum()
    growth = (cur_cat - prev_cat.reindex(cur_cat.index, fill_value=0))
    growth = growth[growth > 0]
    if not growth.empty and prev_expense > 0:
        name = growth.idxmax()
        out.append(Insight("negative", f"A categoria {name.lower()} apresentou o maior crescimento de gastos "
                                       f"(+{format_cents(int(growth.max()))} em relação ao mês anterior)."))
    return out
