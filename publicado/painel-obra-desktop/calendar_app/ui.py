from __future__ import annotations

import tkinter as tk
from datetime import date, datetime, time, timedelta
from tkinter import filedialog, messagebox
import webbrowser

from .google_adapter import GoogleCalendarAdapter
from .models import EventDraft
from .oauth import OAuthManager
from .service import CalendarService, run_async

BG = "#f7f7fb"
SURFACE = "#ffffff"
TEXT = "#202238"
MUTED = "#85879a"
LINE = "#e9e9f1"
PURPLE = "#655de7"
PURPLE_SOFT = "#efefff"
FONT = "Segoe UI"


class CalendarWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Site Diary Intelligence")
        self.geometry("1180x720")
        self.minsize(920, 600)
        self.configure(bg=BG)
        self.oauth = OAuthManager()
        self.service: CalendarService | None = None
        self.events = []
        self.selected_day = 0
        self.panel_visible = True
        self.status = tk.StringVar(value="Agenda desconectada")
        self.updated = tk.StringVar(value="Nunca atualizada")
        self._build_shell()
        self._restore()

    def _build_shell(self):
        titlebar = tk.Frame(self, bg=SURFACE, height=54, highlightbackground=LINE, highlightthickness=1)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)
        tk.Label(titlebar, text="▦", fg=PURPLE, bg=SURFACE, font=(FONT, 18)).pack(side="left", padx=(20, 8))
        tk.Label(titlebar, text="Site Diary", fg=TEXT, bg=SURFACE, font=(FONT, 11, "bold")).pack(side="left")
        tk.Label(titlebar, textvariable=self.status, fg=MUTED, bg=SURFACE, font=(FONT, 9)).pack(side="right", padx=18)

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)

        self.workspace = tk.Frame(self.body, bg=BG)
        self.workspace.pack(side="left", fill="both", expand=True)
        self._build_workspace()

        self.panel = tk.Frame(self.body, bg=BG, width=410, highlightbackground=LINE, highlightthickness=1)
        self.panel.pack(side="right", fill="y")
        self.panel.pack_propagate(False)
        self._build_agenda()

        self.reopen = tk.Button(
            self.body, text="‹", command=self.toggle_panel, bg=PURPLE, fg="white",
            activebackground="#554ec9", activeforeground="white", relief="flat",
            font=(FONT, 18, "bold"), cursor="hand2", width=2,
        )

    def _build_workspace(self):
        header = tk.Frame(self.workspace, bg=BG)
        header.pack(fill="x", padx=34, pady=(28, 20))
        tk.Label(header, text="Área de trabalho", bg=BG, fg=TEXT, font=(FONT, 18, "bold")).pack(anchor="w")
        tk.Label(
            header, text="Acesse seus módulos e funcionalidades", bg=BG, fg=MUTED,
            font=(FONT, 10),
        ).pack(anchor="w", pady=(4, 0))

        grid = tk.Frame(self.workspace, bg=BG)
        grid.pack(fill="both", expand=True, padx=28)
        modules = [
            ("▦", "Visão geral"), ("◫", "Diários"), ("◈", "Indicadores"), ("△", "Ocorrências"),
            ("▤", "Relatórios"), ("✓", "Segurança"), ("◷", "Cronograma"), ("⌁", "Equipe"),
            ("□", "Materiais"), ("↗", "Produtividade"), ("!", "Alertas"), ("⚙", "Configurações"),
        ]
        for column in range(4):
            grid.grid_columnconfigure(column, weight=1, uniform="module")
        for row in range(3):
            grid.grid_rowconfigure(row, weight=1, uniform="module")
        for index, (icon, label) in enumerate(modules):
            card = tk.Frame(grid, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
            card.grid(row=index // 4, column=index % 4, sticky="nsew", padx=7, pady=7)
            tk.Label(card, text=icon, bg=SURFACE, fg=PURPLE, font=(FONT, 23)).pack(pady=(23, 9))
            tk.Label(card, text=label, bg=SURFACE, fg=TEXT, font=(FONT, 10, "bold")).pack()
            tk.Frame(card, bg="#ececf2", width=70, height=4).pack(pady=(11, 5))
            tk.Frame(card, bg="#f1f1f5", width=48, height=4).pack()

    def _build_agenda(self):
        top = tk.Frame(self.panel, bg=SURFACE, height=58)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="AGENDA", bg=SURFACE, fg=PURPLE, font=(FONT, 10, "bold")).pack(side="left", padx=18)
        tk.Button(
            top, text="»", command=self.toggle_panel, bg=SURFACE, fg=TEXT, relief="flat",
            font=(FONT, 15), cursor="hand2", activebackground=SURFACE,
        ).pack(side="right", padx=12)

        self.tabs = tk.Frame(self.panel, bg=SURFACE)
        self.tabs.pack(fill="x")
        self.tab_buttons = []
        for index, label in enumerate(("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")):
            button = tk.Button(
                self.tabs, text=label, command=lambda i=index: self.select_day(i),
                bg=SURFACE, fg=MUTED, activebackground=SURFACE, relief="flat",
                bd=0, font=(FONT, 9), cursor="hand2", pady=9,
            )
            button.pack(side="left", fill="x", expand=True)
            self.tab_buttons.append(button)
        self.tab_line = tk.Frame(self.panel, bg=LINE, height=1)
        self.tab_line.pack(fill="x")

        canvas_wrap = tk.Frame(self.panel, bg=BG)
        canvas_wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_wrap, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(canvas_wrap, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=BG)
        self.content.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))

        footer = tk.Frame(self.panel, bg=SURFACE, height=58, highlightbackground=LINE, highlightthickness=1)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        tk.Button(
            footer, text="Conectar Google Agenda", command=self.connect, bg=PURPLE, fg="white",
            activebackground="#554ec9", activeforeground="white", relief="flat",
            font=(FONT, 9, "bold"), cursor="hand2", padx=12, pady=6,
        ).pack(side="left", padx=12, pady=12)
        tk.Button(
            footer, text="↻", command=self.refresh, bg=SURFACE, fg=PURPLE, relief="flat",
            font=(FONT, 15), cursor="hand2",
        ).pack(side="right", padx=(0, 8))
        tk.Button(
            footer, text="⋮", command=self._account_menu, bg=SURFACE, fg=TEXT, relief="flat",
            font=(FONT, 16), cursor="hand2",
        ).pack(side="right")
        self.select_day(0)

    def _restore(self):
        credentials = self.oauth.credentials()
        if credentials:
            self._activate(credentials)
            self.refresh()
        else:
            self._render_content()

    def toggle_panel(self):
        if self.panel_visible:
            self.panel.pack_forget()
            self.reopen.pack(side="right", fill="y")
        else:
            self.reopen.pack_forget()
            self.panel.pack(side="right", fill="y")
        self.panel_visible = not self.panel_visible

    def select_day(self, index: int):
        self.selected_day = index
        for number, button in enumerate(self.tab_buttons):
            button.configure(
                fg=PURPLE if number == index else MUTED,
                font=(FONT, 9, "bold" if number == index else "normal"),
            )
        self._render_content()

    def _render_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        self._goal_cards()
        start = date.today() - timedelta(days=date.today().weekday())
        days = [start + timedelta(days=offset) for offset in range(7)]
        ordered = [days[self.selected_day]] + [day for day in days if day != days[self.selected_day]]
        for index, day in enumerate(ordered):
            self._day_card(day, expanded=index == 0)
        tk.Label(
            self.content, textvariable=self.updated, bg=BG, fg=MUTED, font=(FONT, 8),
        ).pack(anchor="e", padx=14, pady=(2, 12))

    def _goal_cards(self):
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x", padx=10, pady=(12, 8))
        for icon, title, lines in [
            ("◎", "Goal Week", ("Revisar o planejamento", "Fechar pendências críticas", "Atualizar avanço físico")),
            ("▣", "Goal Diário", ("Registrar diário da obra", "Validar entregas", "Revisar segurança")),
        ]:
            card = tk.Frame(row, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=4)
            head = tk.Frame(card, bg=SURFACE)
            head.pack(fill="x", padx=12, pady=(12, 7))
            tk.Label(head, text=icon, bg=SURFACE, fg=PURPLE, font=(FONT, 16)).pack(side="left")
            tk.Label(head, text=title, bg=SURFACE, fg=TEXT, font=(FONT, 9, "bold")).pack(side="left", padx=7)
            tk.Label(head, text="⋮", bg=SURFACE, fg=TEXT, font=(FONT, 13)).pack(side="right")
            for line in lines:
                item = tk.Frame(card, bg=SURFACE)
                item.pack(fill="x", padx=12, pady=3)
                tk.Label(item, text="○", bg=SURFACE, fg="#c5c6d2", font=(FONT, 11)).pack(side="left")
                tk.Label(item, text=line, bg=SURFACE, fg=MUTED, font=(FONT, 8)).pack(side="left", padx=6)
            tk.Frame(card, bg=SURFACE, height=9).pack()

    def _day_card(self, day: date, expanded: bool):
        names = ("SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO")
        card = tk.Frame(self.content, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        card.pack(fill="x", padx=14, pady=4)
        head = tk.Frame(card, bg=SURFACE)
        head.pack(fill="x", padx=12, pady=10)
        tk.Label(
            head, text=f"{names[day.weekday()]}  •  {day:%d/%m}", bg=SURFACE,
            fg=PURPLE if expanded else MUTED, font=(FONT, 8, "bold"),
        ).pack(side="left")
        tk.Button(
            head, text="+  Adicionar item", command=lambda d=day: self.add_event(d),
            bg=SURFACE, fg=PURPLE, relief="flat", font=(FONT, 8), cursor="hand2",
        ).pack(side="right")

        if not expanded:
            tk.Label(head, text="⌄", bg=SURFACE, fg=TEXT, font=(FONT, 10)).pack(side="right")
            return
        matching = [event for event in self.events if self._event_day(event) == day]
        if not matching:
            tk.Label(
                card, text="Nenhum compromisso neste dia", bg=SURFACE, fg=MUTED,
                font=(FONT, 8), anchor="w",
            ).pack(fill="x", padx=14, pady=(0, 12))
        for event in matching:
            row = tk.Frame(card, bg=SURFACE)
            row.pack(fill="x", padx=13, pady=(0, 8))
            tk.Label(row, text="•", bg=SURFACE, fg=PURPLE, font=(FONT, 13)).pack(side="left")
            when = "Dia inteiro" if event.all_day else event.start.strftime("%H:%M")
            tk.Label(
                row, text=f"{when}  {event.title}", bg=SURFACE, fg=TEXT,
                font=(FONT, 8), anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=5)
            tk.Button(
                row, text="⋮", command=lambda e=event: self._event_menu(e),
                bg=SURFACE, fg=TEXT, relief="flat", font=(FONT, 12), cursor="hand2",
            ).pack(side="right")

    @staticmethod
    def _event_day(event) -> date:
        return event.start.date() if isinstance(event.start, datetime) else event.start

    def add_event(self, day: date):
        if not self.service:
            messagebox.showinfo("Google Agenda", "Conecte sua conta antes de adicionar compromissos.")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Novo compromisso")
        dialog.geometry("390x330")
        dialog.configure(bg=SURFACE)
        dialog.transient(self)
        dialog.grab_set()
        fields = {}
        for label, default in [
            ("Título", ""), ("Data", day.strftime("%d/%m/%Y")),
            ("Início", "09:00"), ("Término", "10:00"), ("Local", ""),
        ]:
            tk.Label(dialog, text=label, bg=SURFACE, fg=TEXT, font=(FONT, 9, "bold")).pack(anchor="w", padx=24, pady=(10, 2))
            entry = tk.Entry(dialog, bg=BG, fg=TEXT, relief="flat", font=(FONT, 10))
            entry.insert(0, default)
            entry.pack(fill="x", padx=24, ipady=6)
            fields[label] = entry

        def confirm():
            try:
                selected = datetime.strptime(fields["Data"].get(), "%d/%m/%Y").date()
                start = datetime.combine(selected, time.fromisoformat(fields["Início"].get())).astimezone()
                end = datetime.combine(selected, time.fromisoformat(fields["Término"].get())).astimezone()
                draft = EventDraft(fields["Título"].get(), start, end, fields["Local"].get() or None)
                draft.validate()
            except ValueError as exc:
                messagebox.showerror("Dados inválidos", str(exc), parent=dialog)
                return
            if not messagebox.askyesno(
                "Confirmar compromisso",
                f"{draft.title}\n{selected:%d/%m/%Y}, {start:%H:%M}–{end:%H:%M}\n{draft.location or 'Sem local'}",
                parent=dialog,
            ):
                return
            run_async(
                lambda: self.service.create(draft),
                lambda event: self.after(0, lambda: (dialog.destroy(), self.refresh(), self._open_created(event))),
                lambda exc: self.after(0, lambda: messagebox.showerror("Não foi possível criar", str(exc), parent=dialog)),
            )

        tk.Button(
            dialog, text="Criar compromisso", command=confirm, bg=PURPLE, fg="white",
            activebackground="#554ec9", relief="flat", font=(FONT, 9, "bold"), pady=8,
        ).pack(fill="x", padx=24, pady=18)

    @staticmethod
    def _open_created(event):
        if event.html_link and messagebox.askyesno("Compromisso criado", "Abrir no Google Agenda?"):
            webbrowser.open(event.html_link)

    def _event_menu(self, event):
        menu = tk.Menu(self, tearoff=False)
        if event.html_link:
            menu.add_command(label="Abrir no Google Agenda", command=lambda: webbrowser.open(event.html_link))
        menu.add_command(label="Excluir", command=lambda: self.delete_event(event))
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def delete_event(self, event):
        if not self.service or not event.etag:
            return
        if event.recurring_event_id:
            messagebox.showinfo(
                "Evento recorrente",
                "Esta tela remove somente a ocorrência selecionada. Para excluir toda a série, abra o Google Agenda.",
            )
        if not messagebox.askyesno(
            "Excluir compromisso",
            f"Excluir “{event.title}” em {self._event_day(event):%d/%m/%Y}?",
        ):
            return
        run_async(
            lambda: self.service.delete(event.id, event.etag),
            lambda _: self.after(0, self.refresh),
            lambda exc: self.after(0, lambda: messagebox.showerror("Não foi possível excluir", str(exc))),
        )

    def connect(self):
        path = filedialog.askopenfilename(
            title="Selecione a credencial OAuth de aplicativo para computador",
            filetypes=[("Arquivo JSON", "*.json")],
        )
        if not path:
            return
        allow = lambda: messagebox.askyesno(
            "Chrome não encontrado", "Autoriza abrir o navegador padrão para autenticar no Google?",
        )
        run_async(
            lambda: self.oauth.connect(path, allow),
            lambda credentials: self.after(0, lambda: (self._activate(credentials), self.refresh())),
            lambda exc: self.after(0, lambda: messagebox.showerror("Falha na conexão", str(exc))),
        )

    def _activate(self, credentials):
        self.service = CalendarService(GoogleCalendarAdapter(credentials))
        self.status.set("Google Agenda conectada")

    def refresh(self):
        if not self.service:
            return
        self.status.set("Atualizando agenda…")
        run_async(
            self.service.next_seven_days,
            lambda events: self.after(0, lambda: self._show(events)),
            lambda exc: self.after(0, lambda: self._error(exc)),
        )

    def _show(self, events):
        self.events = events
        self.status.set("Google Agenda conectada")
        self.updated.set(f"Atualizada em {datetime.now().astimezone():%d/%m às %H:%M}")
        self._render_content()

    def _error(self, exc):
        self.status.set("Erro de atualização")
        messagebox.showerror("Não foi possível atualizar", str(exc))

    def _account_menu(self):
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Atualizar agora", command=self.refresh)
        menu.add_command(label="Abrir Google Agenda", command=lambda: webbrowser.open("https://calendar.google.com"))
        menu.add_separator()
        menu.add_command(label="Desconectar", command=self.disconnect)
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def disconnect(self):
        if not messagebox.askyesno("Desconectar", "Revogar o acesso e desconectar o Google Agenda?"):
            return
        run_async(
            self.oauth.disconnect,
            lambda _: self.after(0, self._disconnected),
            lambda exc: self.after(0, lambda: messagebox.showerror("Erro", str(exc))),
        )

    def _disconnected(self):
        self.service = None
        self.events = []
        self.status.set("Agenda desconectada")
        self.updated.set("Nunca atualizada")
        self._render_content()


def main():
    CalendarWindow().mainloop()
