"""Tela de Metas financeiras (informativas: não alteram o saldo)."""
import customtkinter as ctk
from tkinter import messagebox

from interface import theme as T
from interface.widgets import BaseDialog, Card, Page, form_row
from models.money import format_brl
from services import finance_service as fs
from services.finance_service import BusinessError
from services.validation_service import ValidationError, iso_to_br


class GoalDialog(BaseDialog):
    def __init__(self, master, on_saved, goal=None):
        super().__init__(master, "Editar meta" if goal else "Nova meta", 460, 400)
        self.on_saved, self.goal = on_saved, goal
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(20, 0))
        form.grid_columnconfigure(1, weight=1)
        self.name = form_row(form, "Nome da meta *", lambda p: ctk.CTkEntry(p, placeholder_text="Ex.: Comprar um celular"), 0)
        self.target = form_row(form, "Valor desejado *", lambda p: ctk.CTkEntry(p, placeholder_text="0,00"), 1)
        self.current = form_row(form, "Valor acumulado", lambda p: ctk.CTkEntry(p, placeholder_text="0,00"), 2)
        self.deadline = form_row(form, "Prazo (opcional)", lambda p: ctk.CTkEntry(p, placeholder_text="DD/MM/AAAA"), 3)
        if goal:
            self.name.insert(0, goal.name)
            self.target.insert(0, f"{goal.target:.2f}".replace(".", ","))
            self.current.insert(0, f"{goal.current:.2f}".replace(".", ","))
            if goal.deadline:
                self.deadline.insert(0, iso_to_br(goal.deadline))
        else:
            self.current.insert(0, "0,00")
        self.build_footer(self._save)

    def _save(self):
        args = (self.name.get(), self.target.get(), self.current.get(), self.deadline.get())
        try:
            if self.goal:
                fs.update_goal(self.goal.id, *args)
                msg = "Meta atualizada com sucesso."
            else:
                fs.create_goal(*args)
                msg = "Meta criada com sucesso."
        except (ValidationError, BusinessError) as exc:
            self.show_error(str(exc))
            return
        self.destroy()
        self.on_saved(msg)


class GoalsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        actions = self.make_header("Metas financeiras", "Acompanhe seus objetivos e quanto falta para alcançá-los")
        ctk.CTkButton(actions, text="＋  Nova meta", fg_color=T.GREEN, hover_color=T.GREEN_DARK,
                      command=lambda: GoalDialog(self, self._saved)).pack()
        note = ctk.CTkLabel(self, text="ℹ  As metas são informativas: o valor acumulado nelas não altera o saldo calculado pelas movimentações.",
                            font=T.font(12), text_color=T.MUTED, anchor="w")
        note.pack(fill="x", padx=26, pady=(0, 6))
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=18, pady=(0, 14))

    def _saved(self, message):
        self.app.toast(message, "success")
        self.on_show()

    def on_show(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        goals = fs.list_goals()
        if not goals:
            ctk.CTkLabel(self.scroll, text="Nenhuma meta criada ainda.\nSugestões: comprar um computador, fazer uma viagem, "
                         "montar uma reserva de emergência.", font=T.font(14), text_color=T.MUTED, justify="left").pack(pady=40)
            return
        for g in goals:
            card = Card(self.scroll)
            card.pack(fill="x", padx=6, pady=6)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 4))
            ctk.CTkLabel(top, text=("✅ " if g.completed else "🎯 ") + g.name, font=T.font(16, "bold"),
                         text_color=T.TEXT).pack(side="left")
            ctk.CTkLabel(top, text=f"{g.progress:.0f}%", font=T.font(18, "bold"),
                         text_color=T.GREEN if g.completed else T.BLUE).pack(side="right")
            bar = ctk.CTkProgressBar(card, height=14, corner_radius=7, progress_color=T.GREEN if g.completed else T.BLUE,
                                     fg_color="#E5E7EB")
            bar.pack(fill="x", padx=16, pady=4)
            bar.set(g.progress / 100)
            info = f"{format_brl(g.current)} de {format_brl(g.target)}   •   faltam {format_brl(g.remaining)}"
            info += f"   •   criada em {iso_to_br(g.created_at)}"
            if g.deadline:
                days = g.days_left
                info += f"   •   prazo {iso_to_br(g.deadline)} ({'vencido' if days < 0 else f'{days} dias'})"
            ctk.CTkLabel(card, text=info, font=T.font(12), text_color=T.MUTED, anchor="w", wraplength=760,
                         justify="left").pack(fill="x", padx=16)
            if g.monthly_needed:
                ctk.CTkLabel(card, text=f"💡 Para chegar lá no prazo, guarde cerca de {format_brl(g.monthly_needed)} por mês.",
                             font=T.font(12), text_color=T.NAVY_LIGHT, anchor="w").pack(fill="x", padx=16, pady=(2, 0))
            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(fill="x", padx=16, pady=(8, 14))
            ctk.CTkButton(btns, text="＋ Adicionar valor", width=140, fg_color=T.GREEN, hover_color=T.GREEN_DARK,
                          command=lambda goal=g: self.deposit(goal)).pack(side="left")
            ctk.CTkButton(btns, text="Editar", width=80, fg_color=T.NAVY, hover_color=T.NAVY_LIGHT,
                          command=lambda goal=g: GoalDialog(self, self._saved, goal)).pack(side="left", padx=8)
            ctk.CTkButton(btns, text="Excluir", width=80, fg_color=T.RED, hover_color=T.RED_DARK,
                          command=lambda goal=g: self.delete(goal)).pack(side="left")

    def deposit(self, goal):
        dialog = ctk.CTkInputDialog(text=f"Quanto deseja adicionar à meta “{goal.name}”? (R$)", title="Adicionar valor")
        value = dialog.get_input()
        if value is None:
            return
        try:
            updated = fs.add_to_goal(goal.id, value)
        except (ValidationError, BusinessError) as exc:
            self.app.toast(str(exc), "error")
            return
        self.app.toast("Meta concluída! 🎉" if updated.completed else "Valor adicionado à meta.", "success")
        self.on_show()

    def delete(self, goal):
        if not messagebox.askyesno("Confirmar exclusão", f"Excluir a meta '{goal.name}'?", parent=self):
            return
        try:
            fs.delete_goal(goal.id)
        except BusinessError as exc:
            self.app.toast(str(exc), "error")
            return
        self.app.toast("Meta excluída.", "success")
        self.on_show()
