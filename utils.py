import socket
import winreg
from datetime import datetime
from plyer import notification

def notify_backup_completed(backup_type, filepath, last_notify=[None]):
    """Відправляє сповіщення про успішне копіювання."""
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
    """Відправляє сповіщення про помилку."""
    notification.notify(
        title="Помилка резервного копіювання",
        message=message,
        app_name="Backup App",
        timeout=5
    )

def is_running():
    """Перевіряє, чи програма вже запущена."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("localhost", 12345))
        s.close()
        return False
    except socket.error:
        return True

def add_to_startup():
    """Додає програму до автозавантаження Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "BackupApp", 0, winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(__file__)}" -startMinimized')
        winreg.CloseKey(key)
        logging.info("Програму додано до автозавантаження")
    except Exception as e:
        logging.error(f"Помилка додавання до автозавантаження: {e}")
