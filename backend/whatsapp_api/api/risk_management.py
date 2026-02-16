"""
WhatsApp Risk Management System
Protects against account bans with smart rate limiting and behavior simulation.
"""
import random
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class WhatsAppRiskManager:
    """
    Manages risk scoring and automation safety for WhatsApp operations.
    
    Risk Score: 0-100
    - 0-30: Green zone (normal operation)
    - 31-60: Yellow zone (warnings + slow down)
    - 61-80: Orange zone (force cooldowns)
    - 81-100: Red zone (auto-pause automation)
    """
    
    # Risk factor weights
    WEIGHTS = {
        'message_velocity': 25,
        'spam_reports': 30,
        'failed_rate': 15,
        'contact_complaints': 20,
        'account_age': 10,
    }
    
    @classmethod
    def calculate_risk_score(cls, user) -> int:
        """
        Calculate 0-100 risk score for a user.
        
        Factors:
        - Message velocity (messages per hour)
        - Spam reports from contacts
        - Failed delivery rate
        - Contact complaint/block rate
        - Account age (newer = higher risk)
        """
        from whatsapp_api.api.models import MessageLog
        from whatsapp_api.core.models import User
        
        score = 0
        
        # Message velocity factor
        velocity = cls.get_message_velocity(user)
        if velocity > 100:
            score += 30
        elif velocity > 75:
            score += 20
        elif velocity > 50:
            score += 10
        
        # Failed message rate
        failed_rate = cls.get_failed_rate(user)
        if failed_rate > 0.15:
            score += 25
        elif failed_rate > 0.10:
            score += 15
        elif failed_rate > 0.05:
            score += 5
        
        # Spam/Block reports
        complaint_rate = cls.get_complaint_rate(user)
        if complaint_rate > 0.05:
            score += 30
        elif complaint_rate > 0.02:
            score += 15
        
        # Account age factor
        account_age = (timezone.now() - user.created_at).days
        if account_age < 7:
            score += 15
        elif account_age < 30:
            score += 8
        
        # Payment status
        subscription = getattr(user, 'subscription', None)
        if not subscription:
            score += 10
        elif subscription.status != 'active':
            score += 5
        
        return min(score, 100)
    
    @classmethod
    def get_message_velocity(cls, user) -> float:
        """Get messages sent per hour (rolling 24h)."""
        from whatsapp_api.api.models import MessageLog
        
        since = timezone.now() - timedelta(hours=24)
        count = MessageLog.objects.filter(
            user=user,
            sent_at__gte=since
        ).count()
        
        return count  # messages per 24h, can divide by 24 for hourly
    
    @classmethod
    def get_failed_rate(cls, user) -> float:
        """Get percentage of failed messages (last 100 messages)."""
        from whatsapp_api.api.models import MessageLog
        
        recent = MessageLog.objects.filter(
            user=user
        ).order_by('-created_at')[:100]
        
        if not recent:
            return 0.0
        
        failed_count = sum(1 for m in recent if m.status == 'failed')
        return failed_count / len(recent)
    
    @classmethod
    def get_complaint_rate(cls, user) -> float:
        """Get percentage of contacts who blocked user."""
        from whatsapp_api.api.models import Contact
        
        total_contacts = Contact.objects.filter(user=user).count()
        if total_contacts == 0:
            return 0.0
        
        # Contacts with is_blocked by WhatsApp (not by user)
        # This would require WhatsApp to report blocks back to us
        blocked_by_user = Contact.objects.filter(user=user, is_blocked=True).count()
        
        return blocked_by_user / total_contacts
    
    @classmethod
    def get_safe_delay(cls, user) -> int:
        """
        Calculate human-like delay between messages.
        
        Returns delay in seconds with randomization.
        """
        from whatsapp_api.core.models import User
        
        # Get user's subscription tier
        tier = getattr(user, 'subscription_tier', 'free')
        
        # Base delays in seconds
        base_delays = {
            'free': 300,       # 5 minutes
            'starter': 180,    # 3 minutes  
            'pro': 60,         # 1 minute
            'enterprise': 30,  # 30 seconds
            'basic': 180,      # 3 minutes
        }
        
        delay = base_delays.get(tier, 300)
        
        # Apply randomization (0.5x to 1.5x)
        delay = delay * random.uniform(0.5, 1.5)
        
        # Add risk penalty
        risk_score = cls.calculate_risk_score(user)
        if risk_score > 60:
            delay *= 3  # Triple delay
        elif risk_score > 40:
            delay *= 2  # Double delay
        elif risk_score > 25:
            delay *= 1.5  # 1.5x delay
        
        # Add micro-delays for realism
        delay += random.uniform(0, 5)  # 0-5 seconds
        
        return int(delay)
    
    @classmethod
    def should_pause_automation(cls, user) -> Tuple[bool, str]:
        """Check if automation should be paused for safety."""
        score = cls.calculate_risk_score(user)
        
        if score >= 80:
            return True, "Account flagged for review. Automation paused for safety. Please contact support."
        elif score >= 65:
            return True, "Elevated risk detected. Reducing your sending rate automatically."
        
        return False, ""
    
    @classmethod
    def get_risk_level(cls, score: int) -> dict:
        """Get risk level details for UI display."""
        if score <= 30:
            return {
                'level': 'green',
                'label': 'Safe',
                'message': 'Your account is operating normally.',
                'action': None
            }
        elif score <= 50:
            return {
                'level': 'yellow',
                'label': 'Moderate',
                'message': 'Your sending rate is elevated. Consider slowing down.',
                'action': 'reduce_rate'
            }
        elif score <= 75:
            return {
                'level': 'orange',
                'label': 'High',
                'message': 'Your account is at risk. We\'ve reduced your sending rate.',
                'action': 'force_cooldown'
            }
        else:
            return {
                'level': 'red',
                'label': 'Critical',
                'message': 'Your automation has been paused for safety.',
                'action': 'auto_pause'
            }


class MessageSimulator:
    """
    Simulates human-like behavior to avoid detection.
    """
    
    @classmethod
    def get_typing_delay(cls, message_content: str) -> int:
        """
        Calculate realistic typing time based on message length.
        People type ~200 chars per minute average.
        """
        # Words per minute
        wpm = random.uniform(150, 250)
        word_count = len(message_content.split())
        
        # Calculate base typing time in seconds
        typing_time = (word_count / wpm) * 60
        
        # Add randomness (pauses, corrections)
        typing_time *= random.uniform(0.8, 1.3)
        
        # Add thinking time (1-3 seconds)
        typing_time += random.uniform(1, 3)
        
        return int(typing_time)
    
    @classmethod
    def should_send_typing_indicator(cls) -> bool:
        """Random chance to show typing indicator."""
        return random.random() > 0.3  # 70% chance
    
    @classmethod
    def get_random_hour_offset(cls) -> int:
        """
        For scheduled messages, add random hour offset
        to avoid all messages going out at exact scheduled time.
        """
        return random.randint(-2, 2)  # -2 to +2 hours
    
    @classmethod
    def should_vary_message(cls, template_content: str) -> bool:
        """
        Check if message content should be varied.
        Some templates benefit from slight variations.
        """
        # Only vary messages > 50 chars
        return len(template_content) > 50 and random.random() > 0.7


class RateLimitEnforcer:
    """
    Enforces rate limits per plan tier.
    """
    
    LIMITS = {
        'free': {
            'daily': 50,
            'hourly': 10,
            'per_message_delay': 300,  # 5 minutes
        },
        'basic': {
            'daily': 200,
            'hourly': 50,
            'per_message_delay': 180,  # 3 minutes
        },
        'starter': {
            'daily': 500,
            'hourly': 100,
            'per_message_delay': 120,  # 2 minutes
        },
        'pro': {
            'daily': 2000,
            'hourly': 300,
            'per_message_delay': 60,   # 1 minute
        },
        'enterprise': {
            'daily': 10000,
            'hourly': 1000,
            'per_message_delay': 30,   # 30 seconds
        }
    }
    
    @classmethod
    def get_limits(cls, tier: str) -> dict:
        """Get rate limits for a given tier."""
        return cls.LIMITS.get(tier, cls.LIMITS['free'])
    
    @classmethod
    def check_daily_limit(cls, user) -> Tuple[bool, str]:
        """Check if user has exceeded daily limit."""
        from whatsapp_api.api.models import MessageLog
        from django.utils import timezone
        
        tier = getattr(user, 'subscription_tier', 'free')
        limits = cls.get_limits(tier)
        
        today = timezone.now().date()
        sent_today = MessageLog.objects.filter(
            user=user,
            sent_at__date=today
        ).count()
        
        if sent_today >= limits['daily']:
            return False, f"Daily limit of {limits['daily']} messages reached. Upgrade for more."
        
        # Return remaining
        remaining = limits['daily'] - sent_today
        return True, f"{remaining} messages remaining today"
    
    @classmethod
    def check_hourly_limit(cls, user) -> Tuple[bool, str]:
        """Check if user has exceeded hourly limit."""
        from whatsapp_api.api.models import MessageLog
        from django.utils import timezone
        
        tier = getattr(user, 'subscription_tier', 'free')
        limits = cls.get_limits(tier)
        
        since = timezone.now() - timedelta(hours=1)
        sent_this_hour = MessageLog.objects.filter(
            user=user,
            sent_at__gte=since
        ).count()
        
        if sent_this_hour >= limits['hourly']:
            return False, f"Hourly limit reached. Wait {cls.get_limits(tier)['per_message_delay']}s between messages."
        
        return True, ""
    
    @classmethod
    def get_cooldown_period(cls, user) -> int:
        """Get required cooldown between messages."""
        tier = getattr(user, 'subscription_tier', 'free')
        return cls.get_limits(tier)['per_message_delay']
    
    @classmethod
    def can_send_message(cls, user) -> Tuple[bool, str]:
        """Full check if user can send a message."""
        # Check daily limit
        can_send, message = cls.check_daily_limit(user)
        if not can_send:
            return False, message
        
        # Check hourly limit
        can_send, message = cls.check_hourly_limit(user)
        if not can_send:
            return False, message
        
        # Check risk-based pause
        should_pause, pause_message = WhatsAppRiskManager.should_pause_automation(user)
        if should_pause:
            return False, pause_message
        
        return True, "OK"


class ComplianceManager:
    """
    Ensures compliance with WhatsApp policies.
    """
    
    # Prohibited content patterns
    SPAM_PATTERNS = [
        'click here',
        'act now',
        'limited time',
        'won prize',
        'congratulations',
        'urgent action',
        'verify your account',
        'suspended account',
    ]
    
    @classmethod
    def check_message_content(cls, content: str) -> Tuple[bool, Optional[str]]:
        """
        Check if message content violates policies.
        
        Returns: (is_safe, warning_message)
        """
        content_lower = content.lower()
        
        # Check for spam patterns
        for pattern in cls.SPAM_PATTERNS:
            if pattern in content_lower:
                return False, f"Message contains potentially spammy content: '{pattern}'"
        
        # Check for excessive caps
        if sum(1 for c in content if c.isupper()) / len(content) > 0.5:
            return False, "Avoid excessive capitalization"
        
        # Check for excessive links
        link_count = content.count('http')
        if link_count > 5:
            return False, "Too many links in message"
        
        return True, None
    
    @classmethod
    def requires_approval(cls, user, message_content: str) -> bool:
        """
        Check if message requires manual approval.
        
        New accounts or high-risk content requires approval.
        """
        # Check account age
        account_age = (timezone.now() - user.created_at).days
        
        if account_age < 7:
            # New accounts need approval for bulk messages
            return len(message_content) > 500
        
        # Check risk score
        risk_score = WhatsAppRiskManager.calculate_risk_score(user)
        if risk_score > 50:
            return True
        
        return False
