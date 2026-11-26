"""Janela principal: menu lateral, navegação entre telas e avisos (toast)."""
import os
import traceback

import customtkinter as ctk

from database import connection, operations as ops
from database.demo_data import seed_demo_data
from database.schema import initialize_database
from interface import theme as T
from interface.categories import CategoriesPage
from interface.dashboard import DashboardPage
from interface.education import EducationPage
from interface.goals import GoalsPage
from interface.reports import ReportsPage
from interface.settings import SettingsPage
from interface.transactions import TransactionsPage

NAV = [
    ("dashboard", "📊", "Dashboard", DashboardPage),
    ("transactions", "💸", "Movimentações", TransactionsPage),
    ("categories", "🏷", "Categorias", CategoriesPage),
    ("reports", "📈", "Relatórios", ReportsPage),
    ("goals", "🎯", "Metas financeiras", GoalsPage),
    ("education", "📚", "Educação financeira", EducationPage),
    ("settings", "⚙", "Configurações", SettingsPage),
]


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("MoneyTrack — Educação e controle financeiro")
        self.geometry("1360x820")
        self.minsize(1180, 700)
        self.configure(fg_color=T.BG)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.pages, self.current, self.nav_buttons = {}, None, {}
        self._toast_job = None
        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.toast_label = ctk.CTkLabel(self, text="", font=T.font(13, "bold"), corner_radius=10,
                                        text_color="white", height=40)
        self.show_page("dashboard")

    # ---------------------------------------------------------------- navegação
    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=250, fg_color=T.NAVY, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="💲 MoneyTrack", font=T.font(24, "bold"), text_color="white").pack(
            anchor="w", padx=22, pady=(28, 0))
        ctk.CTkLabel(side, text="Educação financeira", font=T.font(12), text_color="#93C5FD").pack(
            anchor="w", padx=24, pady=(0, 26))
        for key, icon, label, _cls in NAV:
            btn = ctk.CTkButton(side, text=f"  {icon}   {label}", anchor="w", height=44, corner_radius=10,
                                font=T.font(14), fg_color="transparent", hover_color=T.NAVY_LIGHT,
                                text_color="white", command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[key] = btn
        self.demo_banner = ctk.CTkLabel(side, text="MODO DEMONSTRAÇÃO\n(banco separado)", font=T.font(11, "bold"),
                                        fg_color="#F59E0B", text_color=T.NAVY, corner_radius=8, height=44)
        ctk.CTkLabel(side, text="v1.0 · Tech Solutions 2026", font=T.font(11), text_color="#64748B").pack(
            side="bottom", pady=14)

    def show_page(self, key):
        if self.current:
            self.pages[self.current].pack_forget()
        if key not in self.pages:
            cls = next(c for k, _i, _l, c in NAV if k == key)
            self.pages[key] = cls(self.content, self)
        self.pages[key].pack(fill="both", expand=True)
        self.current = key
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=T.BLUE if k == key else "transparent")
        self.pages[key].on_show()   # recarrega os dados do banco ao entrar na tela

    # -------------------------------------------------------------------- avisos
    def toast(self, message, kind="success"):
        """Feedback visual temporário após cada operação."""
        color = T.GREEN if kind == "success" else T.RED
        icon = "✔" if kind == "success" else "⚠"
        self.toast_label.configure(text=f"  {icon}  {message}  ", fg_color=color)
        self.toast_label.place(relx=0.58, rely=0.97, anchor="s")
        self.toast_label.lift()
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(3500, self.toast_label.place_forget)

    # ---------------------------------------------------------- modo demonstração
    def set_demo_mode(self, enabled, force_reset=False):
        if enabled:
            connection.set_database(connection.DEMO_DB_PATH)
            if force_reset and connection.DEMO_DB_PATH.exists():
                os.remove(connection.DEMO_DB_PATH)
            initialize_database()
            if ops.totals()["count"] == 0 and not ops.list_goals():
                seed_demo_data()
            self.demo_banner.pack(side="bottom", fill="x", padx=16, pady=(0, 6))
        else:
            connection.set_database(connection.REAL_DB_PATH)
            initialize_database()
            self.demo_banner.pack_forget()
        if self.current and self.current != "settings":
            self.pages[self.current].on_show()
        for key, page in self.pages.items():
            if key not in (self.current,) and hasattr(page, "on_show") and key != "settings":
                pass  # as demais telas recarregam ao serem abertas

    def report_callback_exception(self, exc, val, tb):
        traceback.print_exception(exc, val, tb)
        self.toast(f"Erro inesperado: {val}", "error")
