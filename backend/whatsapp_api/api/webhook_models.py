"""
Webhook models for WhatsApp events and external integrations.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Webhook(models.Model):
    """
    Webhook configuration for user-defined endpoints.
    """
    EVENT_TYPES = [
        ('message_sent', 'Message Sent'),
        ('message_delivered', 'Message Delivered'),
        ('message_read', 'Message Read'),
        ('message_failed', 'Message Failed'),
        ('contact_created', 'Contact Created'),
        ('contact_updated', 'Contact Updated'),
        ('campaign_completed', 'Campaign Completed'),
        ('subscription_created', 'Subscription Created'),
        ('subscription_renewed', 'Subscription Renewed'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('usage_limit_reached', 'Usage Limit Reached'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=500)
    events = models.JSONField(default=list)  # List of event types to trigger on
    
    # Security
    secret = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Retry configuration
    max_retries = models.IntegerField(default=3)
    retry_delay = models.IntegerField(default=60)  # seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.url}"


class WebhookDelivery(models.Model):
    """
    Webhook delivery attempts and status tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    
    # Delivery status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Response
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.status}"
    
    def deliver(self):
        """Attempt to deliver the webhook."""
        import requests
        import hmac
        import hashlib
        import json
        
        self.attempts += 1
        
        # Prepare payload
        payload = {
            'event': self.event_type,
            'timestamp': self.created_at.isoformat(),
            'data': self.payload
        }
        
        # Sign payload if secret is set
        headers = {'Content-Type': 'application/json'}
        if self.webhook.secret:
            signature = hmac.new(
                self.webhook.secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = signature
        
        try:
            response = requests.post(
                self.webhook.url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            self.response_code = response.status_code
            self.response_body = response.text[:1000]  # Limit response storage
            
            if response.status_code >= 200 and response.status_code < 300:
                self.status = 'success'
                self.delivered_at = timezone.now()
            else:
                self.status = 'failed'
                self._schedule_retry()
                
        except requests.RequestException as e:
            self.response_body = str(e)[:1000]
            self.status = 'failed'
            self._schedule_retry()
        
        self.save()
        return self.status == 'success'
    
    def _schedule_retry(self):
        """Schedule a retry if attempts remain."""
        if self.attempts < self.max_attempts:
            from datetime import timedelta
            self.status = 'retrying'
            self.next_retry_at = timezone.now() + timedelta(
                seconds=self.webhook.retry_delay * (2 ** self.attempts)  # Exponential backoff
            )


class AuditLog(models.Model):
    """
    Audit logging for user actions and security events.
    """
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('permission_denied', 'Permission Denied'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('api_key_used', 'API Key Used'),
        ('subscription_changed', 'Subscription Changed'),
        ('payment_processed', 'Payment Processed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)  # e.g., 'contact', 'campaign'
    resource_id = models.CharField(max_length=50, blank=True)
    
    # Details
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Change tracking
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Request
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.resource_type}"


class APIKey(models.Model):
    """
    API keys for programmatic access.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    
    # Permissions
    permissions = models.JSONField(default=list)  # List of allowed actions
    
    # Limits
    rate_limit = models.IntegerField(default=100)  # requests per minute
    
    # Status
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.key:
            import secrets
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if key is valid and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
