import time
import threading
from datetime import datetime, timedelta
from tkinter import messagebox
import logging
from utils import notify_error

class Scheduler:
    def __init__(self, app):
        """Ініціалізація планувальника."""
        self.app = app
        self.scheduler_active = app.scheduler_active
        self.next_backup = app.next_backup
        self.scheduler_thread = app.scheduler_thread
        self.last_backup = app.last_backup
        self.backup_lock = app.backup_lock
        self.last_backup_minute = app.last_backup_minute

    def start_schedule(self):
        """Запускає або оновлює розклад."""
        if not self.app.schedule_on.get():
            messagebox.showwarning("Попередження", "Увімкніть резервне копіювання за розкладом перед запуском.")
            return

        try:
            time.strptime(self.app.backup_time.get(), "%H:%M")
        except ValueError:
            messagebox.showerror("Помилка", "Неправильний формат часу. Використовуйте HH:MM (наприклад, 14:00).")
            self.app.schedule_on.set(False)
            return

        if not self.scheduler_active:
            self.scheduler_active = True
            logging.info("Розклад резервного копіювання активовано")
            self.update_schedule()
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logging.info("Потік планувальника запущено")
        else:
            self.update_schedule()
            logging.info("Розклад оновлено")

    def run_scheduler(self):
        """Виконує циклічну перевірку часу."""
        while self.scheduler_active:
            try:
                current_time = datetime.now()
                if current_time.second == 0 and current_time.minute % 10 == 0:
                    logging.info("Планувальник активний")
                if self.next_backup:
                    current_hm = (current_time.hour, current_time.minute)
                    next_backup_hm = (self.next_backup.hour, self.next_backup.minute)
                    current_minute_key = f"{current_time.hour}:{current_time.minute}"
                    if current_hm == next_backup_hm and self.last_backup_minute != current_minute_key:
                        with self.backup_lock:
                            logging.info(f"Запуск резервного копіювання о {current_time.strftime('%H:%M:%S')}")
                            self.app.backup_manager.backup("Резервне копіювання за розкладом")
                            self.last_backup = current_time
                            self.last_backup_minute = current_minute_key
                            self.update_schedule()
                            logging.info("Резервне копіювання за розкладом виконано")
                time.sleep(5)
            except Exception as e:
                logging.error(f"Помилка в планувальнику: {e}")
                notify_error(f"Помилка в планувальнику: {e}")
                self.scheduler_active = False
                break

    def update_schedule(self):
        """Оновлює час наступного копіювання."""
        if not self.app.schedule_on.get() or not self.scheduler_active:
            return

        interval = self.app.interval.get()
        scheduled_time_str = self.app.backup_time.get()
        try:
            scheduled_time = time.strptime(scheduled_time_str, "%H:%M")
            now = datetime.now()
            scheduled_datetime = now.replace(hour=scheduled_time.tm_hour, minute=scheduled_time.tm_min, second=0, microsecond=0)

            if scheduled_datetime <= now:
                if interval == "Щогодини":
                    scheduled_datetime += timedelta(hours=1)
                elif interval == "Кожні 5 годин":
                    scheduled_datetime += timedelta(hours=5)
                elif interval == "Кожні 10 годин":
                    scheduled_datetime += timedelta(hours=10)

            if self.next_backup != scheduled_datetime:
                self.next_backup = scheduled_datetime
                logging.info(f"Наступне резервне копіювання заплановано на {self.next_backup.strftime('%Y-%m-%d %H:%M:%S')} ({interval})")
        except Exception as e:
            logging.error(f"Помилка оновлення розкладу: {e}")
            notify_error(f"Помилка налаштування розкладу: {e}")
            self.app.schedule_on.set(False)
            self.scheduler_active = False

    def stop_program(self):
        """Зупиняє програму."""
        self.scheduler_active = False
        self.next_backup = None
        self.last_backup = None
        if self.backup_lock.locked():
            self.backup_lock.release()
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2.0)
        self.scheduler_thread = None
        logging.info("Розклад зупинено")
        if self.app.ui.tray_icon:
            self.app.ui.tray_icon.stop()
        try:
            if self.app.master:
                logging.info("Спроба закрити головне вікно програми")
                self.app.master.destroy()
        except TclError:
            logging.warning("Помилка при закритті головного вікна: TclError")
        except Exception as e:
            logging.error(f"Помилка при закритті програми: {e}")
        sys.exit(0)
