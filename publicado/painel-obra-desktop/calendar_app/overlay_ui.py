from __future__ import annotations

import ctypes
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox
from zoneinfo import ZoneInfo

from .board import BoardStore
from .google_adapter import GoogleCalendarAdapter
from .ai_parser import AppointmentParser, ParsedAppointment
from .models import EventDraft
from .oauth import OAuthManager
from .publish import publish
from .service import CalendarService, run_async
from .suggestions import SuggestionStore

PANEL_WIDTH = 360
TOP_GAP = 8
BOTTOM_GAP = 8
PURPLE = "#5b3df5"
TEXT = "#242331"
MUTED = "#777786"
SURFACE = "#f7f7fb"
CARD = "#ffffff"
LINE = "#e7e6ee"
FONT = "Segoe UI"


def work_area() -> tuple[int, int, int, int]:
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    rect = RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom


class AgendaOverlay(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.oauth = OAuthManager()
        self.service: CalendarService | None = None
        self.events = []
        self.parser: AppointmentParser | None = None
        self.suggestions = SuggestionStore()
        self.board = BoardStore()
        self.notification_count = 0
        self.panel_open = False
        self.animating = False
        self.left, self.top, self.right, self.bottom = work_area()
        self.panel_height = self.bottom - self.top - TOP_GAP - BOTTOM_GAP
        self.closed_x = self.right
        self.open_x = self.right - PANEL_WIDTH
        self.status = tk.StringVar(value="Conectar Google Agenda")
        self.updated = tk.StringVar(value="")
        self._build_overlay()
        self._build_panel()
        self._build_trigger()
        self._restore()
        self._poll_notifications()

    def _build_overlay(self):
        self.overlay = tk.Toplevel(self)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.12)
        self.overlay.configure(bg="black")
        self.overlay.geometry(f"{self.right - self.left}x{self.bottom - self.top}+{self.left}+{self.top}")
        self.overlay.bind("<Button-1>", lambda _event: self.close_panel())

    def _build_trigger(self):
        self.trigger = tk.Toplevel(self)
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.attributes("-alpha", 0.84)
        self.trigger.configure(bg="#ebeaf1")
        trigger_width = 22
        trigger_height = 56
        trigger_x = self.right - trigger_width
        trigger_y = self.top + ((self.bottom - self.top - trigger_height) // 2)
        self.trigger.geometry(f"{trigger_width}x{trigger_height}+{trigger_x}+{trigger_y}")
        button = tk.Button(
            self.trigger, text="◀", command=self.open_panel, bg="#ebeaf1", fg=PURPLE,
            activebackground="#dedce8", activeforeground=PURPLE, relief="flat",
            bd=0, font=(FONT, 8, "bold"), cursor="hand2",
        )
        button.pack(fill="both", expand=True)
        self._round_window(self.trigger, 12)

        self.badge = tk.Toplevel(self)
        self.badge.withdraw()
        self.badge.overrideredirect(True)
        self.badge.attributes("-topmost", True)
        self.badge.configure(bg="#e5484d")
        self.badge.geometry(f"22x22+{self.right - 38}+{trigger_y - 7}")
        self.badge_label = tk.Label(
            self.badge, text="", bg="#e5484d", fg="white",
            font=(FONT, 7, "bold"), cursor="hand2",
        )
        self.badge_label.pack(fill="both", expand=True)
        self.badge_label.bind("<Button-1>", lambda _event: self.open_panel())
        self._round_window(self.badge, 22)

    def _build_panel(self):
        self.panel = tk.Toplevel(self)
        self.panel.withdraw()
        self.panel.overrideredirect(True)
        self.panel.attributes("-topmost", True)
        self.panel.attributes("-alpha", 0.96)
        self.panel.configure(bg=SURFACE)
        self.panel.geometry(f"{PANEL_WIDTH}x{self.panel_height}+{self.closed_x}+{self.top + TOP_GAP}")
        self.panel.bind("<Escape>", lambda _event: self.close_panel())

        puller = tk.Button(
            self.panel, text="▶", command=self.toggle_panel, bg="#f0eff8", fg=PURPLE,
            activebackground="#e7e5f5", activeforeground=PURPLE, relief="flat",
            font=(FONT, 9, "bold"), cursor="hand2", bd=0,
        )
        puller.place(x=0, rely=0.5, anchor="w", width=23, height=56)

        body = tk.Frame(self.panel, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=(23, 0))

        header = tk.Frame(body, bg=SURFACE, height=54)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="AGENDA", bg=SURFACE, fg=PURPLE, font=(FONT, 10, "bold")).pack(side="left", padx=18)
        tk.Button(
            header, text="»", command=self.close_panel, bg=SURFACE, fg=TEXT,
            activebackground=SURFACE, relief="flat", bd=0, font=(FONT, 16), cursor="hand2",
        ).pack(side="right", padx=12)

        tabs = tk.Frame(body, bg=SURFACE)
        tabs.pack(fill="x", padx=13)
        for index, name in enumerate(("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")):
            tk.Label(
                tabs, text=name, bg=SURFACE, fg=PURPLE if index == date.today().weekday() else TEXT,
                font=(FONT, 8, "bold" if index == date.today().weekday() else "normal"),
                pady=8,
            ).pack(side="left", expand=True)
        tk.Frame(body, bg=LINE, height=1).pack(fill="x")

        self.goal_cards = tk.Frame(body, bg=SURFACE)
        self.goal_cards.pack(fill="x", padx=12, pady=(12, 0))
        self.open_items_frame = tk.Frame(body, bg=SURFACE)
        self.open_items_frame.pack(fill="x", padx=12, pady=(8, 12))
        self._render_board()

        canvas_host = tk.Frame(body, bg=SURFACE)
        canvas_host.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_host, bg=SURFACE, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_host, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=SURFACE)
        self.list_frame.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.list_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.list_window, width=event.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        chat = tk.Frame(body, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        chat.pack(fill="x", padx=12, pady=(8, 4))
        self.chat_input = tk.Entry(
            chat, bg=CARD, fg=TEXT, relief="flat", bd=0, font=(FONT, 8),
        )
        self.chat_input.insert(0, "Ex: reunião com o cliente amanhã às 14h")
        self.chat_input.configure(fg=MUTED)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(10, 4), ipady=8)
        self.chat_input.bind("<FocusIn>", self._clear_placeholder)
        self.chat_input.bind("<FocusOut>", self._restore_placeholder)
        self.chat_input.bind("<Return>", lambda _event: self.send_chat())
        self.send_button = tk.Button(
            chat, text="Enviar", command=self.send_chat, bg=PURPLE, fg="white",
            activebackground="#4930d6", activeforeground="white", relief="flat",
            bd=0, font=(FONT, 8, "bold"), cursor="hand2", padx=10, pady=7,
        )
        self.send_button.pack(side="right", padx=4, pady=4)
        self.chat_message = tk.StringVar(value="")
        tk.Label(
            body, textvariable=self.chat_message, bg=SURFACE, fg=MUTED,
            font=(FONT, 7), anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 4))

        footer = tk.Frame(body, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        footer.pack(fill="x")
        tk.Button(
            footer, textvariable=self.status, command=self.connect_or_refresh,
            bg=PURPLE, fg="white", activebackground="#4930d6", activeforeground="white",
            relief="flat", bd=0, font=(FONT, 9, "bold"), cursor="hand2", pady=10,
        ).pack(fill="x", padx=18, pady=(12, 4))
        self.publish_message = tk.StringVar(value="")
        tk.Button(
            footer, text="Publicar painel", command=self.publish_panel, bg=SURFACE, fg=PURPLE,
            activebackground=SURFACE, activeforeground=PURPLE, relief="flat", bd=1,
            highlightbackground=LINE, font=(FONT, 8, "bold"), cursor="hand2", pady=7,
        ).pack(fill="x", padx=18, pady=(0, 4))
        tk.Label(footer, textvariable=self.publish_message, bg=SURFACE, fg=MUTED, font=(FONT, 7)).pack(pady=(0, 4))
        tk.Label(footer, textvariable=self.updated, bg=SURFACE, fg=MUTED, font=(FONT, 7)).pack(pady=(0, 8))
        self._render_days()

    def _render_board(self):
        for child in self.goal_cards.winfo_children():
            child.destroy()
        for child in self.open_items_frame.winfo_children():
            child.destroy()
        self._goal_card(self.goal_cards, "◎", "Metas da semana", "semana")
        self._goal_card(self.goal_cards, "▣", "Metas gerais", "geral")
        self._open_items_card(self.open_items_frame)

    def _goal_card(self, parent, icon: str, title: str, period: str):
        card = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=4)
        head = tk.Frame(card, bg=CARD)
        head.pack(fill="x", padx=9, pady=(9, 5))
        tk.Label(head, text=icon, bg=CARD, fg=PURPLE, font=(FONT, 13)).pack(side="left")
        add_link = tk.Label(head, text="+", bg=CARD, fg=PURPLE, font=(FONT, 11, "bold"), cursor="hand2")
        add_link.pack(side="right")
        add_link.bind("<Button-1>", lambda _e, p=period: self._add_goal(p))
        tk.Label(card, text=title, bg=CARD, fg=TEXT, font=(FONT, 8, "bold"), anchor="w").pack(fill="x", padx=9)
        goals = self.board.goals(period)
        if not goals:
            tk.Label(card, text="○  Nenhuma meta", bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w").pack(fill="x", padx=9, pady=2)
        for goal in goals:
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", padx=9, pady=2)
            tk.Label(row, text=f"○  {goal['label']}", bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w").pack(side="left", fill="x", expand=True)
            remove = tk.Label(row, text="×", bg=CARD, fg=MUTED, font=(FONT, 8), cursor="hand2")
            remove.pack(side="right")
            remove.bind("<Button-1>", lambda _e, g=goal["id"]: self._remove_goal(g))
        tk.Frame(card, bg=CARD, height=7).pack()

    def _open_items_card(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        card.pack(fill="x")
        head = tk.Frame(card, bg=CARD)
        head.pack(fill="x", padx=9, pady=(9, 5))
        tk.Label(head, text="Itens em aberto", bg=CARD, fg=TEXT, font=(FONT, 8, "bold")).pack(side="left")
        add_link = tk.Label(head, text="+ Adicionar item", bg=CARD, fg=PURPLE, font=(FONT, 7), cursor="hand2")
        add_link.pack(side="right")
        add_link.bind("<Button-1>", lambda _e: self._add_open_item())
        items = self.board.open_items()
        if not items:
            tk.Label(card, text="Nenhum item em aberto", bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w").pack(fill="x", padx=9, pady=(0, 9))
        for item in items:
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", padx=9, pady=2)
            mark = "✓" if item["done"] else "○"
            label = tk.Label(row, text=f"{mark}  {item['label']}", bg=CARD, fg=MUTED, font=(FONT, 7), anchor="w", cursor="hand2")
            label.pack(side="left", fill="x", expand=True)
            label.bind("<Button-1>", lambda _e, i=item["id"]: self._toggle_open_item(i))
            remove = tk.Label(row, text="×", bg=CARD, fg=MUTED, font=(FONT, 8), cursor="hand2")
            remove.pack(side="right")
            remove.bind("<Button-1>", lambda _e, i=item["id"]: self._remove_open_item(i))
        tk.Frame(card, bg=CARD, height=7).pack()

    def _add_goal(self, period: str):
        title = "Nova meta da semana" if period == "semana" else "Nova meta geral"
        self._prompt(title, lambda text: (self.board.add_goal(text, period), self._render_board()))

    def _remove_goal(self, goal_id: int):
        self.board.remove_goal(goal_id)
        self._render_board()

    def _add_open_item(self):
        self._prompt("Novo item em aberto", lambda text: (self.board.add_open_item(text), self._render_board()))

    def _toggle_open_item(self, item_id: int):
        self.board.toggle_open_item(item_id)
        self._render_board()

    def _remove_open_item(self, item_id: int):
        self.board.remove_open_item(item_id)
        self._render_board()

    def _prompt(self, title: str, on_confirm):
        dialog = tk.Toplevel(self.panel)
        dialog.title(title)
        dialog.configure(bg=CARD, padx=14, pady=12)
        dialog.transient(self.panel)
        dialog.resizable(False, False)
        tk.Label(dialog, text=title, bg=CARD, fg=PURPLE, font=(FONT, 9, "bold")).pack(anchor="w", pady=(0, 8))
        entry = tk.Entry(dialog, width=32, font=(FONT, 9))
        entry.pack(fill="x")
        feedback = tk.Label(dialog, text="", bg=CARD, fg="#c0392b", font=(FONT, 8))
        feedback.pack(anchor="w", pady=(4, 0))

        def save():
            try:
                on_confirm(entry.get())
            except ValueError as error:
                feedback.configure(text=str(error))
                return
            dialog.destroy()

        buttons = tk.Frame(dialog, bg=CARD)
        buttons.pack(anchor="e", pady=(10, 0))
        tk.Button(
            buttons, text="Cancelar", command=dialog.destroy, bg=CARD, fg=MUTED,
            relief="flat", font=(FONT, 8), cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            buttons, text="Salvar", command=save, bg=PURPLE, fg="#ffffff",
            relief="flat", font=(FONT, 8, "bold"), cursor="hand2", padx=12,
        ).pack(side="left")
        entry.focus_set()
        dialog.grab_set()

    def _render_days(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        today = date.today()
        for offset in range(7):
            day = today + timedelta(days=offset)
            names = ("SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO")
            card = tk.Frame(self.list_frame, bg=CARD, highlightbackground=LINE, highlightthickness=1)
            card.pack(fill="x", padx=16, pady=5)
            header = tk.Frame(card, bg=CARD)
            header.pack(fill="x", padx=11, pady=(10, 6))
            tk.Label(
                header, text=f"{names[day.weekday()]}  •  {day:%d/%m}",
                bg=CARD, fg=PURPLE, font=(FONT, 7, "bold"),
            ).pack(side="left")
            add_link = tk.Label(
                header, text="+ Adicionar item", bg=CARD, fg=PURPLE,
                font=(FONT, 7), cursor="hand2",
            )
            add_link.pack(side="right")
            add_link.bind("<Button-1>", lambda _e, d=day: self._add_item(d))
            matching = [event for event in self.events if self._event_date(event) == day]
            if not matching:
                tk.Label(
                    card, text="Nenhum compromisso neste dia", bg=CARD, fg=MUTED,
                    font=(FONT, 7), anchor="w",
                ).pack(fill="x", padx=11, pady=(0, 9))
            for event in matching:
                if event.all_day:
                    when = "Dia inteiro"
                else:
                    local_start = event.start.astimezone() if event.start.tzinfo else event.start
                    when = local_start.strftime("%H:%M")
                tk.Label(
                    card, text=f"•  {when}  {event.title}", bg=CARD, fg=TEXT,
                    font=(FONT, 7), anchor="w",
                ).pack(fill="x", padx=11, pady=(0, 7))

    @staticmethod
    def _event_date(event):
        if isinstance(event.start, datetime):
            start = event.start.astimezone() if event.start.tzinfo else event.start
            return start.date()
        return event.start

    def _add_item(self, day: date):
        if not self.service:
            self.chat_message.set("Conecte o Google Agenda primeiro.")
            return
        dialog = tk.Toplevel(self.panel)
        dialog.title("Novo compromisso")
        dialog.configure(bg=CARD, padx=14, pady=12)
        dialog.transient(self.panel)
        dialog.resizable(False, False)
        names = ("SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO")
        tk.Label(
            dialog, text=f"{names[day.weekday()]}  •  {day:%d/%m/%Y}",
            bg=CARD, fg=PURPLE, font=(FONT, 9, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(dialog, text="Título", bg=CARD, fg=TEXT, font=(FONT, 8)).grid(row=1, column=0, sticky="w")
        title_entry = tk.Entry(dialog, width=32, font=(FONT, 9))
        title_entry.grid(row=1, column=1, padx=(8, 0), pady=2)
        tk.Label(dialog, text="Início (HH:MM)", bg=CARD, fg=TEXT, font=(FONT, 8)).grid(row=2, column=0, sticky="w")
        start_entry = tk.Entry(dialog, width=10, font=(FONT, 9))
        start_entry.insert(0, "09:00")
        start_entry.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=2)
        tk.Label(dialog, text="Término (HH:MM)", bg=CARD, fg=TEXT, font=(FONT, 8)).grid(row=3, column=0, sticky="w")
        end_entry = tk.Entry(dialog, width=10, font=(FONT, 9))
        end_entry.insert(0, "10:00")
        end_entry.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=2)
        feedback = tk.Label(dialog, text="", bg=CARD, fg="#c0392b", font=(FONT, 8))
        feedback.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def save():
            title = title_entry.get().strip()
            try:
                start_time = datetime.strptime(start_entry.get().strip(), "%H:%M").time()
                end_time = datetime.strptime(end_entry.get().strip(), "%H:%M").time()
            except ValueError:
                feedback.configure(text="Use o formato HH:MM, ex: 14:30.")
                return
            tz = ZoneInfo("America/Sao_Paulo")
            draft = EventDraft(
                title,
                datetime.combine(day, start_time, tz),
                datetime.combine(day, end_time, tz),
            )
            try:
                draft.validate()
            except ValueError as error:
                feedback.configure(text=str(error))
                return
            feedback.configure(text="Adicionando…", fg=MUTED)
            run_async(
                lambda: self.service.create(draft),
                lambda _event: self.after(0, lambda: (dialog.destroy(), self.refresh())),
                lambda exc: self.after(0, lambda: feedback.configure(text=str(exc), fg="#c0392b")),
            )

        buttons = tk.Frame(dialog, bg=CARD)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(10, 0))
        tk.Button(
            buttons, text="Cancelar", command=dialog.destroy, bg=CARD, fg=MUTED,
            relief="flat", font=(FONT, 8), cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            buttons, text="Adicionar", command=save, bg=PURPLE, fg="#ffffff",
            relief="flat", font=(FONT, 8, "bold"), cursor="hand2", padx=12,
        ).pack(side="left")
        dialog.update_idletasks()
        x = self.panel.winfo_rootx() - dialog.winfo_width() - 12
        y = self.panel.winfo_rooty() + 120
        dialog.geometry(f"+{max(x, 20)}+{y}")
        title_entry.focus_set()
        dialog.grab_set()

    def open_panel(self):
        if self.panel_open or self.animating:
            return
        self.panel_open = True
        self.animating = True
        self.trigger.withdraw()
        self.badge.withdraw()
        self.overlay.deiconify()
        self.panel.deiconify()
        self.panel.lift()
        self._animate(self.closed_x, self.open_x)

    def close_panel(self):
        if not self.panel_open or self.animating:
            return
        self.panel_open = False
        self.animating = True
        self._animate(self.open_x, self.closed_x, hide=True)

    def toggle_panel(self):
        self.close_panel() if self.panel_open else self.open_panel()

    def _animate(self, start: int, end: int, hide: bool = False):
        steps = 16
        duration_ms = 350

        def frame(index: int):
            progress = index / steps
            eased = 1 - (1 - progress) ** 3
            x = round(start + (end - start) * eased)
            self.panel.geometry(f"{PANEL_WIDTH}x{self.panel_height}+{x}+{self.top + TOP_GAP}")
            if index < steps:
                self.after(duration_ms // steps, lambda: frame(index + 1))
            else:
                self.animating = False
                if hide:
                    self.panel.withdraw()
                    self.overlay.withdraw()
                    self.trigger.deiconify()
                    self._show_badge()

        frame(0)

    def _restore(self):
        credentials = self.oauth.credentials()
        if credentials:
            self.service = CalendarService(GoogleCalendarAdapter(credentials))
            self.status.set("Atualizar agora")
            self.refresh()

    def connect_or_refresh(self):
        if self.service:
            self.refresh()
        else:
            self.connect()

    def _clear_placeholder(self, _event=None):
        if self.chat_input.get() == "Ex: reunião com o cliente amanhã às 14h":
            self.chat_input.delete(0, tk.END)
            self.chat_input.configure(fg=TEXT)

    def _restore_placeholder(self, _event=None):
        if not self.chat_input.get().strip():
            self.chat_input.insert(0, "Ex: reunião com o cliente amanhã às 14h")
            self.chat_input.configure(fg=MUTED)

    def send_chat(self):
        text = self.chat_input.get().strip()
        if not text or text == "Ex: reunião com o cliente amanhã às 14h":
            self.chat_message.set("Digite um compromisso.")
            return
        if not self.service:
            self.chat_message.set("Conecte o Google Agenda primeiro.")
            return
        self.chat_message.set("Interpretando…")
        self.send_button.configure(state="disabled")

        def parse():
            if self.parser is None:
                self.parser = AppointmentParser()
            return self.parser.parse(text)

        run_async(
            parse,
            lambda result: self.after(0, lambda: self._confirm_ai_event(result)),
            lambda exc: self.after(0, lambda: self._chat_error(exc)),
        )

    def _confirm_ai_event(self, result: ParsedAppointment):
        self.send_button.configure(state="normal")
        dias = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                "sexta-feira", "sábado", "domingo")
        message = (
            f"{result.title}\n"
            f"{dias[result.start.weekday()]}, {result.start:%d/%m/%Y}\n"
            f"{result.start:%H:%M}–{result.end:%H:%M}\n\n"
            "Adicionar à agenda principal?"
        )
        if not messagebox.askyesno("Confirmar compromisso", message, parent=self.panel):
            self.chat_message.set("Compromisso não adicionado.")
            return
        self.chat_message.set("Adicionando à agenda…")
        draft = EventDraft(result.title, result.start, result.end)
        run_async(
            lambda: self.service.create(draft),
            lambda _event: self.after(0, self._chat_created),
            lambda exc: self.after(0, lambda: self._chat_error(exc)),
        )

    def _chat_created(self):
        self.chat_input.delete(0, tk.END)
        self.chat_input.configure(fg=TEXT)
        self.chat_message.set("Compromisso adicionado.")
        self.refresh()

    def _chat_error(self, exc: Exception | None = None):
        self.send_button.configure(state="normal")
        error_text = str(exc or "").lower()
        if "insufficient_quota" in error_text or "current quota" in error_text:
            self.chat_message.set("API sem créditos. Ative o faturamento.")
        elif isinstance(exc, ValueError) and str(exc):
            self.chat_message.set(str(exc))
        else:
            self.chat_message.set("Não entendi, tente novamente.")

    def connect(self):
        path = filedialog.askopenfilename(
            parent=self.panel,
            title="Selecione a credencial OAuth de aplicativo para computador",
            filetypes=[("Arquivo JSON", "*.json")],
        )
        if not path:
            return
        allow = lambda: messagebox.askyesno(
            "Chrome não encontrado", "Autoriza abrir o navegador padrão?", parent=self.panel,
        )
        self.status.set("Conectando…")
        run_async(
            lambda: self.oauth.connect(path, allow),
            lambda credentials: self.after(0, lambda: self._connected(credentials)),
            lambda exc: self.after(0, lambda: self._show_error("Falha na conexão", exc)),
        )

    def _connected(self, credentials):
        self.service = CalendarService(GoogleCalendarAdapter(credentials))
        self.status.set("Atualizar agora")
        self.refresh()

    def refresh(self):
        if not self.service:
            return
        self.status.set("Atualizando…")
        run_async(
            self.service.next_seven_days,
            lambda events: self.after(0, lambda: self._show_events(events)),
            lambda exc: self.after(0, lambda: self._show_error("Falha na atualização", exc)),
        )

    def _show_events(self, events):
        self.events = events
        self.board.store_synced_events(events)
        self.status.set("Atualizar agora")
        self.updated.set(f"Última atualização: {datetime.now():%d/%m/%Y %H:%M}")
        self._render_days()

    def publish_panel(self):
        try:
            out_file = publish(self.board)
        except OSError as error:
            self.publish_message.set(f"Falha ao publicar: {error}")
            return
        self.publish_message.set(f"Publicado: {out_file}")

    def _show_error(self, title: str, error: Exception):
        self.status.set("Tentar novamente")
        messagebox.showerror(title, str(error), parent=self.panel)

    def _poll_notifications(self):
        count = self.suggestions.pending_count()
        if count != self.notification_count:
            self.notification_count = count
            self.badge_label.configure(text="99+" if count > 99 else str(count))
        self._show_badge()
        self.after(30_000, self._poll_notifications)

    def _show_badge(self):
        if self.notification_count > 0 and not self.panel_open:
            self.badge.deiconify()
            self.badge.lift()
        else:
            self.badge.withdraw()

    @staticmethod
    def _round_window(window, radius: int):
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        width = window.winfo_width()
        height = window.winfo_height()
        region = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, width + 1, height + 1, radius, radius)
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)


def main():
    app = AgendaOverlay()
    app.mainloop()
