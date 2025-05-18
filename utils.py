import logging
from datetime import datetime
import winreg
import socket
import sys
from plyer import notification

# Налаштування змінної середовища для Tkinter
import os
os.environ["DISPLAY"] = ":0"

# Налаштування логування
logging.basicConfig(filename='backup.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

def log_operation(message):
    logging.info(message)

def notify_backup_completed(backup_type, filepath, last_notify=[None]):
    current_time = datetime.now()
    if not last_notify[0] or (current_time - last_notify[0]).total_seconds() > 60:
        notification.notify(
            title="Резервне копіювання виконано",
            message=f"{backup_type}: Успішно створено {os.path.basename(filepath)}",
            app_name="Backup App",
            timeout=5
        )
        last_notify[0] = current_time

def notify_error(message):
    notification.notify(
        title="Помилка резервного копіювання",
        message=message,
        app_name="Backup App",
        timeout=5
    )

def add_to_startup():
    try:
        script_path = os.path.abspath(sys.argv[0])
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "BackupApp", 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}" -startMinimized')
        winreg.CloseKey(key)
        logging.info("Програма додана до автозапуску.")
    except Exception as e:
        logging.error(f"Помилка додавання до автозапуску: {e}")

def is_running():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("localhost", 12345))
        s.close()
        return False
    except socket.error:
        return True
