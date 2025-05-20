import sys
import customtkinter as ctk
import logging
from ui import BackupAppUI
from backup_manager import BackupManager
from scheduler import Scheduler
from utils import is_running, add_to_startup

# Налаштування логування
logging.basicConfig(filename='backup.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# Встановлення світлої теми за замовчуванням
ctk.set_appearance_mode("Light")

class BackupApp:
    def __init__(self, master=None):
        """Ініціалізація основного додатка."""
        self.master = ctk.CTk() if master is None else master
        self.master.title("Програма резервного копіювання")
        self.master.geometry("800x600")
        self.master.resizable(True, True)
        self.master.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.files = []
        self.dest_folder = ctk.StringVar()
        self.recent_folders = self.load_recent_folders()
        self.tray_icon = None
        self.backup_name = ctk.StringVar(value="")
        self.use_default_name = ctk.BooleanVar(value=True)
        self.encrypt = ctk.BooleanVar(value=False)
        self.passwd = ctk.StringVar(value="")
        self.decrypt_file = ctk.StringVar()
        self.schedule_on = ctk.BooleanVar(value=False)
        self.interval = ctk.StringVar(value="Щогодини")
        self.backup_time = ctk.StringVar(value="00:00")
        self.scheduler_active = False
        self.next_backup = None
        self.scheduler_thread = None
        self.last_backup = None
        self.backup_lock = threading.Lock()
        self.last_backup_minute = None

        self.ui = BackupAppUI(self)
        self.backup_manager = BackupManager(self)
        self.scheduler = Scheduler(self)

        logging.info("Програма запущена")

    def load_recent_folders(self):
        """Завантажує список нещодавно використаних папок."""
        try:
            with open("recent_destinations.txt", "r", encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            return []
        except Exception as e:
            logging.error(f"Помилка при завантаженні недавніх папок: {e}")
            return []

    def toggle_theme(self):
        """Перемикає тему інтерфейсу."""
        self.ui.toggle_theme()

    def minimize_to_tray(self):
        """Мінімізує програму в системний трей."""
        self.ui.minimize_to_tray()

    def restore_from_tray(self):
        """Відновлює програму з системного трея."""
        self.ui.restore_from_tray()

    def start_schedule(self):
        """Запускає планувальник."""
        self.scheduler.start_schedule()

    def add_files(self):
        """Додає файли до списку."""
        self.ui.add_files()

    def remove_files(self):
        """Видаляє вибрані файли."""
        self.ui.remove_files()

    def select_folder(self):
        """Обирає цільову папку."""
        self.ui.select_folder()

    def use_recent_destination(self, selected_folder):
        """Встановлює нещодавню папку."""
        self.ui.use_recent_destination(selected_folder)

    def manual_backup(self):
        """Запускає резервне копіювання вручну."""
        self.backup_manager.manual_backup()

    def select_decrypt_file(self):
        """Обирає файл для розшифрування."""
        self.backup_manager.select_decrypt_file()

    def decrypt_backup(self):
        """Розшифровує вибраний файл."""
        self.backup_manager.decrypt_backup()

    def toggle_default_name(self):
        """Перемикає використання назви за замовчуванням."""
        self.ui.toggle_default_name()

    def stop_program(self):
        """Зупиняє програму."""
        self.scheduler.stop_program()

def run_app():
    """Запускає основний цикл програми."""
    if is_running():
        print("Програма вже запущена.")
        sys.exit()

    root = ctk.CTk()
    app = BackupApp(root)
    
    if len(sys.argv) > 1 and sys.argv[1] == "-startMinimized":
        app.minimize_to_tray()
    else:
        root.deiconify()
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-addToStartup":
        add_to_startup()
    else:
        run_app()
