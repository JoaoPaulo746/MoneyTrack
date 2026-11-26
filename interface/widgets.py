"""Componentes visuais reutilizáveis."""
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from interface import theme as T
from models.money import format_cents
from services.validation_service import iso_to_br


class Page(ctk.CTkFrame):
    """Base das telas: cabeçalho + método on_show() chamado ao exibir (recarrega os dados)."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.app = app

    def make_header(self, title, subtitle=""):
        """Cria o cabeçalho e devolve o frame da direita (para botões/filtros)."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(20, 10))
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text=title, font=T.font(24, "bold"), text_color=T.TEXT, anchor="w").pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, font=T.font(13), text_color=T.MUTED, anchor="w").pack(anchor="w")
        actions = ctk.CTkFrame(bar, fg_color="transparent")
        actions.pack(side="right")
        return actions

    def on_show(self):
        pass


class Card(ctk.CTkFrame):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", T.CARD)
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", T.BORDER)
        super().__init__(master, **kw)


class KpiCard(Card):
    """Cartão de indicador: título, valor grande colorido e detalhe."""

    def __init__(self, master, title, icon="", accent=T.TEXT, value_size=22):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.default_accent = accent
        ctk.CTkLabel(self, text=f"{icon}  {title}".strip(), font=T.font(12), text_color=T.MUTED,
                     anchor="w").grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        self.value_label = ctk.CTkLabel(self, text="—", font=T.font(value_size, "bold"),
                                        text_color=accent, anchor="w", wraplength=240, justify="left")
        self.value_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 0))
        self.sub_label = ctk.CTkLabel(self, text="", font=T.font(11), text_color=T.MUTED,
                                      anchor="w", wraplength=240, justify="left")
        self.sub_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

    def set(self, value, sub="", color=None):
        self.value_label.configure(text=value, text_color=color or self.default_accent)
        self.sub_label.configure(text=sub)


class ListCard(Card):
    """Cartão com título e corpo que pode ser limpo e reconstruído."""

    def __init__(self, master, title):
        super().__init__(master)
        ctk.CTkLabel(self, text=title, font=T.font(14, "bold"), text_color=T.TEXT,
                     anchor="w").pack(fill="x", padx=16, pady=(12, 4))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=4, pady=(0, 10))

    def clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def empty(self, text):
        ctk.CTkLabel(self.body, text=text, font=T.font(12), text_color=T.MUTED,
                     wraplength=300, justify="left").pack(padx=12, pady=12, anchor="w")


class ChartCard(Card):
    """Cartão que embute uma figura Matplotlib."""

    def __init__(self, master, title, height=280):
        super().__init__(master)
        ctk.CTkLabel(self, text=title, font=T.font(14, "bold"), text_color=T.TEXT,
                     anchor="w").pack(fill="x", padx=16, pady=(12, 0))
        self.body = ctk.CTkFrame(self, fg_color="transparent", height=height)
        self.body.pack(fill="both", expand=True, padx=8, pady=(4, 10))
        self.body.pack_propagate(False)
        self._chart_canvas = None

    def draw(self, painter):
        """painter(ax) desenha o gráfico. A figura é recriada a cada atualização."""
        if self._chart_canvas is not None:
            self._chart_canvas.get_tk_widget().destroy()
            self._chart_canvas = None
        fig = Figure(figsize=(5, 2.8), dpi=100, facecolor="white", layout="constrained")
        ax = fig.add_subplot(111)
        painter(ax)
        canvas = FigureCanvasTkAgg(fig, master=self.body)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvas = canvas


def tx_row(parent, tx):
    """Linha de movimentação: ícone colorido, descrição, categoria/data e valor."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=3)
    ctk.CTkLabel(row, text=tx.category_icon or "•", width=32, height=32, corner_radius=16,
                 fg_color=tx.category_color or T.MUTED, text_color="white").pack(side="left")
    mid = ctk.CTkFrame(row, fg_color="transparent")
    mid.pack(side="left", fill="x", expand=True, padx=10)
    desc = tx.description if len(tx.description) <= 30 else tx.description[:29] + "…"
    ctk.CTkLabel(mid, text=desc, font=T.font(13, "bold"), text_color=T.TEXT, anchor="w").pack(fill="x")
    ctk.CTkLabel(mid, text=f"{tx.category_name} · {iso_to_br(tx.transaction_date)}", font=T.font(11),
                 text_color=T.MUTED, anchor="w").pack(fill="x")
    income = tx.type == "receita"
    ctk.CTkLabel(row, text=f"{'+' if income else '-'} {format_cents(tx.amount_cents)}",
                 font=T.font(13, "bold"), text_color=T.GREEN if income else T.RED).pack(side="right")


def form_row(parent, label, widget_factory, row):
    """Linha de formulário (rótulo + campo) em grid de 2 colunas."""
    ctk.CTkLabel(parent, text=label, font=T.font(12), text_color=T.MUTED, anchor="w").grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=6)
    widget = widget_factory(parent)
    widget.grid(row=row, column=1, sticky="ew", pady=6)
    return widget


class BaseDialog(ctk.CTkToplevel):
    """Janela modal com área de mensagem de erro (feedback visual)."""

    def __init__(self, master, title, width=460, height=480):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=T.CARD)
        self.transient(master.winfo_toplevel())
        self.after(150, self._grab)

    def _grab(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def build_footer(self, on_save, save_text="Salvar"):
        self.error_label = ctk.CTkLabel(self, text="", text_color=T.RED, font=T.font(12),
                                        wraplength=400, justify="left")
        self.error_label.pack(padx=24, pady=(4, 0), anchor="w")
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(buttons, text="Cancelar", fg_color="#E5E7EB", text_color=T.TEXT,
                      hover_color="#D1D5DB", command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(buttons, text=save_text, fg_color=T.GREEN, hover_color=T.GREEN_DARK,
                      command=on_save).pack(side="right")

    def show_error(self, message):
        self.error_label.configure(text="⚠  " + message)
