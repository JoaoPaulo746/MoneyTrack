"""Tela de Configurações: modo demonstração, dados e informações do sistema."""
import customtkinter as ctk
from tkinter import messagebox

from database import connection
from interface import theme as T
from interface.widgets import Card, Page
from database.schema import wipe_all_data


class SettingsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.make_header("Configurações", "Dados, modo de demonstração e informações do sistema")
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        demo = Card(body)
        demo.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(demo, text="Modo demonstração", font=T.font(16, "bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(demo, text="Usa um banco de dados SEPARADO (moneytrack_demo.db) com ~4 meses de movimentações de exemplo, "
                     "ideal para apresentar o sistema. Seus dados reais não são alterados nem misturados.",
                     font=T.font(12), text_color=T.MUTED, wraplength=820, justify="left").pack(anchor="w", padx=18)
        self.demo_switch = ctk.CTkSwitch(demo, text="Ativar modo demonstração", command=self.toggle_demo,
                                         progress_color=T.GREEN)
        self.demo_switch.pack(anchor="w", padx=18, pady=(12, 4))
        ctk.CTkButton(demo, text="Restaurar dados de demonstração", fg_color=T.NAVY, hover_color=T.NAVY_LIGHT,
                      command=self.reset_demo).pack(anchor="w", padx=18, pady=(4, 16))

        data = Card(body)
        data.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(data, text="Dados do banco ativo", font=T.font(16, "bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(16, 2))
        self.path_label = ctk.CTkLabel(data, text="", font=T.font(12), text_color=T.MUTED, wraplength=820, justify="left")
        self.path_label.pack(anchor="w", padx=18)
        ctk.CTkButton(data, text="Apagar todos os dados do banco ativo", fg_color=T.RED, hover_color=T.RED_DARK,
                      command=self.wipe).pack(anchor="w", padx=18, pady=(10, 16))

        about = Card(body)
        about.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(about, text="Sobre o MoneyTrack", font=T.font(16, "bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(about, text="MoneyTrack 1.0 — Plataforma de educação e controle financeiro pessoal.\n"
                     "Desafio Tech Solutions 2026 · 3º A · Técnico em Desenvolvimento de Sistemas.\n"
                     "Tecnologias: Python 3, CustomTkinter, SQLite, Pandas, NumPy e Matplotlib. Funciona 100% offline.",
                     font=T.font(12), text_color=T.MUTED, justify="left").pack(anchor="w", padx=18, pady=(0, 16))

    def on_show(self):
        if connection.is_demo():
            self.demo_switch.select()
        else:
            self.demo_switch.deselect()
        self.path_label.configure(text=f"Arquivo: {connection.get_database_path()}")

    def toggle_demo(self):
        self.app.set_demo_mode(bool(self.demo_switch.get()))
        self.on_show()

    def reset_demo(self):
        if not messagebox.askyesno("Restaurar demonstração", "Recriar os dados de demonstração do zero?", parent=self):
            return
        self.app.set_demo_mode(True, force_reset=True)
        self.on_show()
        self.app.toast("Dados de demonstração restaurados.", "success")

    def wipe(self):
        mode = "de DEMONSTRAÇÃO" if connection.is_demo() else "REAIS"
        if not messagebox.askyesno("Apagar dados", f"Apagar TODAS as movimentações, metas e categorias personalizadas "
                                   f"(dados {mode})?\n\nEsta ação não pode ser desfeita.", icon="warning", parent=self):
            return
        if not messagebox.askyesno("Confirmação final", "Tem certeza absoluta?", icon="warning", parent=self):
            return
        wipe_all_data()
        self.app.toast("Dados apagados. Categorias padrão restauradas.", "success")
