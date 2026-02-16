"""
M-Pesa payment models for Kenyan market.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class MpesaTransaction(models.Model):
    """
    M-Pesa payment transaction tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TRANSACTION_TYPES = [
        ('stk_push', 'STK Push'),
        ('c2b', 'Customer to Business'),
        ('b2c', 'Business to Customer'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mpesa_transactions',
        null=True,
        blank=True
    )
    
    # Transaction identifiers
    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=100, blank=True)
    transaction_description = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_code = models.CharField(max_length=10, blank=True)
    result_description = models.TextField(blank=True)
    
    # Timing
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Raw callback data
    raw_callback = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'mpesa_transactions'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['checkout_request_id']),
        ]

    def __str__(self):
        return f"M-Pesa {self.transaction_type} - KES {self.amount} to {self.phone_number}"


class MpesaPayment(models.Model):
    """
    Links M-Pesa transactions to subscriptions/orders.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mpesa_payments'
    )
    
    transaction = models.OneToOneField(
        MpesaTransaction,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    # Payment purpose
    PAYMENT_TYPES = [
        ('subscription', 'Subscription'),
        ('addon', 'Add-on Purchase'),
        ('overage', 'Usage Overage'),
        ('topup', 'Message Top-up'),
    ]
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    
    # Subscription link (if applicable)
    subscription = models.ForeignKey(
        'billing.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mpesa_payments'
    )
    
    # Amount details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('credited', 'Credited'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mpesa_payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.amount} KES - {self.user.username}"
