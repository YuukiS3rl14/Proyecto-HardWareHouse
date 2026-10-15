from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Tienda'

    def ready(self):
        import core.signals
        from django.apps import apps
        apps.get_app_config('ipn').verbose_name = 'PayPal'



