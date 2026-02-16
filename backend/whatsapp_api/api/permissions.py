"""
Permission classes for API rate limiting and subscription enforcement.
"""
from rest_framework import permissions
from rest_framework.exceptions import ThrottleExceeded
from django.core.cache import cache
from django.utils import timezone
import hashlib


class SubscriptionPermission(permissions.BasePermission):
    """
    Permission class that checks user subscription and enforces limits.
    """
    message = "Your subscription does not allow this action. Please upgrade your plan."
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        # Get user's subscription
        subscription = getattr(user, 'subscription', None)
        
        if not subscription:
            # User is on free tier
            return self._check_free_tier_limits(request, view)
        
        # Check if subscription is active
        if not subscription.is_active:
            return False
        
        # Check plan features
        return self._check_plan_features(request, view, subscription)
    
    def _check_free_tier_limits(self, request, view):
        """Check limits for free tier users."""
        from whatsapp_api.api.models import Contact, Campaign, MessageTemplate
        from whatsapp_api.billing.models import UsageRecord
        
        # Get current usage
        now = timezone.now()
        usage = UsageRecord.objects.filter(
            user=request.user,
            year=now.year,
            month=now.month
        ).first()
        
        # Free tier limits
        max_contacts = 50
        max_campaigns = 1
        message_limit = 100
        
        # Check action-specific limits
        if view.action == 'create':
            # Check contact limit
            if request.data.get('phone'):
                contact_count = Contact.objects.filter(user=request.user).count()
                if contact_count >= max_contacts:
                    return False
            
            # Check campaign limit
            if hasattr(request.data, 'contacts'):
                campaign_count = Campaign.objects.filter(user=request.user).count()
                if campaign_count >= max_campaigns:
                    return False
            
            # Check message limit
            if usage and usage.messages_sent >= message_limit:
                return False
        
        return True
    
    def _check_plan_features(self, request, view, subscription):
        """Check if user's plan allows the requested feature."""
        plan = subscription.plan
        
        # Feature checks based on view/action
        if view.__class__.__name__ == 'CampaignViewSet':
            if view.action in ['create', 'update', 'partial_update']:
                if not plan.allow_bulk_sending:
                    self.message = "Bulk sending is not available on your plan. Upgrade to Pro."
                    return False
        
        elif view.__class__.__name__ == 'ScheduledMessageViewSet':
            if view.action in ['create', 'update', 'partial_update']:
                if not plan.allow_scheduling:
                    self.message = "Scheduled messages are not available on your plan. Upgrade to Starter."
                    return False
        
        elif view.__class__.__name__ == 'AnalyticsViewSet':
            if not plan.allow_analytics:
                self.message = "Advanced analytics are not available on your plan. Upgrade to Pro."
                return False
        
        return True


class UsageRateThrottle(permissions.BasePermission):
    """
    Rate limiting based on user's subscription plan.
    """
    message = "Rate limit exceeded. Please upgrade your plan for higher limits."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get rate limit from subscription
        rate_limit = self._get_rate_limit(request.user)
        
        # Generate cache key
        cache_key = f"rate_limit:{request.user.id}:{view.__class__.__name__}"
        
        # Check current request count
        current = cache.get(cache_key, 0)
        
        if current >= rate_limit:
            return False
        
        # Increment counter
        cache.set(cache_key, current + 1, 60)  # 60 second window
        
        return True
    
    def _get_rate_limit(self, user):
        """Get rate limit based on subscription."""
        subscription = getattr(user, 'subscription', None)
        
        if subscription and subscription.is_active:
            # Different plans have different rate limits
            tier = subscription.plan.tier
            limits = {
                'free': 10,      # 10 requests/minute
                'starter': 30,   # 30 requests/minute
                'pro': 100,     # 100 requests/minute
                'enterprise': 300,  # 300 requests/minute
            }
            return limits.get(tier, 10)
        
        return 10  # Default for free tier


class MessageLimitMiddleware:
    """
    Middleware to enforce message sending limits.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is a message sending request
        if self._is_message_request(request):
            user = request.user
            
            if user.is_authenticated:
                # Check message limit
                if not self._can_send_message(user):
                    from rest_framework.response import Response
                    return Response(
                        {
                            'error': 'Message limit reached',
                            'upgrade_url': '/dashboard/billing/upgrade'
                        },
                        status=403
                    )
        
        return self.get_response(request)
    
    def _is_message_request(self, request):
        """Check if this is a message sending request."""
        return (
            request.method == 'POST' and
            '/messages/' in request.path
        )
    
    def _can_send_message(self, user):
        """Check if user can send a message."""
        from whatsapp_api.billing.models import UsageRecord
        from django.utils import timezone
        
        now = timezone.now()
        
        usage = UsageRecord.objects.filter(
            user=user,
            year=now.year,
            month=now.month
        ).first()
        
        if not usage:
            return True  # First month, no limit yet
        
        return usage.messages_sent < usage.message_limit


class TeamRolePermission(permissions.BasePermission):
    """
    Permission class for team-based access control.
    """
    message = "You don't have permission to perform this action."
    
    TEAM_ROLES = {
        'admin': ['create', 'update', 'delete', 'read'],
        'manager': ['create', 'update', 'read'],
        'member': ['read'],
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow if not in team context
        if not hasattr(request.user, 'team_member'):
            return True
        
        member = request.user.team_member
        role = member.role
        allowed_actions = self.TEAM_ROLES.get(role, ['read'])
        
        return view.action in allowed_actions


class TenantPermission(permissions.BasePermission):
    """
    Multi-tenant permission - ensures users can only access their own data.
    """
    message = "You don't have access to this resource."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check tenant association
        if hasattr(request.user, 'tenant'):
            # Verify tenant is active
            tenant = request.user.tenant
            if hasattr(tenant, 'is_active') and not tenant.is_active:
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant_id'):
            if hasattr(request.user, 'tenant_id'):
                return obj.tenant_id == request.user.tenant_id
        
        # Fallback to user check
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        
        return True
