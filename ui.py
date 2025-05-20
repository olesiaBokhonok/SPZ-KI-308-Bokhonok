import customtkinter as ctk
from tkinter import filedialog, Listbox, Scrollbar, MULTIPLE
import os
import json
from PIL import Image
import pystray
import logging
from tooltip import CustomTooltip

class BackupAppUI:
    def __init__(self, app):
        """Ініціалізація модуля інтерфейсу."""
        self.app = app
        self.master = app.master
        self.files = app.files
        self.dest_folder = app.dest_folder
        self.recent_folders = app.recent_folders
        self.tray_icon = app.tray_icon
        self.backup_name = app.backup_name
        self.use_default_name = app.use_default_name
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        """Створює графічні елементи інтерфейсу."""
        theme = ctk.get_appearance_mode()
        frame_bg = "#f0f0f0" if theme == "Light" else "#2b2b2b"
        canvas_bg = "#f0f0f0" if theme == "Light" else "#2b2b2b"
        listbox_bg = "#ffffff" if theme == "Light" else "#333333"
        listbox_fg = "#263238" if theme == "Light" else "#ffffff"
        scrollbar_bg = "#d9d9d9" if theme == "Light" else "#444444"

        # Основний контейнер для всіх елементів
        self.main_frame = ctk.CTkFrame(self.master, fg_color=frame_bg)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Створення полотна для прокрутки
        self.canvas = ctk.CTkCanvas(self.main_frame, background=canvas_bg)
        self.scrollbar = ctk.CTkScrollbar(self.main_frame, orientation="vertical", command=self.canvas.yview, fg_color=scrollbar_bg)
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color=frame_bg)

        # Налаштування прокрутки для canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Перемикач тем
        theme_switch = ctk.CTkSwitch(self.scrollable_frame, text="Темна/Світла тема", command=self.app.toggle_theme, font=("Segoe UI", 12))
        theme_switch.pack(anchor="ne", padx=10, pady=10)
        CustomTooltip(theme_switch, "Перемкнути між темною та світлою темами")

        # Секція для вибору файлів
        self.file_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=frame_bg)
        self.file_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.file_frame, text="Файли для архівування", font=("Segoe UI", 16, "bold"), text_color="#0288d1").pack(anchor="w", padx=10, pady=(10, 5))
        self.files_listbox = Listbox(self.file_frame, selectmode=MULTIPLE, width=60, height=8, bg=listbox_bg, fg=listbox_fg, font=("Segoe UI", 11), borderwidth=1, relief="sunken", highlightthickness=0)
        self.files_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        self.scrollbar_files = Scrollbar(self.file_frame, orient="vertical", command=self.files_listbox.yview, bg=scrollbar_bg)
        self.scrollbar_files.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        self.files_listbox.config(yscrollcommand=self.scrollbar_files.set)
        CustomTooltip(self.files_listbox, "Список файлів, які будуть архівовані")

        # Заповнення списку файлів
        for file_path in self.files:
            self.files_listbox.insert(ctk.END, os.path.basename(file_path))

        # Кнопки для додавання та видалення файлів
        self.button_frame = ctk.CTkFrame(self.file_frame, fg_color=frame_bg)
        self.button_frame.pack(fill="x", padx=10, pady=(0, 10))
        add_button = ctk.CTkButton(self.button_frame, text="Додати файли", command=self.app.add_files, width=150, font=("Segoe UI", 12))
        add_button.pack(side="left", padx=5)
        CustomTooltip(add_button, "Додайте файли для створення резервної копії")
        remove_button = ctk.CTkButton(self.button_frame, text="Видалити вибрані", command=self.app.remove_files, width=150, font=("Segoe UI", 12))
        remove_button.pack(side="left", padx=5)
        CustomTooltip(remove_button, "Видаліть вибрані файли зі списку")

        # Секція для назви резервної копії
        self.name_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=frame_bg)
        self.name_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.name_frame, text="Назва резервної копії", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(self.name_frame, text="Назва:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.backup_name_entry = ctk.CTkEntry(self.name_frame, textvariable=self.backup_name, width=400, font=("Segoe UI", 11))
        self.backup_name_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        CustomTooltip(self.backup_name_entry, "Введіть власну назву для резервної копії (без розширення)")
        default_name_check = ctk.CTkCheckBox(self.name_frame, text="Використовувати назву 'backup' за замовчуванням", variable=self.use_default_name, font=("Segoe UI", 12), command=self.app.toggle_default_name)
        default_name_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(default_name_check, "Увімкніть, щоб використовувати назву 'backup' за замовчуванням")
        self.name_frame.grid_columnconfigure(1, weight=1)

        # Секція для вибору цільової папки
        self.folder_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=frame_bg)
        self.folder_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.folder_frame, text="Цільова папка", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(self.folder_frame, text="Папка:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.destination_entry = ctk.CTkEntry(self.folder_frame, textvariable=self.dest_folder, width=400, font=("Segoe UI", 11))
        self.destination_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        CustomTooltip(self.destination_entry, "Вкажіть папку, куди зберегти резервну копію")
        browse_button = ctk.CTkButton(self.folder_frame, text="Обрати", command=self.app.select_folder, width=100, font=("Segoe UI", 12))
        browse_button.grid(row=1, column=2, pady=5, padx=5)
        CustomTooltip(browse_button, "Оберіть папку для збереження")

        ctk.CTkLabel(self.folder_frame, text="Нещодавні:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.recent_dest_combo = ctk.CTkComboBox(self.folder_frame, values=self.recent_folders, width=400, variable=self.dest_folder, command=self.app.use_recent_destination, font=("Segoe UI", 11))
        self.recent_dest_combo.grid(row=2, column=1, pady=(5, 10), padx=5, sticky="ew")
        CustomTooltip(self.recent_dest_combo, "Виберіть одну з нещодавно використаних папок")
        self.folder_frame.grid_columnconfigure(1, weight=1)

        # Кнопка для ручного резервного копіювання
        manual_backup_button = ctk.CTkButton(self.scrollable_frame, text="Резервне копіювання зараз", command=self.app.manual_backup, font=("Segoe UI", 14), height=40, fg_color="#0288d1", hover_color="#0277bd")
        manual_backup_button.pack(fill="x", padx=10, pady=10)
        CustomTooltip(manual_backup_button, "Запустіть резервне копіювання негайно")

        # Секція для шифрування
        self.encrypt_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=frame_bg)
        self.encrypt_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.encrypt_frame, text="Шифрування", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        encrypt_check = ctk.CTkCheckBox(self.encrypt_frame, text="Шифрувати резервні копії", variable=self.app.encrypt, font=("Segoe UI", 12))
        encrypt_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(encrypt_check, "Увімкніть шифрування для захисту резервних копій")
        ctk.CTkLabel(self.encrypt_frame, text="Пароль:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(self.encrypt_frame, text="(мін. 8 символів, літери та цифри):", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=5)
        self.password_entry = ctk.CTkEntry(self.encrypt_frame, show="*", width=250, font=("Segoe UI", 11), textvariable=self.app.passwd)
        self.password_entry.grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 10), padx=10)
        CustomTooltip(self.password_entry, "Введіть пароль для шифрування (мін. 8 символів, літери та цифри)")

        # Секція для розшифрування
        self.decrypt_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=frame_bg)
        self.decrypt_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.decrypt_frame, text="Розшифрування", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(self.decrypt_frame, text="Файл:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.decrypt_file_entry = ctk.CTkEntry(self.decrypt_frame, textvariable=self.app.decrypt_file, width=400, font=("Segoe UI", 11))
        self.decrypt_file_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        CustomTooltip(self.decrypt_file_entry, "Вкажіть зашифрований файл для розшифрування")
        browse_decrypt_button = ctk.CTkButton(self.decrypt_frame, text="Обрати файл", command=self.app.select_decrypt_file, width=150, font=("Segoe UI", 12))
        browse_decrypt_button.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(browse_decrypt_button, "Оберіть зашифрований файл")
        ctk.CTkLabel(self.decrypt_frame, text="Пароль:", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(self.decrypt_frame, text="(мін. 8 символів, літери та цифри):", font=("Segoe UI", 10)).grid(row=3, column=1, sticky="w", padx=5)
        self.decrypt_password_entry = ctk.CTkEntry(self.decrypt_frame, show="*", width=250, font=("Segoe UI", 11))
        self.decrypt_password_entry.grid(row=4, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        CustomTooltip(self.decrypt_password_entry, "Введіть пароль для розшифрування")
        decrypt_button = ctk.CTkButton(self.decrypt_frame, text="Розшифрувати", command=self.app.decrypt_backup, width=150, font=("Segoe UI", 12))
        decrypt_button.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 10))
        CustomTooltip(decrypt_button, "Розшифруйте вибраний файл")
        self.decrypt_frame.grid_columnconfigure(1, weight=1)

        # Секція для розкладу резервного копіювання
        self.schedule_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=frame_bg)
        self.schedule_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.schedule_frame, text="Розклад резервного копіювання", font=("Segoe UI", 16, "bold"), text_color="#0288d1").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        schedule_check = ctk.CTkCheckBox(self.schedule_frame, text="Увімкнути резервне копіювання за розкладом", variable=self.app.schedule_on, font=("Segoe UI", 12))
        schedule_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        CustomTooltip(schedule_check, "Увімкніть автоматичне резервне копіювання за розкладом")
        ctk.CTkLabel(self.schedule_frame, text="Інтервал:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        schedule_options = ["Щогодини", "Кожні 5 годин", "Кожні 10 годин"]
        self.schedule_combo = ctk.CTkComboBox(self.schedule_frame, values=schedule_options, variable=self.app.interval, width=150, font=("Segoe UI", 11))
        self.schedule_combo.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        CustomTooltip(self.schedule_combo, "Виберіть інтервал для автоматичного копіювання")
        ctk.CTkLabel(self.schedule_frame, text="Час (HH:MM):", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.time_entry = ctk.CTkEntry(self.schedule_frame, textvariable=self.app.backup_time, width=100, font=("Segoe UI", 11))
        self.time_entry to_tray(self):
        """Мінімізує програму в системний трей."""
        self.save_config()
        self.master.withdraw()
        if not self.tray_icon:
            try:
                image = Image.open("icon.png")
            except FileNotFoundError:
                logging.warning("Файл icon.png не знайдено, використовується заглушка.")
                image = Image.new('RGB', (64, 64), color='blue')
            menu = pystray.Menu(
                pystray.MenuItem("Відкрити", self.app.restore_from_tray),
                pystray.MenuItem("Вийти", self.app.stop_program)
            )
            self.tray_icon = pystray.Icon("backup_app", image, "Backup App", menu)
            self.tray_icon.run_detached()
        logging.info("Програму мінімізовано в трей")

    def restore_from_tray(self):
        """Відновлює програму з системного трея."""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.master.deiconify()
        logging.info("Програму відновлено з трею")

    def add_files(self):
        """Додає файли до списку для архівування."""
        filepaths = filedialog.askopenfilenames(title="Виберіть файли для архівування")
        for filepath in filepaths:
            if filepath not in self.files:
                self.files.append(filepath)
                filename = os.path.basename(filepath)
                self.files_listbox.insert(ctk.END, filename)
        if filepaths:
            self.save_config()
            logging.info(f"Додано файли: {', '.join([os.path.basename(f) for f in filepaths])}")

    def remove_files(self):
        """Видаляє вибрані файли зі списку."""
        selected_indices = self.files_listbox.curselection()
        if selected_indices:
            removed_files = [self.files[i] for i in selected_indices]
            for index in reversed(selected_indices):
                del self.files[index]
                self.files_listbox.delete(index)
            self.save_config()
            logging.info(f"Видалено файли: {', '.join([os.path.basename(f) for f in removed_files])}")

    def select_folder(self):
        """Обирає цільову папку."""
        folder = filedialog.askdirectory(title="Виберіть цільову папку")
        if folder:
            self.dest_folder.set(folder)
            self.update_recent_folders(folder)
            self.save_config()
            logging.info(f"Вибрано цільову папку: {folder}")

    def use_recent_destination(self, selected_folder):
        """Встановлює нещодавню папку."""
        self.dest_folder.set(selected_folder)
        self.save_config()
        logging.info(f"Вибрано нещодавню папку: {selected_folder}")

    def update_recent_folders(self, folder):
        """Оновлює список нещодавно використаних папок."""
        if folder and folder not in self.recent_folders:
            self.recent_folders.insert(0, folder)
            if len(self.recent_folders) > 5:
                self.recent_folders.pop()
            self.recent_dest_combo.configure(values=self.recent_folders)
            self.save_recent_folders()

    def save_recent_folders(self):
        """Зберігає список нещодавно використаних папок."""
        try:
            with open("recent_destinations.txt", "w", encoding='utf-8') as f:
                for folder in self.recent_folders:
                    f.write(f"{folder}\n")
        except Exception as e:
            logging.error(f"Помилка при збереженні недавніх папок: {e}")

    def load_config(self):
        """Завантажує конфігурацію програми."""
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
            logging.error(f"Помилка при завантаженні стану: {e}")

    def save_config(self):
        """Зберігає поточний стан програми."""
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
            logging.error(f"Помилка при збереженні стану: {e}")

    def toggle_default_name(self):
        """Перемикає використання назви за замовчуванням."""
        if self.use_default_name.get():
            self.backup_name.set("")
        self.save_config()
