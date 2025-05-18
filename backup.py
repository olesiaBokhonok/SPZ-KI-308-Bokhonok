import zipfile
import os
from datetime import datetime
from encryption import EncryptionManager
from utils import log_operation, notify_backup_completed, notify_error

class BackupManager:
    def __init__(self, app):
        self.app = app
        self.files = app.files
        self.dest_folder = app.dest_folder
        self.encrypt = app.encrypt
        self.passwd = app.passwd
        self.decrypt_file = app.decrypt_file
        self.backup_name = app.backup_name
        self.use_default_name = app.use_default_name
        self.encryption = EncryptionManager()

    def manual_backup(self):
        self.backup("Ручне резервне копіювання")

    def backup(self, backup_type):
        if not self.files:
            log_operation(f"{backup_type} перервано: не вибрано файли")
            notify_error("Виберіть файли для архівування.")
            return
        if not self.dest_folder.get():
            log_operation(f"{backup_type} перервано: не вибрано цільову папку")
            notify_error("Виберіть цільову папку.")
            return

        for file_path in self.files:
            if not os.path.exists(file_path):
                log_operation(f"{backup_type}: Помилка - файл не знайдено: {file_path}")
                notify_error(f"Файл не знайдено: {os.path.basename(file_path)}")
                return

        base_name = self.backup_name.get() if not self.use_default_name.get() and self.backup_name.get().strip() else "backup"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        zip_filename = f"{base_name}_{timestamp}.zip"
        zip_filepath = os.path.join(self.dest_folder.get(), zip_filename)

        # Перевірка на унікальність назви
        counter = 1
        while os.path.exists(zip_filepath):
            zip_filename = f"{base_name}_{timestamp}_{counter}.zip"
            zip_filepath = os.path.join(self.dest_folder.get(), zip_filename)
            counter += 1

        try:
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                for file_path in self.files:
                    zipf.write(file_path, os.path.basename(file_path))

            if self.encrypt.get():
                password = self.passwd.get()
                if not (len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)):
                    os.remove(zip_filepath)
                    log_operation(f"{backup_type}: Помилка шифрування - невірний пароль")
                    notify_error("Пароль повинен містити мінімум 8 символів, включаючи літери та цифри.")
                    return
                encrypted_filepath = self.encryption.encrypt_file(zip_filepath, password)
                if encrypted_filepath:
                    os.remove(zip_filepath)
                    zip_filepath = encrypted_filepath

            log_operation(f"{backup_type}: Успішно створено копію: {os.path.basename(zip_filepath)}")
            notify_backup_completed(backup_type, zip_filepath)
        except (zipfile.BadZipFile, OSError) as e:
            log_operation(f"{backup_type}: Помилка при роботі з ZIP-архівом: {e}")
            notify_error(f"Помилка при створенні ZIP-архіву: {e}")
        except Exception as e:
            log_operation(f"{backup_type}: Помилка: {e}")
            notify_error(f"Помилка резервного копіювання: {e}")

    def select_decrypt_file(self):
        filepath = filedialog.askopenfilename(title="Виберіть зашифрований файл", filetypes=[("Encrypted files", "*.encrypted")])
        if filepath:
            self.decrypt_file.set(filepath)
            log_operation(f"Вибрано файл для розшифрування: {filepath}")

    def decrypt_backup(self):
        filepath = self.decrypt_file.get()
        password = self.app.ui.decrypt_password_entry.get()

        if not filepath:
            log_operation("Розшифрування перервано: не вибрано файл")
            notify_error("Виберіть файл для розшифрування.")
            return
        if not password:
            log_operation("Розшифрування перервано: не введено пароль")
            notify_error("Введіть пароль для розшифрування.")
            return

        try:
            decrypted_filepath = self.encryption.decrypt_file(filepath, password)
            if decrypted_filepath:
                log_operation(f"Файл розшифровано: {os.path.basename(decrypted_filepath)}")
                notify_backup_completed("Розшифрування", decrypted_filepath)
        except Exception as e:
            log_operation(f"Помилка розшифрування: {e}")
            notify_error(f"Помилка розшифрування: {e}")
