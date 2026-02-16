"""
Billing serializers for subscription and payment data.
"""
from rest_framework import serializers
from .models import (
    Plan, Subscription, UsageRecord, BillingHistory,
    Coupon, Referral, PaymentMethod, UserCoupon
)


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans."""
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'tier', 'description',
            'price_monthly', 'price_yearly',
            'monthly_message_limit', 'max_contacts', 'max_campaigns',
            'max_scheduled_messages', 'max_templates', 'max_team_members',
            'allow_bulk_sending', 'allow_scheduling', 'allow_analytics',
            'allow_api_access', 'priority_support', 'custom_branding',
            'is_active', 'is_popular', 'display_order'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions."""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_tier = serializers.CharField(source='plan.tier', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_name', 'plan_tier',
            'status', 'billing_interval',
            'current_period_start', 'current_period_end',
            'canceled_at', 'cancel_at_period_end',
            'trial_start', 'trial_end', 'is_trialing',
            'stripe_subscription_id',
            'next_billing_date', 'last_payment_date', 'last_payment_status',
            'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'current_period_start', 'current_period_end',
            'canceled_at', 'created_at'
        ]


class UsageRecordSerializer(serializers.ModelSerializer):
    """Serializer for usage records."""
    messages_remaining = serializers.IntegerField(read_only=True)
    usage_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = UsageRecord
        fields = [
            'id', 'year', 'month',
            'messages_sent', 'messages_delivered', 'messages_failed',
            'message_limit', 'messages_remaining', 'usage_percentage',
            'created_at'
        ]


class BillingHistorySerializer(serializers.ModelSerializer):
    """Serializer for billing history."""
    
    class Meta:
        model = BillingHistory
        fields = [
            'id', 'event_type',
            'stripe_event_id', 'stripe_invoice_id',
            'amount', 'currency',
            'plan_name', 'status',
            'description', 'failure_message',
            'created_at'
        ]


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for coupons."""
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description',
            'discount_type', 'discount_value',
            'max_uses', 'current_uses',
            'valid_from', 'valid_until',
            'is_active'
        ]


class ReferralSerializer(serializers.ModelSerializer):
    """Serializer for referrals."""
    referred_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Referral
        fields = [
            'id', 'referral_code', 'referred_email', 'referred_name',
            'status', 'referrer_reward_claimed', 'referred_reward_claimed',
            'created_at', 'signed_up_at', 'subscribed_at'
        ]
    
    def get_referred_name(self, obj):
        if obj.referred:
            return f"{obj.referred.first_name} {obj.referred.last_name}".strip() or obj.referred.username
        return None


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods."""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'type', 'last4', 'brand',
            'exp_month', 'exp_year',
            'is_default', 'is_valid',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserCouponSerializer(serializers.ModelSerializer):
    """Serializer for user coupons."""
    coupon_details = CouponSerializer(source='coupon', read_only=True)
    
    class Meta:
        model = UserCoupon
        fields = ['id', 'coupon', 'coupon_details', 'discount_amount', 'used_at']


class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics."""
    subscription = serializers.DictField()
    usage = serializers.DictField()
    features = serializers.DictField()
    alerts = serializers.ListField()
