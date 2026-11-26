"""Dashboard: indicadores, gráficos e resumos. Recarrega os dados do banco a cada exibição."""
import customtkinter as ctk

from interface import charts
from interface import theme as T
from interface.transactions import TransactionDialog
from interface.widgets import ChartCard, KpiCard, ListCard, Page, tx_row
from models.money import format_brl, format_cents
from services import analytics_service as an
from services import finance_service as fs

INSIGHT_COLORS = {"positive": T.GREEN_DARK, "negative": T.RED_DARK, "info": T.TEXT}


class DashboardPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        actions = self.make_header("Dashboard", "Visão geral da sua situação financeira")
        self.period_var = ctk.StringVar(value="Este mês")
        ctk.CTkOptionMenu(actions, values=fs.PERIODS, variable=self.period_var, width=170,
                          command=lambda _v: self.on_show(), fg_color="white", text_color=T.TEXT,
                          button_color=T.NAVY, button_hover_color=T.NAVY_LIGHT).pack(side="left", padx=(0, 10))
        ctk.CTkButton(actions, text="＋  Nova movimentação", fg_color=T.GREEN, hover_color=T.GREEN_DARK,
                      command=lambda: TransactionDialog(self, self._saved)).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Indicadores
        kpis = ctk.CTkFrame(body, fg_color="transparent")
        kpis.pack(fill="x")
        self.k_balance = KpiCard(kpis, "Saldo atual", "💰", T.NAVY)
        self.k_income = KpiCard(kpis, "Receitas", "⬆", T.GREEN)
        self.k_expense = KpiCard(kpis, "Despesas", "⬇", T.RED)
        self.k_result = KpiCard(kpis, "Resultado do período", "⚖", T.TEXT)
        self.k_count = KpiCard(kpis, "Movimentações", "🧾", T.BLUE)
        for i, card in enumerate([self.k_balance, self.k_income, self.k_expense, self.k_result, self.k_count]):
            kpis.grid_columnconfigure(i, weight=1, uniform="kpi")
            card.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)

        # Gráficos
        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        for c in (0, 1):
            grid.grid_columnconfigure(c, weight=1, uniform="ch")
        self.c_inc = ChartCard(grid, "Receitas x Despesas (últimos 6 meses)")
        self.c_cat = ChartCard(grid, "Despesas por categoria (período)")
        self.c_bal = ChartCard(grid, "Evolução do saldo")
        self.c_cmp = ChartCard(grid, "Comparação entre períodos")
        for i, card in enumerate([self.c_inc, self.c_cat, self.c_bal, self.c_cmp]):
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)

        # Listas
        lists = ctk.CTkFrame(body, fg_color="transparent")
        lists.pack(fill="x")
        for c in (0, 1):
            lists.grid_columnconfigure(c, weight=1, uniform="ls")
        self.l_recent = ListCard(lists, "Últimas movimentações")
        self.l_big = ListCard(lists, "Maiores despesas do período")
        self.l_month = ListCard(lists, "Resumo financeiro mensal")
        self.l_insight = ListCard(lists, "Destaques e análises")
        for i, card in enumerate([self.l_recent, self.l_big, self.l_month, self.l_insight]):
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)

    def _saved(self, message):
        self.app.toast(message, "success")
        self.on_show()   # indicadores e gráficos atualizam automaticamente

    def on_show(self):
        d_from, d_to = fs.period_range(self.period_var.get())
        s = fs.summary(d_from, d_to)
        balance = fs.current_balance()
        df_p, df_all = an.load_dataframe(d_from, d_to), an.load_dataframe()
        monthly_all = an.monthly_summary(df_all)
        cats = an.expenses_by_category(df_p)

        # Indicadores
        self.k_balance.set(format_brl(balance), "receitas − despesas (todo o histórico)",
                           T.GREEN if balance >= 0 else T.RED)
        self.k_income.set(format_brl(s["income"]), self.period_var.get())
        self.k_expense.set(format_brl(s["expense"]), self.period_var.get())
        self.k_result.set(format_brl(s["result"]), "positivo ✔" if s["result"] > 0 else
                          ("negativo ✖" if s["result"] < 0 else "equilibrado"),
                          T.GREEN if s["result"] > 0 else (T.RED if s["result"] < 0 else T.TEXT))
        self.k_count.set(str(s["count"]), "no período selecionado")

        # Gráficos
        self.c_inc.draw(lambda ax: charts.income_vs_expense(ax, monthly_all))
        self.c_cat.draw(lambda ax: charts.expense_pie(ax, cats))
        self.c_bal.draw(lambda ax: charts.balance_evolution(ax, an.daily_balance(df_all)))
        comp = an.period_comparison(df_all)
        self.c_cmp.draw(lambda ax: charts.period_comparison(ax, comp))

        # Últimas movimentações
        self.l_recent.clear()
        recent = fs.list_transactions(limit=6)
        for tx in recent:
            tx_row(self.l_recent.body, tx)
        if not recent:
            self.l_recent.empty("Nenhuma movimentação ainda. Clique em “Nova movimentação” para começar.")

        # Maiores despesas
        self.l_big.clear()
        big = fs.list_transactions(type_="despesa", date_from=d_from, date_to=d_to,
                                   order_by="amount", descending=True, limit=5)
        for tx in big:
            tx_row(self.l_big.body, tx)
        if not big:
            self.l_big.empty("Nenhuma despesa no período selecionado.")

        # Resumo mensal
        self.l_month.clear()
        if monthly_all.empty:
            self.l_month.empty("O resumo mensal aparece após o primeiro registro.")
        else:
            for month, r in monthly_all.tail(6).iloc[::-1].iterrows():
                row = ctk.CTkFrame(self.l_month.body, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=3)
                pos = r["resultado"] >= 0
                ctk.CTkLabel(row, text=charts.month_short(month), width=60, anchor="w", font=T.font(13, "bold"),
                             text_color=T.TEXT).pack(side="left")
                ctk.CTkLabel(row, text=f"⬆ {format_cents(r['receita'])}", text_color=T.GREEN_DARK,
                             font=T.font(12), width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"⬇ {format_cents(r['despesa'])}", text_color=T.RED_DARK,
                             font=T.font(12), width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=("▲ " if pos else "▼ ") + format_cents(r["resultado"]), anchor="e",
                             font=T.font(12, "bold"), text_color=T.GREEN if pos else T.RED).pack(side="right")

        # Destaques
        self.l_insight.clear()
        top = cats.iloc[0] if not cats.empty else None
        if top is not None:
            ctk.CTkLabel(self.l_insight.body, anchor="w", font=T.font(13, "bold"), text_color=T.TEXT,
                         text=f"🏆 Categoria com mais gastos: {top['category']} ({format_cents(top['amount_cents'])})",
                         wraplength=420, justify="left").pack(fill="x", padx=12, pady=(2, 6))
        for ins in an.generate_insights(df_all)[:4]:
            ctk.CTkLabel(self.l_insight.body, text="•  " + ins.text, anchor="w", justify="left", wraplength=420,
                         font=T.font(12), text_color=INSIGHT_COLORS[ins.kind]).pack(fill="x", padx=12, pady=2)
