from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app configuration for user authentication and profiles."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whatsapp_api.core'
    verbose_name = 'Core'
