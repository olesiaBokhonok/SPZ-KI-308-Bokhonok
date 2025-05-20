import customtkinter as ctk
from tkinter import Toplevel, Label, TclError

class CustomTooltip:
    _current_tooltip = None

    def __init__(self, widget, text):
        """Ініціалізація підказки."""
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.hide_timeout = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.reset_timer)

    def show_tooltip(self, event=None):
        """Показує підказку."""
        if CustomTooltip._current_tooltip and CustomTooltip._current_tooltip != self:
            CustomTooltip._current_tooltip.hide_tooltip()
        if isinstance(self.widget, Listbox) and self.widget.size() == 0:
            self.text = "Список порожній. Додайте файли для архівування."
        x = event.x_root + 25
        y = event.y_root + 25
        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        theme = ctk.get_appearance_mode()
        label = Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0" if theme == "Light" else "#333333",
            foreground="#000000" if theme == "Light" else "#ffffff",
            relief="solid",
            borderwidth=1,
            padx=5,
            pady=3,
            font=("Segoe UI", 10)
        )
        label.pack()
        self.hide_timeout = self.widget.after(3000, self.hide_tooltip)
        CustomTooltip._current_tooltip = self

    def hide_tooltip(self, event=None):
        """Приховує підказку."""
        if self.hide_timeout:
            self.widget.after_cancel(self.hide_timeout)
            self.hide_timeout = None
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except TclError:
                pass
            self.tooltip_window = None
        if CustomTooltip._current_tooltip == self:
            CustomTooltip._current_tooltip = None

    def reset_timer(self, event=None):
        """Скидає таймер підказки."""
        if self.hide_timeout:
            self.widget.after_cancel(self.hide_timeout)
            self.hide_timeout = self.widget.after(3000, self.hide_tooltip)
