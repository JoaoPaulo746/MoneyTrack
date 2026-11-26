"""Módulo de Educação Financeira: conteúdos + calculadoras ligadas aos dados reais do usuário."""
import customtkinter as ctk

from interface import theme as T
from interface.widgets import Card, Page
from models.money import format_brl
from services import analytics_service as an

LESSONS = {
    "Conceitos básicos": [
        ("O que é receita?", "Todo dinheiro que entra: salário, mesada, freelance, rendimentos e presentes. Conhecer suas "
         "receitas é o primeiro passo para saber quanto você realmente pode gastar."),
        ("O que é despesa?", "Todo dinheiro que sai: alimentação, transporte, moradia, lazer, assinaturas. Despesas "
         "podem ser FIXAS (aluguel, mensalidade) ou VARIÁVEIS (lanches, passeios)."),
        ("O que é saldo?", "Saldo = Receitas − Despesas. Saldo positivo significa que sobrou dinheiro; negativo, que você "
         "gastou mais do que recebeu — e provavelmente está usando dívida ou economias."),
    ],
    "Planejamento": [
        ("Regra 50-30-20", "Uma referência simples: 50% da renda para necessidades (moradia, comida, transporte), 30% "
         "para desejos (lazer, compras) e 20% para poupar ou quitar dívidas. Adapte à sua realidade."),
        ("Defina objetivos", "Metas com valor e prazo (ex.: R$ 3.000 em 10 meses) transformam “vontade” em plano. "
         "Use a tela de Metas para acompanhar o progresso."),
        ("Planeje o mês", "No início do mês, liste as receitas esperadas e as despesas fixas. O que sobra é o seu "
         "orçamento para gastos variáveis e para guardar."),
    ],
    "Controle de gastos": [
        ("Registre tudo", "Anote cada gasto, até os pequenos. Pequenas despesas repetidas (lanches, apps, delivery) "
         "somam muito no fim do mês."),
        ("Revise os relatórios", "Olhe a categoria que mais consome seu dinheiro e pergunte: esse gasto me traz "
         "valor? Dá para reduzir 10%?"),
        ("Pague-se primeiro", "Assim que receber, separe a parte da poupança antes de gastar. Poupar o que sobra "
         "raramente funciona; poupar primeiro cria o hábito."),
    ],
    "Consumo consciente": [
        ("Necessidade ou desejo?", "Antes de comprar, pergunte: eu preciso disso? Já tenho algo parecido? "
         "Vou usar com frequência?"),
        ("Regra das 48 horas", "Para compras por impulso, espere 48 horas. Se ainda fizer sentido, compre. "
         "Muitas vontades passam sozinhas."),
        ("Cuidado com parcelas e assinaturas", "Parcelas pequenas e assinaturas esquecidas comprometem a renda dos "
         "próximos meses. Revise-as periodicamente."),
    ],
    "Reserva de emergência": [
        ("Por que ter?", "É um dinheiro guardado para imprevistos (saúde, perda de renda, conserto). Sem reserva, "
         "qualquer surpresa vira dívida."),
        ("Quanto guardar?", "A recomendação comum é de 3 a 6 meses do seu custo de vida mensal. Quem está começando "
         "pode partir de uma primeira meta menor (ex.: 1 mês) e ir aumentando."),
        ("Onde deixar?", "Em aplicações seguras e com liquidez diária (como o Tesouro Selic ou CDB com liquidez "
         "diária), para poder sacar rápido quando precisar."),
    ],
}


class EducationPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.make_header("Educação financeira", "Aprenda a organizar e fazer seu dinheiro render")
        self.tabs = ctk.CTkTabview(self, fg_color=T.CARD, segmented_button_selected_color=T.NAVY,
                                   segmented_button_selected_hover_color=T.NAVY_LIGHT)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self.dynamic = {}
        for name, lessons in LESSONS.items():
            tab = self.tabs.add(name)
            scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            scroll.pack(fill="both", expand=True)
            for title, text in lessons:
                box = ctk.CTkFrame(scroll, fg_color="#F8FAFC", corner_radius=12)
                box.pack(fill="x", padx=6, pady=6)
                ctk.CTkLabel(box, text=title, font=T.font(15, "bold"), text_color=T.NAVY, anchor="w").pack(
                    fill="x", padx=16, pady=(12, 2))
                ctk.CTkLabel(box, text=text, font=T.font(13), text_color=T.TEXT, anchor="w", justify="left",
                             wraplength=820).pack(fill="x", padx=16, pady=(0, 12))
            if name in ("Planejamento", "Reserva de emergência"):
                label = ctk.CTkLabel(scroll, text="", font=T.font(13, "bold"), text_color=T.NAVY, anchor="w",
                                     justify="left", wraplength=820, fg_color="#DBEAFE", corner_radius=12)
                label.pack(fill="x", padx=6, pady=6, ipadx=12, ipady=12)
                self.dynamic[name] = label

    def on_show(self):
        """Calculadoras com base nos SEUS dados reais."""
        df = an.load_dataframe()
        monthly = an.monthly_summary(df)
        reserve = self.dynamic["Reserva de emergência"]
        plan = self.dynamic["Planejamento"]
        if monthly.empty or monthly["despesa"].mean() <= 0:
            reserve.configure(text="🧮 Sua reserva ideal: cadastre despesas para o MoneyTrack calcular com base nos seus gastos.")
        else:
            avg = monthly["despesa"].mean() / 100
            reserve.configure(text=f"🧮 Com base na sua média de gastos ({format_brl(avg)}/mês), sua reserva de "
                                   f"emergência ideal fica entre {format_brl(avg * 3)} (3 meses) e {format_brl(avg * 6)} (6 meses).")
        if monthly.empty or monthly["receita"].mean() <= 0:
            plan.configure(text="🧮 Regra 50-30-20: cadastre receitas para ver a divisão sugerida para a sua renda.")
        else:
            inc = monthly["receita"].mean() / 100
            plan.configure(text=f"🧮 Para a sua renda média ({format_brl(inc)}/mês), a regra 50-30-20 sugere: "
                                f"{format_brl(inc * 0.5)} em necessidades, {format_brl(inc * 0.3)} em desejos e "
                                f"{format_brl(inc * 0.2)} para poupar.")
