from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'BD HardwareHouse'

    def ready(self):
        # Importa las señales para que se registren cuando la app esté lista.
        import core.signals



