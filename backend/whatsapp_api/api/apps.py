from django.apps import AppConfig


class ApiConfig(AppConfig):
    """API app configuration for WhatsApp automation."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whatsapp_api.api'
    verbose_name = 'WhatsApp API'
