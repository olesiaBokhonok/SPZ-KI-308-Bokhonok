import customtkinter as ctk
from tkinter import filedialog, Listbox, Scrollbar, MULTIPLE, Toplevel, Label
from tkinter import TclError
import os
import pystray
from PIL import Image
from utils import log_operation

class CustomTooltip:
    _current_tooltip = None

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.hide_timeout = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.reset_timer)

    def show_tooltip(self, event=None):
        if CustomTooltip._current_tooltip and CustomTooltip._current_tooltip != self:
            CustomTooltip._current_tooltip.hide_tooltip()
        if isinstance(self.widget, Listbox) and self.widget.size() == 0:
            self.text = "Список порожній. Додайте файли для архівування."
        x = event.x_root + 25
        y = event.y_root + 25
        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",
            foreground="#000000",
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
        if self.hide_timeout:
            self.widget.after_cancel(self.hide_timeout)
            self.hide_timeout = self.widget.after(3000, self.hide_tooltip)

class BackupAppUI:
    def __init__(self, app):
        self.app = app
        self.master = app.master
        self.files = app.files = []
        self.dest_folder = app.dest_folder = ctk.StringVar()
        self.recent_folders = app.recent_folders = self.load_recent_folders()
        self.tray_icon = None
        self.backup_name = app.backup_name = ctk.StringVar(value="")
        self.use_default_name = app.use_default_name = ctk.BooleanVar(value=True)
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.master, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.canvas = ctk.CTkCanvas(main_frame, background="#f0f0f0" if ctk.get_appearance_mode() == "Light" else "#2b2b2b")
        scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        theme_switch = ctk.CTkSwitch(self.scrollable_frame, text="Темна/Світла тема", command=self.app.toggle_theme, font=("Segoe UI", 12))
        theme_switch.pack(anchor="ne", padx=10, pady=10)
        CustomTooltip(theme_switch, "Перемкнути між темною та світлою темами")

        file_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        file_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(file_frame, text="Файли для архівування", font=("Segoe UI", 16, "bold"), text_color="#0288d1").pack(anchor="w", padx=10, pady=(10, 5))
        self.files_listbox = Listbox(file_frame, selectmode=MULTIPLE, width=60, height=8, bg="#ffffff" if ctk.get_appearance_mode() == "Light" else "#2b2b2b", fg="#263238" if ctk.get_appearance_mode() == "Light" else "white", font=("Segoe UI", 11), borderwidth=1, relief="sunken")
        self.files_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar_files = Scrollbar(file_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar_files.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        self.files_listbox.config(yscrollcommand=scrollbar_files.set)
        CustomTooltip(self.files_listbox, "Список файлів, які будуть архівовані")

        for file_path in self.files:
            self.files_listbox.insert(ctk.END, os.path.basename(file_path))

        button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        add_button = ctk.CTkButton(button_frame, text="Додати файли", command=self.app.add_files, width=150, font=("Segoe UI", 12))
        add_button.pack(side="left", padx=5)
        CustomTooltip(add_button, "Додайте файли для створення резервної копії")
        remove_button = ctk.CTkButton(button_frame, text="Видалити вибрані", command=self.app.remove_files, width=150, font=("Segoe UI", 12))
        remove_button.pack(side="left", padx=5)
        CustomTooltip(remove_button, "Видаліть вибрані файли зі списку")

        folder_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        folder_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(folder_frame, text="Цільова папка", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(folder_frame, text="Папка:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.destination_entry = ctk.CTkEntry(folder_frame, textvariable=self.dest_folder, width=400, font=("Segoe UI", 11))
        self.destination_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        CustomTooltip(self.destination_entry, "Вкажіть папку, куди зберегти резервну копію")
        browse_button = ctk.CTkButton(folder_frame, text="Обрати", command=self.app.select_folder, width=100, font=("Segoe UI", 12))
        browse_button.grid(row=1, column=2, pady=5, padx=5)
        CustomTooltip(browse_button, "Оберіть папку для збереження")

        ctk.CTkLabel(folder_frame, text="Нещодавні:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.recent_dest_combo = ctk.CTkComboBox(folder_frame, values=self.recent_folders, width=400, variable=self.dest_folder, command=self.app.use_recent_destination, font=("Segoe UI", 11))
        self.recent_dest_combo.grid(row=2, column=1, pady=(5, 10), padx=5, sticky="ew")
        CustomTooltip(self.recent_dest_combo, "Виберіть одну з нещодавно використаних папок")
        folder_frame.grid_columnconfigure(1, weight=1)

        manual_backup_button = ctk.CTkButton(self.scrollable_frame, text="Резервне копіювання зараз", command=self.app.manual_backup, font=("Segoe UI", 14), height=40, fg_color="#0288d1", hover_color="#0277bd")
        manual_backup_button.pack(fill="x", padx=10, pady=10)
        CustomTooltip(manual_backup_button, "Запустіть резервне копіювання негайно")

        encrypt_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        encrypt_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(encrypt_frame, text="Шифрування", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        self.app.encrypt = ctk.BooleanVar(value=False)
        encrypt_check = ctk.CTkCheckBox(encrypt_frame, text="Шифрувати резервні копії", variable=self.app.encrypt, font=("Segoe UI", 12))
        encrypt_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(encrypt_check, "Увімкніть шифрування для захисту резервних копій")
        ctk.CTkLabel(encrypt_frame, text="Пароль:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(encrypt_frame, text="(мін. 8 символів, літери та цифри):", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=5)
        self.app.passwd = ctk.StringVar(value="")
        self.password_entry = ctk.CTkEntry(encrypt_frame, show="*", width=250, font=("Segoe UI", 11), textvariable=self.app.passwd)
        self.password_entry.grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 10), padx=10)
        CustomTooltip(self.password_entry, "Введіть пароль для шифрування (мін. 8 символів, літери та цифри)")

        decrypt_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        decrypt_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(decrypt_frame, text="Розшифрування", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(decrypt_frame, text="Файл:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.app.decrypt_file = ctk.StringVar()
        self.decrypt_file_entry = ctk.CTkEntry(decrypt_frame, textvariable=self.app.decrypt_file, width=400, font=("Segoe UI", 11))
        self.decrypt_file_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        CustomTooltip(self.decrypt_file_entry, "Вкажіть зашифрований файл для розшифрування")
        browse_decrypt_button = ctk.CTkButton(decrypt_frame, text="Обрати файл", command=self.app.select_decrypt_file, width=150, font=("Segoe UI", 12))
        browse_decrypt_button.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(browse_decrypt_button, "Оберіть зашифрований файл")
        ctk.CTkLabel(decrypt_frame, text="Пароль:", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(decrypt_frame, text="(мін. 8 символів, літери та цифри):", font=("Segoe UI", 10)).grid(row=3, column=1, sticky="w", padx=5)
        self.decrypt_password_entry = ctk.CTkEntry(decrypt_frame, show="*", width=250, font=("Segoe UI", 11))
        self.decrypt_password_entry.grid(row=4, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        CustomTooltip(self.decrypt_password_entry, "Введіть пароль для розшифрування")
        decrypt_button = ctk.CTkButton(decrypt_frame, text="Розшифрувати", command=self.app.decrypt_backup, width=150, font=("Segoe UI", 12))
        decrypt_button.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 10))
        CustomTooltip(decrypt_button, "Розшифруйте вибраний файл")
        decrypt_frame.grid_columnconfigure(1, weight=1)

        schedule_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        schedule_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(schedule_frame, text="Розклад резервного копіювання", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        self.app.schedule_on = ctk.BooleanVar(value=False)
        schedule_check = ctk.CTkCheckBox(schedule_frame, text="Увімкнути резервне копіювання за розкладом", variable=self.app.schedule_on, font=("Segoe UI", 12))
        schedule_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(schedule_check, "Увімкніть автоматичне резервне копіювання за розкладом")
        ctk.CTkLabel(schedule_frame, text="Інтервал:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        schedule_options = ["Щогодини", "Кожні 5 годин", "Кожні 10 годин"]
        self.app.interval = ctk.StringVar(value="Щогодини")
        self.schedule_combo = ctk.CTkComboBox(schedule_frame, values=schedule_options, variable=self.app.interval, width=150, font=("Segoe UI", 11))
        self.schedule_combo.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        CustomTooltip(self.schedule_combo, "Виберіть інтервал для автоматичного копіювання")
        ctk.CTkLabel(schedule_frame, text="Час (HH:MM):", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.app.backup_time = ctk.StringVar(value="00:00")
        self.time_entry = ctk.CTkEntry(schedule_frame, textvariable=self.app.backup_time, width=100, font=("Segoe UI", 11))
        self.time_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        CustomTooltip(self.time_entry, "Вкажіть час у форматі HH:MM (наприклад, 14:00)")
        start_schedule_button = ctk.CTkButton(schedule_frame, text="Запустити розклад", command=self.app.start_schedule, width=150, font=("Segoe UI", 12))
        start_schedule_button.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 10))
        CustomTooltip(start_schedule_button, "Запустіть автоматичне копіювання за заданим розкладом")

        name_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        name_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(name_frame, text="Назва резервної копії", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(name_frame, text="Назва:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.backup_name_entry = ctk.CTkEntry(name_frame, textvariable=self.backup_name, width=400, font=("Segoe UI", 11))
        self.backup_name_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        CustomTooltip(self.backup_name_entry, "Введіть власну назву для резервної копії (без розширення)")
        default_name_check = ctk.CTkCheckBox(name_frame, text="Використовувати назву 'backup' за замовчуванням", variable=self.use_default_name, font=("Segoe UI", 12), command=self.app.toggle_default_name)
        default_name_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(default_name_check, "Увімкніть, щоб використовувати назву 'backup' за замовчуванням")
        name_frame.grid_columnconfigure(1, weight=1)

        minimize_button = ctk.CTkButton(self.scrollable_frame, text="Мінімізувати в трей", command=self.app.minimize_to_tray, font=("Segoe UI", 14), height=40, fg_color="#0288d1", hover_color="#0277bd")
        minimize_button.pack(fill="x", padx=10, pady=10)
        CustomTooltip(minimize_button, "Мінімізувати програму в системний трей")

        stop_button = ctk.CTkButton(self.scrollable_frame, text="Зупинити програму", command=self.app.stop_program, font=("Segoe UI", 14), height=40, fg_color="#d32f2f", hover_color="#b71c1c")
        stop_button.pack(fill="x", padx=10, pady=10)
        CustomTooltip(stop_button, "Закрити програму")

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Dark" if current_mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.canvas.configure(background="#f0f0f0" if new_mode == "Light" else "#2b2b2b")
        self.files_listbox.configure(bg="#ffffff" if new_mode == "Light" else "#2b2b2b", fg="#263238" if new_mode == "Light" else "white")
        log_operation(f"Змінено тему на {new_mode}")

    def minimize_to_tray(self):
        self.save_config()
        self.master.withdraw()
        if not self.tray_icon:
            try:
                image = Image.open("icon.png")
            except FileNotFoundError:
                log_operation("Файл icon.png не знайдено, використовується заглушка.")
                image = Image.new('RGB', (64, 64), color='blue')
            menu = pystray.Menu(
                pystray.MenuItem("Відкрити", self.app.restore_from_tray),
                pystray.MenuItem("Вийти", self.app.stop_program)
            )
            self.tray_icon = pystray.Icon("backup_app", image, "Backup App", menu)
            self.tray_icon.run_detached()
        log_operation("Програму мінімізовано в трей")

    def restore_from_tray(self):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.master.deiconify()
        log_operation("Програму відновлено з трею")

    def add_files(self):
        filepaths = filedialog.askopenfilenames(title="Виберіть файли для архівування")
        for filepath in filepaths:
            if filepath not in self.files:
                self.files.append(filepath)
                filename = os.path.basename(filepath)
                self.files_listbox.insert(ctk.END, filename)
        if filepaths:
            self.save_config()
            log_operation(f"Додано файли: {', '.join([os.path.basename(f) for f in filepaths])}")

    def remove_files(self):
        selected_indices = self.files_listbox.curselection()
        if selected_indices:
            removed_files = [self.files[i] for i in selected_indices]
            for index in reversed(selected_indices):
                del self.files[index]
                self.files_listbox.delete(index)
            self.save_config()
            log_operation(f"Видалено файли: {', '.join([os.path.basename(f) for f in removed_files])}")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Виберіть цільову папку")
        if folder:
            self.dest_folder.set(folder)
            self.update_recent_folders(folder)
            self.save_config()
            log_operation(f"Вибрано цільову папку: {folder}")

    def use_recent_destination(self, selected_folder):
        self.dest_folder.set(selected_folder)
        self.save_config()
        log_operation(f"Вибрано нещодавню папку: {selected_folder}")

    def load_recent_folders(self):
        try:
            with open("recent_destinations.txt", "r", encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            return []
        except Exception as e:
            log_operation(f"Помилка при завантаженні недавніх папок: {e}")
            return []

    def update_recent_folders(self, folder):
        if folder and folder not in self.recent_folders:
            self.recent_folders.insert(0, folder)
            if len(self.recent_folders) > 5:
                self.recent_folders.pop()
            self.recent_dest_combo.configure(values=self.recent_folders)
            self.save_recent_folders()

    def save_recent_folders(self):
        try:
            with open("recent_destinations.txt", "w", encoding='utf-8') as f:
                for folder in self.recent_folders:
                    f.write(f"{folder}\n")
        except Exception as e:
            log_operation(f"Помилка при збереженні недавніх папок: {e}")

    def load_config(self):
        try:
            with open("backup_config.json", "r", encoding="utf-8") as f:
                state = json.load(f)
            self.files = self.app.files = state.get("files", [])
            self.dest_folder.set(state.get("dest_folder", ""))
            self.app.schedule_on.set(state.get("schedule_on", False))
            self.app.interval.set(state.get("interval", "Щогодини"))
            self.app.backup_time.set(state.get("backup_time", "00:00"))
            self.app.encrypt.set(state.get("encrypt", False))
            self.app.passwd.set(state.get("passwd", ""))
            self.backup_name.set(state.get("backup_name", ""))
            self.use_default_name.set(state.get("use_default_name", True))
            for file_path in self.files:
                self.files_listbox.insert(ctk.END, os.path.basename(file_path))
        except FileNotFoundError:
            pass
        except Exception as e:
            log_operation(f"Помилка при завантаженні стану: {e}")

    def save_config(self):
        state = {
            "files": self.files,
            "dest_folder": self.dest_folder.get(),
            "schedule_on": self.app.schedule_on.get(),
            "interval": self.app.interval.get(),
            "backup_time": self.app.backup_time.get(),
            "encrypt": self.app.encrypt.get(),
            "passwd": self.app.passwd.get(),
            "backup_name": self.backup_name.get(),
            "use_default_name": self.use_default_name.get()
        }
        try:
            with open("backup_config.json", "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
        except Exception as e:
            log_operation(f"Помилка при збереженні стану: {e}")

    def toggle_default_name(self):
        if self.use_default_name.get():
            self.backup_name.set("")
        self.save_config()
