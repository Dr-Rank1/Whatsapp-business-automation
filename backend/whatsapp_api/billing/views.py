"""
Billing API views for subscription management.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    Plan, Subscription, UsageRecord, BillingHistory, 
    Coupon, Referral, PaymentMethod
)
from .serializers import (
    PlanSerializer, SubscriptionSerializer, UsageRecordSerializer,
    BillingHistorySerializer, CouponSerializer, ReferralSerializer
)
from .stripe_service import stripe_service


class PlanListView(generics.ListAPIView):
    """List all available subscription plans."""
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Plan.objects.filter(is_active=True).order_by('display_order')


class SubscriptionDetailView(generics.RetrieveAPIView):
    """Get current user's subscription details."""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        subscription, _ = Subscription.objects.get_or_create(
            user=self.request.user,
            defaults={
                'plan': Plan.objects.get(tier='free'),
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timedelta(days=30),
            }
        )
        return subscription


class CreateCheckoutSessionView(generics.CreateAPIView):
    """Create Stripe checkout session for subscription."""
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')
        billing_interval = request.data.get('billing_interval', 'monthly')
        coupon_code = request.data.get('coupon')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {'error': 'Plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already has subscription
        subscription = getattr(request.user, 'subscription', None)
        if subscription and subscription.is_active:
            return Response(
                {'error': 'You already have an active subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build URLs
        base_url = request.data.get('base_url', settings.FRONTEND_URL)
        success_url = f"{base_url}/dashboard/settings?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/dashboard/settings?canceled=true"
        
        # Determine trial days based on plan
        trial_days = 7 if plan.tier != 'free' else 0
        
        try:
            session = stripe_service.create_checkout_session(
                user=request.user,
                plan=plan,
                success_url=success_url,
                cancel_url=cancel_url,
                coupon_code=coupon_code,
                trial_days=trial_days
            )
            
            return Response({
                'checkout_url': session.url,
                'session_id': session.id
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreatePortalSessionView(generics.CreateAPIView):
    """Create Stripe customer portal session."""
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        subscription = getattr(request.user, 'subscription', None)
        
        if not subscription or not subscription.stripe_customer_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        base_url = request.data.get('base_url', settings.FRONTEND_URL)
        return_url = f"{base_url}/dashboard/settings"
        
        try:
            session = stripe_service.create_portal_session(
                customer_id=subscription.stripe_customer_id,
                return_url=return_url
            )
            
            return Response({
                'portal_url': session.url
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CancelSubscriptionView(generics.CreateAPIView):
    """Cancel current subscription."""
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        subscription = getattr(request.user, 'subscription', None)
        
        if not subscription or not subscription.stripe_subscription_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stripe_service.cancel_subscription(
                subscription_id=subscription.stripe_subscription_id,
                at_period_end=True
            )
            
            subscription.cancel_at_period_end = True
            subscription.save()
            
            return Response({
                'message': 'Subscription will be canceled at the end of billing period'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePlanView(generics.CreateAPIView):
    """Change subscription to different plan."""
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription = getattr(request.user, 'subscription', None)
        
        if not subscription or not subscription.stripe_subscription_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {'error': 'Plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determine price ID
        price_id = new_plan.stripe_price_id_monthly
        
        try:
            stripe_subscription = stripe_service.change_plan(
                subscription_id=subscription.stripe_subscription_id,
                new_price_id=price_id
            )
            
            # Update local subscription
            subscription.plan = new_plan
            subscription.save()
            
            return Response({
                'message': f'Successfully changed to {new_plan.name}',
                'subscription': SubscriptionSerializer(subscription).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UsageView(generics.ListAPIView):
    """Get user's usage records."""
    serializer_class = UsageRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UsageRecord.objects.filter(user=self.request.user)


class CurrentUsageView(generics.RetrieveAPIView):
    """Get current month's usage."""
    serializer_class = UsageRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        now = timezone.now()
        usage, _ = UsageRecord.objects.get_or_create(
            user=self.request.user,
            year=now.year,
            month=now.month,
            defaults={
                'message_limit': self._get_message_limit()
            }
        )
        return usage
    
    def _get_message_limit(self):
        subscription = getattr(self.request.user, 'subscription', None)
        if subscription:
            return subscription.get_message_limit()
        return 100  # Default free tier limit


class BillingHistoryView(generics.ListAPIView):
    """Get user's billing history."""
    serializer_class = BillingHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BillingHistory.objects.filter(user=self.request.user)


class ApplyCouponView(generics.CreateAPIView):
    """Validate and apply a coupon code."""
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        code = request.data.get('code', '').strip().upper()
        
        if not code:
            return Response(
                {'error': 'Coupon code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(code__upper=code)
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Invalid coupon code'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not coupon.is_valid():
            return Response(
                {'error': 'Coupon is expired or has reached maximum uses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'valid': True,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'description': coupon.description
        })


class ReferralView(generics.ListCreateAPIView):
    """Get user's referrals and generate new referral code."""
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)
    
    def perform_create(self, serializer):
        import uuid
        code = f"REF{uuid.uuid4().hex[:8].upper()}"
        serializer.save(
            referrer=self.request.user,
            referral_code=code
        )


class WebhookView(generics.CreateAPIView):
    """Handle Stripe webhooks."""
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        payload = request.body
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            return Response(
                {'error': 'No signature provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            event = stripe_service.construct_webhook_event(payload, signature)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle the event
        success = stripe_service.handle_webhook(event)
        
        if success:
            return Response({'status': 'success'})
        else:
            return Response(
                {'error': 'Failed to process webhook'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionStatsView(generics.RetrieveAPIView):
    """Get subscription and usage statistics."""
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        subscription = getattr(request.user, 'subscription', None)
        
        # Get current usage
        now = timezone.now()
        usage = UsageRecord.objects.filter(
            user=request.user,
            year=now.year,
            month=now.month
        ).first()
        
        # Get plan limits
        if subscription:
            plan = subscription.plan
            message_limit = plan.monthly_message_limit
            max_contacts = plan.max_contacts
            max_campaigns = plan.max_campaigns
            allow_scheduling = plan.allow_scheduling
            allow_analytics = plan.allow_analytics
        else:
            free_plan = Plan.objects.get(tier='free')
            message_limit = free_plan.monthly_message_limit
            max_contacts = free_plan.max_contacts
            max_campaigns = free_plan.max_campaigns
            allow_scheduling = free_plan.allow_scheduling
            allow_analytics = free_plan.allow_analytics
        
        # Calculate usage
        messages_sent = usage.messages_sent if usage else 0
        messages_remaining = max(0, message_limit - messages_sent)
        usage_percentage = (messages_sent / message_limit * 100) if message_limit > 0 else 0
        
        # Get contact count
        from whatsapp_api.api.models import Contact
        contact_count = Contact.objects.filter(user=request.user).count()
        
        # Get campaign count
        from whatsapp_api.api.models import Campaign
        campaign_count = Campaign.objects.filter(user=request.user).count()
        
        return Response({
            'subscription': {
                'status': subscription.status if subscription else 'free',
                'plan_name': subscription.plan.name if subscription else 'Free',
                'plan_tier': subscription.plan.tier if subscription else 'free',
                'current_period_end': subscription.current_period_end if subscription else None,
                'is_trialing': subscription.is_trialing if subscription else False,
            },
            'usage': {
                'messages_sent': messages_sent,
                'message_limit': message_limit,
                'messages_remaining': messages_remaining,
                'usage_percentage': round(usage_percentage, 1),
                'contact_count': contact_count,
                'max_contacts': max_contacts,
                'campaign_count': campaign_count,
                'max_campaigns': max_campaigns,
            },
            'features': {
                'allow_scheduling': allow_scheduling,
                'allow_analytics': allow_analytics,
                'allow_bulk_sending': plan.allow_bulk_sending if subscription else False,
                'priority_support': plan.priority_support if subscription else False,
            },
            'alerts': self._get_alerts(usage_percentage, messages_remaining, subscription)
        })
    
    def _get_alerts(self, usage_percentage, messages_remaining, subscription):
        alerts = []
        
        # Usage alerts
        if usage_percentage >= 90:
            alerts.append({
                'type': 'danger',
                'message': 'You have used 90% of your monthly messages. Upgrade to avoid interruption.'
            })
        elif usage_percentage >= 80:
            alerts.append({
                'type': 'warning',
                'message': 'You have used 80% of your monthly messages. Consider upgrading.'
            })
        
        # Trial alerts
        if subscription and subscription.is_trialing:
            days_remaining = (subscription.trial_end - timezone.now()).days
            if days_remaining <= 3:
                alerts.append({
                    'type': 'warning',
                    'message': f'Your trial ends in {days_remaining} days. Subscribe to continue.'
                })
        
        # Past due
        if subscription and subscription.status == 'past_due':
            alerts.append({
                'type': 'danger',
                'message': 'Payment failed. Please update your payment method.'
            })
        
        return alerts
