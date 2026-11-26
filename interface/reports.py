"""Tela de Relatórios: indicadores, análises automáticas e gráficos de ciência de dados."""
import customtkinter as ctk
from tkinter import filedialog

from interface import charts
from interface import theme as T
from interface.widgets import ChartCard, KpiCard, ListCard, Page
from models.money import format_brl, format_cents
from services import analytics_service as an
from services import finance_service as fs
from services.validation_service import iso_to_br

INSIGHT_ICONS = {"positive": ("✅", T.GREEN_DARK), "negative": ("⚠", T.RED_DARK), "info": ("ℹ", T.TEXT)}


class ReportsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        actions = self.make_header("Relatórios", "Indicadores, análises automáticas e gráficos")
        self.period_var = ctk.StringVar(value="Todo o período")
        ctk.CTkOptionMenu(actions, values=fs.PERIODS, variable=self.period_var, width=170,
                          command=lambda _v: self.on_show(), fg_color="white", text_color=T.TEXT,
                          button_color=T.NAVY, button_hover_color=T.NAVY_LIGHT).pack(side="left", padx=(0, 10))
        ctk.CTkButton(actions, text="⬇  Exportar CSV", fg_color=T.NAVY, hover_color=T.NAVY_LIGHT,
                      command=self.export_csv).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Indicadores (2 linhas x 3)
        kp = ctk.CTkFrame(body, fg_color="transparent")
        kp.pack(fill="x")
        specs = [("avg", "Média mensal de despesas", "📅", T.TEXT), ("top", "Categoria que mais consome", "🏆", T.TEXT),
                 ("pct", "Receita comprometida com despesas", "📊", T.TEXT),
                 ("var", "Variação vs. mês anterior", "📈", T.TEXT), ("big", "Maior despesa registrada", "💥", T.RED),
                 ("saved", "Total economizado no período", "🐖", T.GREEN)]
        self.k = {}
        for i, (key, title, icon, color) in enumerate(specs):
            self.k[key] = KpiCard(kp, title, icon, color, value_size=18)
            kp.grid_columnconfigure(i % 3, weight=1, uniform="rk")
            self.k[key].grid(row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)

        # Análises + meses
        mid = ctk.CTkFrame(body, fg_color="transparent")
        mid.pack(fill="x")
        for c in (0, 1):
            mid.grid_columnconfigure(c, weight=1, uniform="rm")
        self.insights = ListCard(mid, "🧠 Análises automáticas")
        self.months = ListCard(mid, "Meses com saldo positivo ou negativo")
        self.insights.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.months.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        # Gráficos obrigatórios
        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        for c in (0, 1):
            grid.grid_columnconfigure(c, weight=1, uniform="rc")
        self.g1 = ChartCard(grid, "1. Despesas por categoria")
        self.g2 = ChartCard(grid, "2. Receitas x Despesas por mês")
        self.g3 = ChartCard(grid, "3. Evolução financeira mensal (histórico completo)")
        self.g4 = ChartCard(grid, "4. Distribuição percentual dos gastos")
        self.g5 = ChartCard(grid, "5. Comparação de despesas entre meses (últimos 3)", height=300)
        for i, card in enumerate([self.g1, self.g2, self.g3, self.g4]):
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)
        self.g5.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

    def on_show(self):
        d_from, d_to = fs.period_range(self.period_var.get())
        df_p, df_all = an.load_dataframe(d_from, d_to), an.load_dataframe()
        ind = an.indicators(df_p, df_all)
        cats = an.expenses_by_category(df_p)
        monthly_p, monthly_all = an.monthly_summary(df_p), an.monthly_summary(df_all)

        # Indicadores
        self.k["avg"].set(format_brl(ind["avg_monthly_expense"]), "média por mês no período")
        top = ind["top_category"]
        self.k["top"].set(top["name"] if top else "—",
                          f"{format_brl(top['amount'])} ({top['percent']:.0f}% das despesas)" if top else "sem despesas")
        pct = ind["committed_percent"]
        self.k["pct"].set(f"{pct:.0f}%" if pct is not None else "—",
                          "das receitas foram gastas" if pct is not None else "sem receitas no período",
                          (T.RED if pct >= 80 else T.GREEN) if pct is not None else T.TEXT)
        var = ind["variation_vs_previous"]
        if var is None:
            self.k["var"].set("—", "sem mês anterior para comparar")
        else:
            self.k["var"].set(f"{var:+.0f}%", "despesas do mês de referência vs. anterior",
                              T.RED if var > 0 else T.GREEN)
        big = ind["biggest_expense"]
        self.k["big"].set(format_brl(big["amount"]) if big else "—",
                          f"{big['description']} · {iso_to_br(big['date'])}" if big else "sem despesas")
        self.k["saved"].set(format_brl(ind["saved"]), "receitas − despesas",
                            T.GREEN if ind["saved"] >= 0 else T.RED)

        # Análises
        self.insights.clear()
        for ins in an.generate_insights(df_all):
            icon, color = INSIGHT_ICONS[ins.kind]
            ctk.CTkLabel(self.insights.body, text=f"{icon}  {ins.text}", anchor="w", justify="left", wraplength=480,
                         font=T.font(13), text_color=color).pack(fill="x", padx=12, pady=4)
        self.months.clear()
        if monthly_all.empty:
            self.months.empty("Sem dados ainda.")
        else:
            positives = int((monthly_all["resultado"] > 0).sum())
            negatives = int((monthly_all["resultado"] < 0).sum())
            ctk.CTkLabel(self.months.body, text=f"{positives} mês(es) positivo(s)  •  {negatives} negativo(s)",
                         font=T.font(12, "bold"), text_color=T.MUTED).pack(anchor="w", padx=12, pady=(0, 4))
            for month, r in monthly_all.iloc[::-1].head(8).iterrows():
                pos = r["resultado"] >= 0
                ctk.CTkLabel(self.months.body, anchor="w", font=T.font(13),
                             text=f"{'▲' if pos else '▼'}  {an.month_label(month).capitalize()}:  {format_cents(r['resultado'])}",
                             text_color=T.GREEN_DARK if pos else T.RED_DARK).pack(fill="x", padx=12, pady=2)

        # Gráficos
        self.g1.draw(lambda ax: charts.expenses_by_category_bars(ax, cats))
        self.g2.draw(lambda ax: charts.income_vs_expense(ax, monthly_p, last_n=12))
        self.g3.draw(lambda ax: charts.monthly_result(ax, monthly_all))
        self.g4.draw(lambda ax: charts.expense_pie(ax, cats, donut=False))
        pivot = an.category_month_comparison(df_all, 3)
        self.g5.draw(lambda ax: charts.month_comparison(ax, pivot))

    def export_csv(self):
        d_from, d_to = fs.period_range(self.period_var.get())
        df = an.load_dataframe(d_from, d_to)
        if df.empty:
            self.app.toast("Não há movimentações para exportar.", "error")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="moneytrack_movimentacoes.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        out = df[["transaction_date", "description", "category", "type"]].copy()
        out["valor_reais"] = df["amount_cents"] / 100
        out.columns = ["data", "descricao", "categoria", "tipo", "valor_reais"]
        try:
            out.to_csv(path, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        except OSError as exc:
            self.app.toast(f"Não foi possível salvar o arquivo: {exc}", "error")
            return
        self.app.toast("Relatório exportado com sucesso.", "success")
