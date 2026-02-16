from django.apps import AppConfig


class BillingConfig(AppConfig):
    """Billing app configuration for subscriptions and payments."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whatsapp_api.billing'
    verbose_name = 'Billing & Subscriptions'
