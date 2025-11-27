import os
from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
        
    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start_scheduler
            try:
                start_scheduler()
            except Exception as e:
                print(f"Error starting scheduler: {e}")
