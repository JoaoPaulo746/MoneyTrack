"""Gera docs/modelo_er.png, docs/fluxograma_sistema.png e docs/fluxograma_movimentacao.png.
Uso: python docs/gerar_diagramas.py  (requer apenas matplotlib)"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

OUT = os.path.dirname(os.path.abspath(__file__))
NAVY, GREEN, RED, BLUE, GRAY = "#0B1F3A", "#16A34A", "#DC2626", "#2563EB", "#6B7280"


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w * 10); ax.set_ylim(0, h * 10); ax.axis("off")
    return fig, ax


def box(ax, cx, cy, w, h, text, fc="#E0E7FF", ec=NAVY, fs=9, color="black", weight="normal"):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=color, fontweight=weight)


def diamond(ax, cx, cy, w, h, text, fc="#FEF3C7", fs=8.5):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
                         fc=fc, ec="#B45309", lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p1, p2, label="", color=NAVY, off=(0, 0)):
    ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))
    if label:
        ax.text((p1[0] + p2[0]) / 2 + off[0], (p1[1] + p2[1]) / 2 + off[1], label, fontsize=8.5,
                color=color, fontweight="bold", ha="center", va="center",
                bbox=dict(fc="white", ec="none", pad=1))


# ---------------------------------------------------------------- modelo ER
def er():
    fig, ax = canvas(14, 8.2)
    ax.text(70, 77, "MoneyTrack — Modelo Entidade-Relacionamento (SQLite)", ha="center", fontsize=15, fontweight="bold", color=NAVY)

    def table(x, y, title, rows, color, w=38):
        h = 5.5 + len(rows) * 4.6
        ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.3,rounding_size=1", fc="white", ec=color, lw=2))
        ax.add_patch(FancyBboxPatch((x, y - 5.5), w, 5.5, boxstyle="round,pad=0.3,rounding_size=1", fc=color, ec=color))
        ax.text(x + w / 2, y - 2.8, title, ha="center", va="center", color="white", fontsize=12, fontweight="bold")
        for i, (name, typ, note) in enumerate(rows):
            yy = y - 5.5 - 3.4 - i * 4.6
            ax.text(x + 1.5, yy, name, fontsize=9, fontweight="bold" if "PK" in note or "FK" in note else "normal", va="center")
            ax.text(x + 17, yy, typ, fontsize=8.5, color=GRAY, va="center")
            ax.text(x + w - 1, yy, note, fontsize=8, color=BLUE if "FK" in note else RED, va="center", ha="right")
        return x, y, w, h

    table(4, 68, "categories", [("id", "INTEGER", "PK"), ("name", "TEXT", "NOT NULL"), ("type", "TEXT", "'receita'|'despesa'"),
                                ("color", "TEXT", "#RRGGBB"), ("icon", "TEXT", ""), ("UNIQUE", "(name, type)", "")], GREEN)
    table(52, 68, "transactions", [("id", "INTEGER", "PK"), ("description", "TEXT", "NOT NULL"),
                                   ("amount_cents", "INTEGER", "CHECK > 0"), ("type", "TEXT", "'receita'|'despesa'"),
                                   ("category_id", "INTEGER", "FK → categories.id"), ("transaction_date", "TEXT", "ISO válida"),
                                   ("notes", "TEXT", ""), ("created_at", "TEXT", "automático")], NAVY, w=44)
    table(100, 68, "goals", [("id", "INTEGER", "PK"), ("name", "TEXT", "NOT NULL"), ("target_cents", "INTEGER", "CHECK > 0"),
                             ("current_cents", "INTEGER", "CHECK >= 0"), ("created_at", "TEXT", ""), ("deadline", "TEXT", "opcional")], "#7C3AED", w=36)
    arrow(ax, (42.5, 50), (51.5, 50), color=GREEN)
    ax.text(47, 53, "1 : N", ha="center", fontsize=11, fontweight="bold", color=GREEN)
    ax.text(47, 46.5, "ON DELETE\nRESTRICT", ha="center", fontsize=8, color=GRAY)
    ax.text(118, 29, "Metas são informativas:\nnão se relacionam com as\nmovimentações nem alteram o saldo.", ha="center", fontsize=8.5, color=GRAY, style="italic")
    notes = ["Regras de integridade:",
             "• Saldo NÃO é armazenado: Saldo = SUM(receitas) − SUM(despesas), calculado a cada consulta.",
             "• Valores em CENTAVOS (INTEGER) + Decimal no Python → sem erro de ponto flutuante.",
             "• Trigger: o tipo da movimentação deve ser igual ao tipo da categoria; categoria com movimentações não troca de tipo.",
             "• PRAGMA foreign_keys = ON; consultas 100% parametrizadas (prevenção contra SQL Injection)."]
    for i, n in enumerate(notes):
        ax.text(4, 21 - i * 4.2, n, fontsize=9.5, fontweight="bold" if i == 0 else "normal", color=NAVY if i == 0 else "black")
    fig.savefig(os.path.join(OUT, "modelo_er.png"), dpi=130, bbox_inches="tight", facecolor="white")


# -------------------------------------------------------- fluxograma geral
def sistema():
    fig, ax = canvas(14, 8.6)
    ax.text(70, 83, "MoneyTrack — Fluxograma geral do sistema", ha="center", fontsize=15, fontweight="bold", color=NAVY)
    box(ax, 18, 73, 24, 7, "Início\npython main.py", "#DCFCE7", GREEN, 10, weight="bold")
    box(ax, 62, 73, 40, 7, "initialize_database()\ncria tabelas, triggers e categorias padrão", "#E0E7FF")
    box(ax, 112, 73, 38, 7, "Janela principal (CustomTkinter)\nmenu lateral + área de conteúdo", "#E0E7FF")
    arrow(ax, (30, 73), (42, 73)); arrow(ax, (82, 73), (92.5, 73))

    box(ax, 70, 56, 128, 10, "INTERFACE (interface/)\nDashboard  ·  Movimentações  ·  Categorias  ·  Relatórios  ·  Metas  ·  Educação financeira  ·  Configurações",
        "#DBEAFE", BLUE, 9.5, weight="bold")
    arrow(ax, (112, 69), (112, 61.5), color=BLUE)
    ax.text(70, 65.5, "o usuário escolhe uma seção; cada tela recarrega os dados do banco ao abrir (on_show)", ha="center", fontsize=9, color=GRAY, style="italic")

    box(ax, 26, 38, 40, 8, "validation_service\nvalida valores, datas e campos", "#FEF3C7", "#B45309")
    box(ax, 76, 38, 40, 8, "finance_service\nregras de negócio: CRUD, saldo,\ncategorias e metas", "#FEF3C7", "#B45309")
    box(ax, 117, 38, 38, 8, "analytics_service\nPandas + NumPy: indicadores\ne análises automáticas", "#FCE7F3", "#BE185D")
    for x in (26, 76, 117):
        arrow(ax, (x, 50.5), (x, 42.5), color=BLUE)
    arrow(ax, (46.5, 38), (55.5, 38), "valida", "#B45309", off=(0, 3.2))

    box(ax, 76, 21, 44, 8, "database/operations\nconsultas parametrizadas (sqlite3)", "#DCFCE7", GREEN)
    box(ax, 76, 6.5, 36, 7, "SQLite — data/moneytrack.db", "#BBF7D0", GREEN, 10, weight="bold")
    box(ax, 117, 21, 38, 8, "interface/charts\nMatplotlib → gráficos", "#FCE7F3", "#BE185D")
    arrow(ax, (76, 33.5), (76, 25.5)); arrow(ax, (76, 17), (76, 10))
    arrow(ax, (117, 33.5), (117, 25.5), "DataFrames", "#BE185D", off=(11, 0))
    arrow(ax, (106, 33.5), (92, 24), "lê dados", "#BE185D", off=(-3, 3))
    ax.text(117, 12, "gráficos exibidos no Dashboard\ne em Relatórios", ha="center", fontsize=8.5, color=GRAY, style="italic")
    fig.savefig(os.path.join(OUT, "fluxograma_sistema.png"), dpi=130, bbox_inches="tight", facecolor="white")


# ------------------------------------------- fluxograma: cadastrar movimentação
def movimentacao():
    fig, ax = canvas(11, 12)
    ax.text(55, 116, "Fluxograma — Cadastro de movimentação", ha="center", fontsize=14, fontweight="bold", color=NAVY)
    box(ax, 45, 107, 30, 6, "Início", "#DCFCE7", GREEN, 10, weight="bold")
    box(ax, 45, 96, 46, 7, "Usuário preenche o formulário\n(tipo, descrição, valor, data, categoria, obs.)", "#E0E7FF")
    diamond(ax, 45, 82, 44, 12, "Campos obrigatórios\ne valor válido (> 0)?")
    diamond(ax, 45, 64, 44, 12, "Data válida e categoria\ncompatível com o tipo?")
    box(ax, 45, 48, 46, 7, "Converte Decimal → centavos e grava\nno SQLite (INSERT parametrizado)", "#DCFCE7", GREEN)
    box(ax, 45, 35, 46, 7, "Fecha o formulário e mostra aviso verde\n“Movimentação cadastrada com sucesso”", "#DCFCE7", GREEN)
    box(ax, 45, 22, 46, 7, "Dashboard recalcula saldo, indicadores\ne gráficos a partir do banco", "#DBEAFE", BLUE)
    box(ax, 45, 10, 30, 6, "Fim", "#DCFCE7", GREEN, 10, weight="bold")
    box(ax, 95, 73, 30, 9, "Exibe mensagem de erro\nno formulário (nada é gravado)", "#FEE2E2", RED, 9)
    for a, b in [((45, 104), (45, 99.5)), ((45, 92.5), (45, 88)), ((45, 76), (45, 70)), ((45, 58), (45, 52)),
                 ((45, 44.5), (45, 38.5)), ((45, 31.5), (45, 25.5)), ((45, 18.5), (45, 13))]:
        arrow(ax, a, b)
    ax.text(47, 73, "Sim", color=GREEN, fontweight="bold", fontsize=9); ax.text(47, 55, "Sim", color=GREEN, fontweight="bold", fontsize=9)
    arrow(ax, (67, 82), (80, 76), "Não", RED); arrow(ax, (67, 64), (80, 70), "Não", RED)
    ax.annotate("", xy=(68, 96), xytext=(95, 77.5), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4, ls="--"))
    ax.text(88, 90, "corrige e tenta de novo", color=RED, fontsize=8.5, style="italic")
    fig.savefig(os.path.join(OUT, "fluxograma_movimentacao.png"), dpi=130, bbox_inches="tight", facecolor="white")


if __name__ == "__main__":
    er(); sistema(); movimentacao()
    print("Diagramas gerados em", OUT)
