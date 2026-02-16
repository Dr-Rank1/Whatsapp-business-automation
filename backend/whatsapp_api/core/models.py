"""
Core models for WhatsApp Business Automation.
Includes User model and base functionality.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds fields for WhatsApp Business API integration and user preferences.
    """
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('WhatsApp phone number with country code')
    )
    whatsapp_connected = models.BooleanField(
        default=False,
        help_text=_('Whether WhatsApp is connected')
    )
    whatsapp_session_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('WhatsApp session data for automation')
    )
    api_usage_limit = models.IntegerField(
        default=1000,
        help_text=_('Monthly API message limit')
    )
    api_usage_count = models.IntegerField(
        default=0,
        help_text=_('Current month API usage count')
    )
    subscription_tier = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.email})"

    def increment_usage(self):
        """Increment API usage count."""
        self.api_usage_count += 1
        self.save(update_fields=['api_usage_count'])

    @property
    def remaining_quota(self):
        """Calculate remaining API quota."""
        return max(0, self.api_usage_limit - self.api_usage_count)


class UserProfile(models.Model):
    """
    Extended user profile with additional settings.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    company_name = models.CharField(max_length=200, blank=True)
    business_description = models.TextField(blank=True)
    default_country_code = models.CharField(max_length=5, default='+1')
    auto_reply_enabled = models.BooleanField(default=False)
    greeting_message = models.TextField(blank=True)
    away_message = models.TextField(blank=True)
    working_hours_start = models.TimeField(null=True, blank=True)
    working_hours_end = models.TimeField(null=True, blank=True)
    notification_email = models.EmailField(blank=True)
    webhook_url = models.URLField(blank=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile: {self.user.username}"
