"""Gráficos Matplotlib (funções puras: recebem um Axes e os dados já tratados pelo Pandas)."""
import matplotlib.dates as mdates
import numpy as np
from matplotlib.ticker import FuncFormatter

from interface import theme as T

MONTHS_SHORT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
FALLBACK_COLORS = ["#2563EB", "#F97316", "#16A34A", "#A855F7", "#EAB308", "#14B8A6", "#EF4444", "#64748B"]


def month_short(period: str) -> str:
    y, m = period.split("-")
    return f"{MONTHS_SHORT[int(m) - 1]}/{y[2:]}"


def _brl_axis(value, _pos=None) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _money(value) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _style(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#CBD5E1")
    ax.tick_params(colors=T.MUTED, labelsize=8)
    ax.grid(axis=grid_axis, color="#E5E7EB", linewidth=0.7)
    ax.set_axisbelow(True)


def _empty(ax, message="Sem dados para exibir"):
    ax.text(0.5, 0.5, message, ha="center", va="center", color=T.MUTED, fontsize=10,
            transform=ax.transAxes)
    ax.axis("off")


def income_vs_expense(ax, monthly, last_n=6):
    """Receitas x despesas por mês (barras agrupadas)."""
    if monthly is None or monthly.empty:
        return _empty(ax)
    m = monthly.tail(last_n)
    x = np.arange(len(m))
    w = 0.38
    ax.bar(x - w / 2, m["receita"] / 100, w, color=T.GREEN, label="Receitas")
    ax.bar(x + w / 2, m["despesa"] / 100, w, color=T.RED, label="Despesas")
    ax.set_xticks(x)
    ax.set_xticklabels([month_short(i) for i in m.index])
    ax.yaxis.set_major_formatter(FuncFormatter(_brl_axis))
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    _style(ax)


def expenses_by_category_bars(ax, cats, top=8):
    """Barras horizontais de despesas por categoria."""
    if cats is None or cats.empty:
        return _empty(ax, "Sem despesas no período")
    c = cats.head(top).iloc[::-1]
    values = c["amount_cents"] / 100
    bars = ax.barh(c["category"], values, color=list(c["color"]), height=0.6)
    ax.bar_label(bars, labels=[_money(v) for v in values], fontsize=7, padding=3, color=T.MUTED)
    ax.set_xlim(0, float(values.max()) * 1.35)
    ax.xaxis.set_major_formatter(FuncFormatter(_brl_axis))
    _style(ax, grid_axis="x")


def expense_pie(ax, cats, donut=True, top=7):
    """Distribuição percentual das despesas (rosca ou pizza). Agrupa o excedente em 'Demais'."""
    if cats is None or cats.empty:
        return _empty(ax, "Sem despesas no período")
    data = cats.head(top)
    rest = int(cats["amount_cents"].iloc[top:].sum())
    names = list(data["category"]) + (["Demais"] if rest else [])
    values = list(data["amount_cents"]) + ([rest] if rest else [])
    colors = list(data["color"]) + (["#94A3B8"] if rest else [])
    total = float(sum(values))
    kwargs = {"wedgeprops": dict(width=0.42, edgecolor="white")} if donut else {
        "wedgeprops": dict(edgecolor="white")}
    if not donut:
        kwargs["autopct"] = lambda p: f"{p:.0f}%" if p >= 6 else ""
        kwargs["pctdistance"] = 0.72
        kwargs["textprops"] = dict(color="white", fontsize=8, fontweight="bold")
    wedges = ax.pie(values, colors=colors, startangle=90, counterclock=False, **kwargs)[0]
    ax.set_aspect("equal")
    if donut:
        ax.text(0, 0, _money(total / 100).replace("R$ ", "R$\n"), ha="center", va="center",
                fontsize=9, fontweight="bold", color=T.TEXT)
    labels = [f"{n} ({v * 100 / total:.0f}%)" for n, v in zip(names, values)]
    ax.figure.legend(wedges, labels, loc="outside center right", fontsize=8, frameon=False)


def balance_evolution(ax, daily):
    """Evolução do saldo acumulado ao longo do tempo."""
    if daily is None or len(daily) == 0:
        return _empty(ax)
    y = daily.values / 100
    ax.plot(daily.index, y, color=T.BLUE, linewidth=2, marker="o" if len(y) <= 40 else None, markersize=3)
    ax.fill_between(daily.index, y, 0, color=T.BLUE, alpha=0.10)
    ax.axhline(0, color="#94A3B8", linewidth=0.8)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.yaxis.set_major_formatter(FuncFormatter(_brl_axis))
    _style(ax)


def monthly_result(ax, monthly):
    """Resultado mensal (verde/vermelho) + linha do saldo acumulado."""
    if monthly is None or monthly.empty:
        return _empty(ax)
    x = np.arange(len(monthly))
    res = monthly["resultado"] / 100
    ax.bar(x, res, color=[T.GREEN if v >= 0 else T.RED for v in res], width=0.55, label="Resultado do mês")
    ax.plot(x, monthly["acumulado"] / 100, color=T.NAVY, marker="o", linewidth=2, label="Saldo acumulado")
    ax.axhline(0, color="#94A3B8", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([month_short(i) for i in monthly.index])
    ax.yaxis.set_major_formatter(FuncFormatter(_brl_axis))
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    _style(ax)


def month_comparison(ax, pivot):
    """Despesas por categoria comparando os últimos meses."""
    if pivot is None or pivot.empty:
        return _empty(ax, "Sem despesas para comparar")
    shades = ["#BFDBFE", "#60A5FA", T.NAVY_LIGHT]
    months = list(pivot.columns)
    n = len(months)
    x = np.arange(len(pivot))
    w = 0.8 / n
    for i, m in enumerate(months):
        ax.bar(x + (i - (n - 1) / 2) * w, pivot[m] / 100, w,
               color=shades[-n:][i] if n <= 3 else None, label=month_short(m))
    ax.set_xticks(x)
    ax.set_xticklabels(list(pivot.index), rotation=25, ha="right", fontsize=7)
    ax.yaxis.set_major_formatter(FuncFormatter(_brl_axis))
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    _style(ax)


def period_comparison(ax, comp):
    """Mês de referência x mês anterior: receitas, despesas e resultado."""
    if not comp:
        return _empty(ax)
    groups = ["receita", "despesa", "resultado"]
    x = np.arange(3)
    w = 0.36
    prev = [comp["anterior"][g] / 100 for g in groups]
    cur = [comp["atual"][g] / 100 for g in groups]
    ax.bar(x - w / 2, prev, w, color="#93C5FD", label=comp["anterior_label"].split(" de ")[0].capitalize())
    ax.bar(x + w / 2, cur, w, color=T.NAVY, label=comp["atual_label"].split(" de ")[0].capitalize())
    ax.axhline(0, color="#94A3B8", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Receitas", "Despesas", "Resultado"])
    ax.yaxis.set_major_formatter(FuncFormatter(_brl_axis))
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    _style(ax)
