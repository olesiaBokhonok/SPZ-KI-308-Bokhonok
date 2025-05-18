import customtkinter as ctk
import sys
from ui import BackupAppUI
from backup import BackupManager
from scheduler import Scheduler
from utils import add_to_startup, is_running, log_operation

def run_app():
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

class BackupApp:
    def __init__(self, master=None):
        self.master = ctk.CTk() if master is None else master
        self.master.title("Програма резервного копіювання")
        self.master.geometry("800x600")
        self.master.resizable(True, True)
        self.master.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Ініціалізація компонентів
        self.ui = BackupAppUI(self)
        self.backup_manager = BackupManager(self)
        self.scheduler = Scheduler(self)

        log_operation("Програма запущена")

    def toggle_theme(self):
        self.ui.toggle_theme()

    def minimize_to_tray(self):
        self.ui.minimize_to_tray()

    def restore_from_tray(self):
        self.ui.restore_from_tray()

    def start_schedule(self):
        self.scheduler.start_schedule()

    def add_files(self):
        self.ui.add_files()

    def remove_files(self):
        self.ui.remove_files()

    def select_folder(self):
        self.ui.select_folder()

    def use_recent_destination(self, selected_folder):
        self.ui.use_recent_destination(selected_folder)

    def manual_backup(self):
        self.backup_manager.manual_backup()

    def select_decrypt_file(self):
        self.backup_manager.select_decrypt_file()

    def decrypt_backup(self):
        self.backup_manager.decrypt_backup()

    def toggle_default_name(self):
        self.ui.toggle_default_name()

    def stop_program(self):
        self.scheduler.stop_program()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-addToStartup":
        add_to_startup()
    else:
        run_app()
