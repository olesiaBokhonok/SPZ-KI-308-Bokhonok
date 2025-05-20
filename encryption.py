from cryptography.fernet import Fernet, InvalidToken
import hashlib
import base64
import logging
from utils import notify_error

class EncryptionManager:
    def __init__(self):
        """Ініціалізація менеджера шифрування."""
        pass

    def encrypt_file(self, filepath, password):
        """Шифрує файл за допомогою пароля."""
        try:
            salt = b'salt_'
            password_encoded = password.encode('utf-8')
            key = hashlib.pbkdf2_hmac('sha256', password_encoded, salt, 100000)
            key = base64.urlsafe_b64encode(key[:32])
            f = Fernet(key)
            with open(filepath, "rb") as file:
                data = file.read()
            encrypted_data = f.encrypt(data)
            encrypted_filepath = filepath + ".encrypted"
            with open(encrypted_filepath, "wb") as file:
                file.write(encrypted_data)
            logging.info(f"Файл зашифровано: {os.path.basename(encrypted_filepath)}")
            return encrypted_filepath
        except Exception as e:
            logging.error(f"Помилка шифрування: {e}")
            notify_error(f"Помилка шифрування: {e}")
            return None

    def decrypt_file(self, filepath, password):
        """Розшифровує файл за допомогою пароля."""
        try:
            decrypted_filepath = filepath.replace(".encrypted", "")
            salt = b'salt_'
            password_encoded = password.encode('utf-8')
            key = hashlib.pbkdf2_hmac('sha256', password_encoded, salt, 100000)
            key = base64.urlsafe_b64encode(key[:32])
            f = Fernet(key)
            with open(filepath, "rb") as file:
                encrypted_data = file.read()
            decrypted_data = f.decrypt(encrypted_data)
            with open(decrypted_filepath, "wb") as file:
                file.write(decrypted_data)
            logging.info(f"Файл розшифровано: {os.path.basename(decrypted_filepath)}")
            return decrypted_filepath
        except InvalidToken:
            logging.error("Помилка розшифрування: невірний пароль")
            notify_error("Невірний пароль.")
            return None
        except Exception as e:
            logging.error(f"Помилка розшифрування: {e}")
            notify_error(f"Помилка розшифрування: {e}")
            return None
