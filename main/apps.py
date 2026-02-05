from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials
import os

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        # Инициализируем Firebase только один раз
        if not firebase_admin._apps:  # проверка, что ещё не инициализировано
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cred_path = os.path.join(BASE_DIR, 'main', 'biokam_key.json')
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin успешно инициализирован")