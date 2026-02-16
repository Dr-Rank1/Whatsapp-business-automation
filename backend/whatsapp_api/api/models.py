"""
API models for WhatsApp Business Automation.
Contains all core data models: Contact, Template, Campaign, ScheduledMessage, MessageLog.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator


class Contact(models.Model):
    """
    Contact model for storing WhatsApp contacts.
    """
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be in format: '+999999999'"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    phone = models.CharField(max_length=20, validators=[phone_validator])
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    company = models.CharField(max_length=200, blank=True)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contacts'
        unique_together = ['user', 'phone']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'phone']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name or self.phone} ({self.user.username})"


class MessageTemplate(models.Model):
    """
    Message template model for reusable messages.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    name = models.CharField(max_length=100)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('greeting', 'Greeting'),
            ('support', 'Support'),
            ('promotional', 'Promotional'),
            ('notification', 'Notification'),
            ('followup', 'Follow-up'),
            ('custom', 'Custom'),
        ],
        default='custom'
    )
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'message_templates'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Campaign(models.Model):
    """
    Campaign model for bulk message sending.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns'
    )
    message_content = models.TextField()
    contacts = models.ManyToManyField(Contact, related_name='campaigns')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Statistics
    total_contacts = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    delay_between_messages = models.IntegerField(default=5, help_text='Seconds between messages')
    retry_failed = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"


class ScheduledMessage(models.Model):
    """
    Scheduled message model for time-specific messaging.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_messages'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='scheduled_messages'
    )
    template = models.ForeignKey(
        MessageTemplate,
        on_delete.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_messages'
    )
    message_content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=50,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_messages'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"Scheduled: {self.contact.phone} at {self.scheduled_at}"


class MessageLog(models.Model):
    """
    Message log model for tracking all sent messages.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_logs'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='message_logs'
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_logs'
    )
    scheduled_message = models.ForeignKey(
        ScheduledMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_logs'
    )
    template = models.ForeignKey(
        MessageTemplate,
        on_delete.SET_NULL,
        null=True,
        blank=True,
        related_name='message_logs'
    )
    
    message_content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['contact', 'created_at']),
            models.Index(fields=['campaign', 'status']),
        ]

    def __str__(self):
        return f"Message to {self.contact.phone} - {self.status}"


class Analytics(models.Model):
    """
    Analytics model for aggregated statistics.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    date = models.DateField()
    messages_sent = models.IntegerField(default=0)
    messages_delivered = models.IntegerField(default=0)
    messages_failed = models.IntegerField(default=0)
    messages_read = models.IntegerField(default=0)
    contacts_added = models.IntegerField(default=0)
    campaigns_created = models.IntegerField(default=0)
    scheduled_messages = models.IntegerField(default=0)

    class Meta:
        db_table = 'analytics'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"Analytics: {self.user.username} - {self.date}"
