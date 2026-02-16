"""
Django admin configuration for API models.
"""
from django.contrib import admin
from .models import Contact, MessageTemplate, Campaign, ScheduledMessage, MessageLog, Analytics


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin configuration for Contact model."""
    list_display = ['phone', 'name', 'company', 'user', 'is_blocked', 'created_at']
    list_filter = ['is_blocked', 'created_at']
    search_fields = ['phone', 'name', 'email', 'company']
    raw_id_fields = ['user']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for MessageTemplate model."""
    list_display = ['name', 'category', 'user', 'usage_count', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'content']
    raw_id_fields = ['user']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin configuration for Campaign model."""
    list_display = ['name', 'user', 'status', 'total_contacts', 'sent_count', 'scheduled_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['user', 'template', 'contacts']


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ScheduledMessage model."""
    list_display = ['contact', 'user', 'status', 'scheduled_at', 'is_recurring', 'created_at']
    list_filter = ['status', 'is_recurring', 'scheduled_at']
    raw_id_fields = ['user', 'contact', 'template']


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    """Admin configuration for MessageLog model."""
    list_display = ['contact', 'user', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['contact__phone', 'message_content']
    raw_id_fields = ['user', 'contact', 'campaign', 'template', 'scheduled_message']


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    """Admin configuration for Analytics model."""
    list_display = ['user', 'date', 'messages_sent', 'messages_delivered', 'messages_failed']
    list_filter = ['date']
    raw_id_fields = ['user']
