from django.apps import AppConfig

class ZodiacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zodiac'

    def ready(self):
        from .scheduler import start
        start()
