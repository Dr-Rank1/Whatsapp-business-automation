"""
Billing app URL configuration.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    PlanListView,
    SubscriptionDetailView,
    CreateCheckoutSessionView,
    CreatePortalSessionView,
    CancelSubscriptionView,
    ChangePlanView,
    UsageView,
    CurrentUsageView,
    BillingHistoryView,
    ApplyCouponView,
    ReferralView,
    WebhookView,
    SubscriptionStatsView
)

urlpatterns = [
    # Plans
    path('plans/', PlanListView.as_view(), name='plan-list'),
    
    # Subscription
    path('subscription/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscription/stats/', SubscriptionStatsView.as_view(), name='subscription-stats'),
    path('subscription/checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('subscription/portal/', CreatePortalSessionView.as_view(), name='create-portal'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/change-plan/', ChangePlanView.as_view(), name='change-plan'),
    
    # Usage
    path('usage/', UsageView.as_view(), name='usage-list'),
    path('usage/current/', CurrentUsageView.as_view(), name='usage-current'),
    
    # Billing
    path('billing/history/', BillingHistoryView.as_view(), name='billing-history'),
    
    # Coupons
    path('coupon/apply/', ApplyCouponView.as_view(), name='apply-coupon'),
    
    # Referrals
    path('referrals/', ReferralView.as_view(), name='referral-list'),
    
    # Webhooks
    path('webhook/', WebhookView.as_view(), name='stripe-webhook'),
]
