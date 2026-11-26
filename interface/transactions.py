"""Tela de Movimentações: cadastro, consulta, edição, exclusão, busca, filtros e ordenação."""
from datetime import date
from decimal import Decimal
from tkinter import messagebox, ttk

import customtkinter as ctk

from interface import theme as T
from interface.widgets import BaseDialog, Page, form_row
from models.money import format_brl, from_cents
from services import finance_service as fs
from services.finance_service import BusinessError
from services.validation_service import ValidationError, iso_to_br, parse_date


class TransactionDialog(BaseDialog):
    """Formulário para criar/editar movimentação."""

    def __init__(self, master, on_saved, transaction=None, default_type="despesa"):
        super().__init__(master, "Editar movimentação" if transaction else "Nova movimentação", 480, 560)
        self.on_saved = on_saved
        self.transaction = transaction
        self.type_var = ctk.StringVar(value=transaction.type if transaction else default_type)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(20, 0))
        form.grid_columnconfigure(1, weight=1)

        self.type_btn = form_row(form, "Tipo", lambda p: ctk.CTkSegmentedButton(
            p, values=["Receita", "Despesa"], command=self._type_changed,
            selected_color=T.NAVY, selected_hover_color=T.NAVY_LIGHT), 0)
        self.type_btn.set(self.type_var.get().capitalize())
        self.desc = form_row(form, "Descrição *", lambda p: ctk.CTkEntry(p, placeholder_text="Ex.: Mercado"), 1)
        self.amount = form_row(form, "Valor (R$) *", lambda p: ctk.CTkEntry(p, placeholder_text="0,00"), 2)
        self.date = form_row(form, "Data *", lambda p: ctk.CTkEntry(p, placeholder_text="DD/MM/AAAA"), 3)
        self.category_menu = form_row(form, "Categoria *", lambda p: ctk.CTkOptionMenu(
            p, values=["-"], fg_color="#F1F5F9", text_color=T.TEXT, button_color=T.NAVY,
            button_hover_color=T.NAVY_LIGHT, dropdown_text_color=T.TEXT), 4)
        self.notes = form_row(form, "Observação", lambda p: ctk.CTkEntry(p, placeholder_text="Opcional"), 5)

        self.categories = {}
        self._load_categories()
        if transaction:
            self.desc.insert(0, transaction.description)
            self.amount.insert(0, f"{from_cents(transaction.amount_cents):.2f}".replace(".", ","))
            self.date.insert(0, iso_to_br(transaction.transaction_date))
            self.notes.insert(0, transaction.notes)
            self._select_category(transaction.category_id)
        else:
            self.date.insert(0, date.today().strftime("%d/%m/%Y"))
        self.build_footer(self._save)
        self.desc.focus()

    def _current_type(self):
        return self.type_btn.get().lower()

    def _load_categories(self):
        cats = fs.list_categories(self._current_type())
        self.categories = {f"{c.icon} {c.name}".strip(): c.id for c in cats}
        names = list(self.categories) or ["(sem categorias)"]
        self.category_menu.configure(values=names)
        self.category_menu.set(names[0])

    def _select_category(self, category_id):
        for label, cid in self.categories.items():
            if cid == category_id:
                self.category_menu.set(label)

    def _type_changed(self, _value):
        self._load_categories()

    def _save(self):
        category_id = self.categories.get(self.category_menu.get())
        args = (self.desc.get(), self.amount.get(), self._current_type(), category_id,
                self.date.get(), self.notes.get())
        try:
            if self.transaction:
                fs.update_transaction(self.transaction.id, *args)
                msg = "Movimentação atualizada com sucesso."
            else:
                fs.add_transaction(*args)
                msg = "Movimentação cadastrada com sucesso."
        except (ValidationError, BusinessError) as exc:
            self.show_error(str(exc))
            return
        self.destroy()
        self.on_saved(msg)


class TransactionsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        actions = self.make_header("Movimentações", "Registre e consulte suas receitas e despesas")
        ctk.CTkButton(actions, text="＋  Nova receita", fg_color=T.GREEN, hover_color=T.GREEN_DARK,
                      command=lambda: self.open_form(None, "receita")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="－  Nova despesa", fg_color=T.RED, hover_color=T.RED_DARK,
                      command=lambda: self.open_form(None, "despesa")).pack(side="left")

        self.desc_descending = True
        self.category_map = {"Todas as categorias": None}
        self._build_filters()
        self._build_table()

    # ------------------------------------------------------------------ filtros
    def _build_filters(self):
        bar = ctk.CTkFrame(self, fg_color=T.CARD, corner_radius=14, border_width=1, border_color=T.BORDER)
        bar.pack(fill="x", padx=24, pady=(0, 10))
        row1 = ctk.CTkFrame(bar, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(12, 4))
        row2 = ctk.CTkFrame(bar, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(4, 12))

        self.search = ctk.CTkEntry(row1, placeholder_text="🔎  Pesquisar por descrição…", width=260)
        self.search.pack(side="left", padx=(0, 8))
        self.search.bind("<KeyRelease>", lambda _e: self.refresh())

        self.type_var = ctk.StringVar(value="Todos os tipos")
        ctk.CTkOptionMenu(row1, values=["Todos os tipos", "Receitas", "Despesas"], variable=self.type_var,
                          width=140, command=lambda _v: self.refresh(), fg_color="#F1F5F9", text_color=T.TEXT,
                          button_color=T.NAVY, button_hover_color=T.NAVY_LIGHT).pack(side="left", padx=4)
        self.category_var = ctk.StringVar(value="Todas as categorias")
        self.category_menu = ctk.CTkOptionMenu(row1, values=["Todas as categorias"], variable=self.category_var,
                                               width=210, command=lambda _v: self.refresh(), fg_color="#F1F5F9",
                                               text_color=T.TEXT, button_color=T.NAVY,
                                               button_hover_color=T.NAVY_LIGHT)
        self.category_menu.pack(side="left", padx=4)

        ctk.CTkLabel(row2, text="De", text_color=T.MUTED).pack(side="left", padx=(0, 4))
        self.date_from = ctk.CTkEntry(row2, placeholder_text="DD/MM/AAAA", width=110)
        self.date_from.pack(side="left")
        ctk.CTkLabel(row2, text="até", text_color=T.MUTED).pack(side="left", padx=6)
        self.date_to = ctk.CTkEntry(row2, placeholder_text="DD/MM/AAAA", width=110)
        self.date_to.pack(side="left")
        for e in (self.date_from, self.date_to):
            e.bind("<Return>", lambda _e: self.refresh())
        ctk.CTkButton(row2, text="Filtrar", width=70, fg_color=T.NAVY, hover_color=T.NAVY_LIGHT,
                      command=self.refresh).pack(side="left", padx=8)
        ctk.CTkButton(row2, text="Limpar", width=70, fg_color="#E5E7EB", text_color=T.TEXT,
                      hover_color="#D1D5DB", command=self.clear_filters).pack(side="left")

        ctk.CTkLabel(row2, text="Ordenar por", text_color=T.MUTED).pack(side="left", padx=(24, 4))
        self.order_var = ctk.StringVar(value="Data")
        ctk.CTkOptionMenu(row2, values=["Data", "Valor"], variable=self.order_var, width=90,
                          command=lambda _v: self.refresh(), fg_color="#F1F5F9", text_color=T.TEXT,
                          button_color=T.NAVY, button_hover_color=T.NAVY_LIGHT).pack(side="left")
        self.direction_btn = ctk.CTkButton(row2, text="↓ Decrescente", width=120, fg_color="#E5E7EB",
                                           text_color=T.TEXT, hover_color="#D1D5DB",
                                           command=self.toggle_direction)
        self.direction_btn.pack(side="left", padx=6)

    # ------------------------------------------------------------------- tabela
    def _build_table(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("MT.Treeview", background="white", fieldbackground="white", foreground=T.TEXT,
                        rowheight=32, borderwidth=0, font=("Segoe UI", 11))
        style.configure("MT.Treeview.Heading", background=T.NAVY, foreground="white", relief="flat",
                        font=("Segoe UI", 11, "bold"), padding=6)
        style.map("MT.Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", T.TEXT)])
        style.map("MT.Treeview.Heading", background=[("active", T.NAVY_LIGHT)])

        card = ctk.CTkFrame(self, fg_color=T.CARD, corner_radius=14, border_width=1, border_color=T.BORDER)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        cols = ("data", "descricao", "categoria", "tipo", "valor")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", style="MT.Treeview", selectmode="browse")
        for col, text, width, anchor in [("data", "Data", 100, "center"), ("descricao", "Descrição", 300, "w"),
                                         ("categoria", "Categoria", 170, "w"), ("tipo", "Tipo", 90, "center"),
                                         ("valor", "Valor", 140, "e")]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor, stretch=(col == "descricao"))
        self.tree.tag_configure("receita", foreground=T.GREEN_DARK)
        self.tree.tag_configure("despesa", foreground=T.RED_DARK)
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", pady=8, padx=(0, 6))
        self.tree.pack(fill="both", expand=True, padx=(8, 0), pady=8)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 14))
        self.summary_label = ctk.CTkLabel(footer, text="", font=T.font(13), text_color=T.MUTED)
        self.summary_label.pack(side="left")
        ctk.CTkButton(footer, text="🗑  Excluir", width=100, fg_color=T.RED, hover_color=T.RED_DARK,
                      command=self.delete_selected).pack(side="right")
        ctk.CTkButton(footer, text="✏  Editar", width=100, fg_color=T.NAVY, hover_color=T.NAVY_LIGHT,
                      command=self.edit_selected).pack(side="right", padx=8)

    # --------------------------------------------------------------------- ações
    def toggle_direction(self):
        self.desc_descending = not self.desc_descending
        self.direction_btn.configure(text="↓ Decrescente" if self.desc_descending else "↑ Crescente")
        self.refresh()

    def clear_filters(self):
        self.search.delete(0, "end")
        self.date_from.delete(0, "end")
        self.date_to.delete(0, "end")
        self.type_var.set("Todos os tipos")
        self.category_var.set("Todas as categorias")
        self.order_var.set("Data")
        self.desc_descending = True
        self.direction_btn.configure(text="↓ Decrescente")
        self.refresh()

    def open_form(self, transaction, default_type="despesa"):
        TransactionDialog(self, self._after_save, transaction, default_type)

    def _after_save(self, message):
        self.app.toast(message, "success")
        self.refresh()

    def _selected_id(self):
        selection = self.tree.selection()
        if not selection:
            self.app.toast("Selecione uma movimentação na tabela primeiro.", "error")
            return None
        return int(selection[0])

    def edit_selected(self):
        tx_id = self._selected_id()
        if tx_id is None:
            return
        tx = fs.get_transaction(tx_id)
        if tx:
            self.open_form(tx)

    def delete_selected(self):
        tx_id = self._selected_id()
        if tx_id is None:
            return
        tx = fs.get_transaction(tx_id)
        if not tx:
            return
        if not messagebox.askyesno("Confirmar exclusão",
                                   f"Excluir a movimentação '{tx.description}' "
                                   f"({format_brl(tx.amount)})?\n\nEsta ação não pode ser desfeita.", parent=self):
            return
        try:
            fs.delete_transaction(tx_id)
        except BusinessError as exc:
            self.app.toast(str(exc), "error")
            return
        self.app.toast("Movimentação excluída.", "success")
        self.refresh()

    # ------------------------------------------------------------------- dados
    def on_show(self):
        self._reload_category_filter()
        self.refresh()

    def _reload_category_filter(self):
        cats = fs.list_categories()
        self.category_map = {"Todas as categorias": None}
        for c in cats:
            self.category_map[f"{c.name} · {c.type.capitalize()}"] = c.id
        current = self.category_var.get()
        self.category_menu.configure(values=list(self.category_map))
        if current not in self.category_map:
            self.category_var.set("Todas as categorias")

    def refresh(self):
        try:
            d_from = parse_date(self.date_from.get()).isoformat() if self.date_from.get().strip() else None
            d_to = parse_date(self.date_to.get()).isoformat() if self.date_to.get().strip() else None
        except ValidationError as exc:
            self.app.toast(str(exc), "error")
            return
        type_ = {"Receitas": "receita", "Despesas": "despesa"}.get(self.type_var.get())
        items = fs.list_transactions(
            search=self.search.get().strip() or None, type_=type_,
            category_id=self.category_map.get(self.category_var.get()),
            date_from=d_from, date_to=d_to,
            order_by="amount" if self.order_var.get() == "Valor" else "date",
            descending=self.desc_descending)

        self.tree.delete(*self.tree.get_children())
        income = expense = 0
        for tx in items:
            sign = "+" if tx.type == "receita" else "-"
            self.tree.insert("", "end", iid=str(tx.id), tags=(tx.type,), values=(
                iso_to_br(tx.transaction_date), tx.description,
                f"{tx.category_icon} {tx.category_name}".strip(), tx.type.capitalize(),
                f"{sign} {format_brl(tx.amount)}"))
            if tx.type == "receita":
                income += tx.amount_cents
            else:
                expense += tx.amount_cents
        self.summary_label.configure(
            text=f"{len(items)} movimentação(ões)   •   Receitas {format_brl(from_cents(income))}   •   "
                 f"Despesas {format_brl(from_cents(expense))}   •   Resultado {format_brl(from_cents(income - expense))}")
