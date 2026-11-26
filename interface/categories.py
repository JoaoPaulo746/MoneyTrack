"""Tela de Categorias: criar, editar, consultar e excluir (quando não vinculadas)."""
import customtkinter as ctk
from tkinter import messagebox

from interface import theme as T
from interface.widgets import BaseDialog, Card, Page, form_row
from services import finance_service as fs
from services.finance_service import BusinessError
from services.validation_service import ValidationError

PALETTE = ["#16A34A", "#0EA5E9", "#8B5CF6", "#EC4899", "#64748B", "#F97316", "#3B82F6", "#6366F1",
           "#0D9488", "#EF4444", "#A855F7", "#EAB308", "#14B8A6", "#78350F"]
ICONS = ["💼", "💻", "📈", "🎁", "💰", "🍔", "🚌", "🏠", "🎓", "💊", "🎮", "🛒", "📺", "📦",
         "✈", "🐶", "☕", "⚽", "🎵", "📚", "🔧", "👕", "💡", "📱"]


class CategoryDialog(BaseDialog):
    def __init__(self, master, on_saved, category=None, default_type="despesa"):
        super().__init__(master, "Editar categoria" if category else "Nova categoria", 480, 520)
        self.on_saved, self.category = on_saved, category
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(20, 0))
        form.grid_columnconfigure(1, weight=1)

        self.type_btn = form_row(form, "Tipo", lambda p: ctk.CTkSegmentedButton(
            p, values=["Receita", "Despesa"], selected_color=T.NAVY, selected_hover_color=T.NAVY_LIGHT), 0)
        self.type_btn.set((category.type if category else default_type).capitalize())
        self.name = form_row(form, "Nome *", lambda p: ctk.CTkEntry(p, placeholder_text="Ex.: Pets"), 1)
        self.icon_menu = form_row(form, "Ícone", lambda p: ctk.CTkOptionMenu(
            p, values=ICONS, fg_color="#F1F5F9", text_color=T.TEXT, button_color=T.NAVY,
            button_hover_color=T.NAVY_LIGHT, dropdown_text_color=T.TEXT), 2)
        self.color = form_row(form, "Cor (#RRGGBB)", lambda p: ctk.CTkEntry(p), 3)

        swatches = ctk.CTkFrame(form, fg_color="transparent")
        swatches.grid(row=4, column=1, sticky="w", pady=(0, 6))
        for i, hex_color in enumerate(PALETTE):
            ctk.CTkButton(swatches, text="", width=24, height=24, corner_radius=12, fg_color=hex_color,
                          hover_color=hex_color, command=lambda c=hex_color: self._pick(c)).grid(
                row=i // 7, column=i % 7, padx=2, pady=2)
        self.preview = ctk.CTkLabel(form, text="", width=40, height=40, corner_radius=20, text_color="white")
        self.preview.grid(row=5, column=1, sticky="w", pady=8)
        ctk.CTkLabel(form, text="Pré-visualização", text_color=T.MUTED, font=T.font(12)).grid(row=5, column=0, sticky="w")

        if category:
            self.name.insert(0, category.name)
            self.color.insert(0, category.color)
            if category.icon in ICONS:
                self.icon_menu.set(category.icon)
        else:
            self.color.insert(0, PALETTE[0])
        self.icon_menu.configure(command=lambda _v: self._update_preview())
        self.color.bind("<KeyRelease>", lambda _e: self._update_preview())
        self._update_preview()
        self.build_footer(self._save)

    def _pick(self, hex_color):
        self.color.delete(0, "end")
        self.color.insert(0, hex_color)
        self._update_preview()

    def _update_preview(self):
        value = self.color.get().strip()
        valid = len(value) == 7 and value.startswith("#")
        try:
            self.preview.configure(text=self.icon_menu.get(), fg_color=value if valid else T.MUTED)
        except Exception:
            self.preview.configure(text=self.icon_menu.get(), fg_color=T.MUTED)

    def _save(self):
        args = (self.name.get(), self.type_btn.get().lower(), self.color.get(), self.icon_menu.get())
        try:
            if self.category:
                fs.update_category(self.category.id, *args)
                msg = "Categoria atualizada com sucesso."
            else:
                fs.create_category(*args)
                msg = "Categoria criada com sucesso."
        except (ValidationError, BusinessError) as exc:
            self.show_error(str(exc))
            return
        self.destroy()
        self.on_saved(msg)


class CategoriesPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        actions = self.make_header("Categorias", "Organize receitas e despesas por categoria")
        ctk.CTkButton(actions, text="＋  Nova categoria", fg_color=T.GREEN, hover_color=T.GREEN_DARK,
                      command=lambda: CategoryDialog(self, self._saved)).pack()
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        for c in (0, 1):
            cols.grid_columnconfigure(c, weight=1, uniform="cat")
        cols.grid_rowconfigure(0, weight=1)
        self.lists = {}
        for i, (type_, title, color) in enumerate([("receita", "Receitas", T.GREEN), ("despesa", "Despesas", T.RED)]):
            card = Card(cols)
            card.grid(row=0, column=i, sticky="nsew", padx=6)
            ctk.CTkLabel(card, text=title, font=T.font(16, "bold"), text_color=color).pack(anchor="w", padx=16, pady=(14, 4))
            frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=6, pady=(0, 10))
            self.lists[type_] = frame

    def _saved(self, message):
        self.app.toast(message, "success")
        self.on_show()

    def on_show(self):
        for type_, frame in self.lists.items():
            for w in frame.winfo_children():
                w.destroy()
            for cat in fs.list_categories(type_):
                row = ctk.CTkFrame(frame, fg_color="#F8FAFC", corner_radius=10)
                row.pack(fill="x", padx=4, pady=3)
                ctk.CTkLabel(row, text=cat.icon or "•", width=34, height=34, corner_radius=17,
                             fg_color=cat.color, text_color="white").pack(side="left", padx=10, pady=8)
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(info, text=cat.name, font=T.font(13, "bold"), text_color=T.TEXT, anchor="w").pack(fill="x")
                ctk.CTkLabel(info, text=f"{cat.usage} movimentação(ões)", font=T.font(11), text_color=T.MUTED,
                             anchor="w").pack(fill="x")
                ctk.CTkButton(row, text="🗑", width=34, fg_color="#FEE2E2", text_color=T.RED, hover_color="#FECACA",
                              command=lambda c=cat: self.delete(c)).pack(side="right", padx=(0, 8))
                ctk.CTkButton(row, text="✏", width=34, fg_color="#E0E7FF", text_color=T.NAVY, hover_color="#C7D2FE",
                              command=lambda c=cat: CategoryDialog(self, self._saved, c)).pack(side="right", padx=4)

    def delete(self, cat):
        if cat.usage:
            self.app.toast(f"“{cat.name}” possui {cat.usage} movimentação(ões) vinculada(s) e não pode ser excluída.", "error")
            return
        if not messagebox.askyesno("Confirmar exclusão", f"Excluir a categoria '{cat.name}'?", parent=self):
            return
        try:
            fs.delete_category(cat.id)
        except BusinessError as exc:
            self.app.toast(str(exc), "error")
            return
        self.app.toast("Categoria excluída.", "success")
        self.on_show()
