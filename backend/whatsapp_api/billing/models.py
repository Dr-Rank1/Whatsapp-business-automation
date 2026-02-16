"""
Billing models for SaaS subscriptions and payments.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Plan(models.Model):
    """
    Subscription plan model defining tier features and limits.
    """
    TIER_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_INTERVAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=50)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    # Pricing
    price_monthly = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    price_yearly = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True)
    
    # Limits
    monthly_message_limit = models.IntegerField(default=100)
    max_contacts = models.IntegerField(default=50)
    max_campaigns = models.IntegerField(default=1)
    max_scheduled_messages = models.IntegerField(default=10)
    max_templates = models.IntegerField(default=5)
    max_team_members = models.IntegerField(default=1)
    
    # Features
    allow_bulk_sending = models.BooleanField(default=False)
    allow_scheduling = models.BooleanField(default=False)
    allow_analytics = models.BooleanField(default=False)
    allow_api_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    
    # Display
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        ordering = ['display_order']

    def __str__(self):
        return f"{self.name} (${self.price_monthly}/month)"


class Subscription(models.Model):
    """
    User subscription model tracking active plans and billing cycles.
    """
    STATUS_CHOICES = [
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('paused', 'Paused'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    
    # Stripe integration
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_item_id = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trialing'
    )
    
    # Billing
    billing_interval = models.CharField(
        max_length=20,
        choices=Plan.BILLING_INTERVAL_CHOICES,
        default='monthly'
    )
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Trial
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Payment
    next_billing_date = models.DateTimeField(null=True, blank=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    last_payment_status = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    @property
    def is_active(self):
        return self.status in ['trialing', 'active'] and self.current_period_end > timezone.now()
    
    @property
    def is_trialing(self):
        return self.status == 'trialing' and self.trial_end and self.trial_end > timezone.now()
    
    def can_send_message(self):
        """Check if user can send messages based on plan limits."""
        if not self.is_active:
            return False
        return True
    
    def get_message_limit(self):
        """Get monthly message limit for current plan."""
        return self.plan.monthly_message_limit


class UsageRecord(models.Model):
    """
    Track monthly usage for quota enforcement.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_records'
    )
    year = models.IntegerField()
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Counters
    messages_sent = models.IntegerField(default=0)
    messages_delivered = models.IntegerField(default=0)
    messages_failed = models.IntegerField(default=0)
    
    # Limits (snapshot at time of record)
    message_limit = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usage_records'
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.username} - {self.year}-{self.month:02d}"
    
    @property
    def messages_remaining(self):
        return max(0, self.message_limit - self.messages_sent)
    
    @property
    def usage_percentage(self):
        if self.message_limit == 0:
            return 100
        return min(100, (self.messages_sent / self.message_limit) * 100)


class BillingHistory(models.Model):
    """
    Track payment history for user billing.
    """
    EVENT_CHOICES = [
        ('payment_succeeded', 'Payment Succeeded'),
        ('payment_failed', 'Payment Failed'),
        ('subscription_created', 'Subscription Created'),
        ('subscription_updated', 'Subscription Updated'),
        ('subscription_canceled', 'Subscription Canceled'),
        ('trial_started', 'Trial Started'),
        ('trial_ended', 'Trial Ended'),
        ('invoice_created', 'Invoice Created'),
        ('invoice_paid', 'Invoice Paid'),
        ('refund', 'Refund'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='billing_history'
    )
    
    # Event details
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    stripe_event_id = models.CharField(max_length=100, blank=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Amount
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='usd')
    
    # Plan info
    plan_name = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, default='pending')
    description = models.TextField(blank=True)
    failure_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'billing_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event_type} - ${self.amount}"


class Coupon(models.Model):
    """
    Promo codes and discount coupons.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    
    # Discount
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Limits
    max_uses = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    current_uses = models.IntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Plan restriction (None = all plans)
    applicable_plans = models.ManyToManyField(
        Plan,
        blank=True,
        related_name='coupons'
    )
    
    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'

    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '$'}"
    
    def is_valid(self):
        """Check if coupon is currently valid."""
        if not self.is_active:
            return False
        if self.current_uses >= self.max_uses:
            return False
        now = timezone.now()
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True


class UserCoupon(models.Model):
    """
    Track coupon usage per user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='used_coupons'
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_coupons'
        unique_together = ['user', 'coupon']


class Referral(models.Model):
    """
    Referral system for user acquisition.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('signed_up', 'Signed Up'),
        ('subscribed', 'Subscribed'),
        ('rewarded', 'Rewarded'),
        ('expired', 'Expired'),
    ]
    
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_given'
    )
    referred = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_received',
        null=True,
        blank=True
    )
    
    referral_code = models.CharField(max_length=50, unique=True)
    referred_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Rewards
    referrer_reward_claimed = models.BooleanField(default=False)
    referred_reward_claimed = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    signed_up_at = models.DateTimeField(null=True, blank=True)
    subscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'referrals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.username} -> {self.referred_email or 'pending'}"


class PaymentMethod(models.Model):
    """
    Store user payment methods (cards, etc.)
    """
    TYPE_CHOICES = [
        ('card', 'Card'),
        ('bank_account', 'Bank Account'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    
    # Stripe
    stripe_payment_method_id = models.CharField(max_length=100, unique=True)
    
    # Card details (last 4 only for security)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    last4 = models.CharField(max_length=4)
    brand = models.CharField(max_length=20, blank=True)  # visa, mastercard, etc.
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    
    is_default = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.brand} ****{self.last4} (exp: {self.exp_month}/{self.exp_year})"
