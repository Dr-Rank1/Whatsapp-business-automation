"""
Django admin configuration for core models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""
    list_display = ['username', 'email', 'phone', 'subscription_tier', 'whatsapp_connected', 'is_active']
    list_filter = ['subscription_tier', 'whatsapp_connected', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('WhatsApp Info', {'fields': ('phone', 'whatsapp_connected', 'whatsapp_session_data')}),
        ('API Usage', {'fields': ('api_usage_limit', 'api_usage_count', 'subscription_tier')}),
        ('Settings', {'fields': ('timezone',)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    list_display = ['user', 'company_name', 'auto_reply_enabled']
    search_fields = ['user__username', 'company_name']
    list_filter = ['auto_reply_enabled']
