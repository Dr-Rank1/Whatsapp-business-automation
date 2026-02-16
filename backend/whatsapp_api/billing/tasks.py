"""
Billing Celery tasks for subscription management.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def check_trial_expiration():
    """
    Check for trials expiring soon and send reminders.
    Run daily via Celery Beat.
    """
    from whatsapp_api.billing.models import Subscription, BillingHistory
    
    now = timezone.now()
    three_days = now + timedelta(days=3)
    
    # Find trialing subscriptions expiring within 3 days
    expiring_trials = Subscription.objects.filter(
        status='trialing',
        trial_end__lte=three_days,
        trial_end__gte=now
    )
    
    notified_count = 0
    
    for subscription in expiring_trials:
        try:
            days_remaining = (subscription.trial_end - now).days
            
            # Create notification record
            # In production, integrate with email/SMS service
            
            logger.info(f"Trial expiring for user {subscription.user.id} in {days_remaining} days")
            
            # Log the notification
            BillingHistory.objects.create(
                user=subscription.user,
                event_type='trial_ending_soon',
                description=f"Trial ends in {days_remaining} days",
                status='completed'
            )
            
            notified_count += 1
            
        except Exception as e:
            logger.error(f"Error processing trial for user {subscription.user.id}: {str(e)}")
    
    return {'notified': notified_count}


@shared_task
def process_subscription_renewals():
    """
    Process subscription renewals and handle failed payments.
    Run daily via Celery Beat.
    """
    from whatsapp_api.billing.models import Subscription, BillingHistory
    from whatsapp_api.billing.stripe_service import stripe_service
    
    now = timezone.now()
    
    # Find subscriptions ending tomorrow
    ending_tomorrow = Subscription.objects.filter(
        status='active',
        current_period_end__date=(now + timedelta(days=1)).date()
    )
    
    for subscription in ending_tomorrow:
        try:
            # In production, this would:
            # 1. Charge the customer via Stripe
            # 2. Handle payment failures
            # 3. Send renewal receipts
            
            logger.info(f"Processing renewal for subscription {subscription.id}")
            
            # Update billing history
            BillingHistory.objects.create(
                user=subscription.user,
                event_type='subscription_renewed',
                plan_name=subscription.plan.name,
                amount=subscription.plan.price_monthly,
                status='completed'
            )
            
        except Exception as e:
            logger.error(f"Error processing renewal for subscription {subscription.id}: {str(e)}")
            
            # Mark as past due
            subscription.status = 'past_due'
            subscription.save()
            
            BillingHistory.objects.create(
                user=subscription.user,
                event_type='payment_failed',
                plan_name=subscription.plan.name,
                status='failed',
                failure_message=str(e)
            )
    
    return {'processed': ending_tomorrow.count()}


@shared_task
def cancel_expired_trials():
    """
    Cancel trials that have expired without conversion.
    Run daily via Celery Beat.
    """
    from whatsapp_api.billing.models import Subscription, Plan, BillingHistory
    
    now = timezone.now()
    
    # Find expired trials
    expired_trials = Subscription.objects.filter(
        status='trialing',
        trial_end__lt=now
    )
    
    cancelled_count = 0
    
    for subscription in expired_trials:
        try:
            # Downgrade to free plan
            free_plan = Plan.objects.get(tier='free')
            subscription.plan = free_plan
            subscription.status = 'canceled'
            subscription.canceled_at = now
            subscription.save()
            
            # Log the event
            BillingHistory.objects.create(
                user=subscription.user,
                event_type='trial_ended',
                description='Trial expired - downgraded to free plan',
                status='completed'
            )
            
            cancelled_count += 1
            
            logger.info(f"Cancelled expired trial for user {subscription.user.id}")
            
        except Exception as e:
            logger.error(f"Error cancelling trial for user {subscription.user.id}: {str(e)}")
    
    return {'cancelled': cancelled_count}


@shared_task
def process_referral_rewards():
    """
    Process referral rewards for completed referrals.
    Run daily via Celery Beat.
    """
    from whatsapp_api.billing.models import Referral, BillingHistory, Subscription
    
    # Find referrals where the referred user has subscribed
    completed_referrals = Referral.objects.filter(
        status='subscribed',
        referrer_reward_claimed=False
    )
    
    rewarded_count = 0
    
    for referral in completed_referrals:
        try:
            # Check if referrer has active subscription
            subscription = getattr(referral.referrer, 'subscription', None)
            
            if subscription and subscription.is_active:
                # Award referrer reward (e.g., one month free or credits)
                # This is a simplified implementation
                
                referral.referrer_reward_claimed = True
                referral.save()
                
                # Log the reward
                BillingHistory.objects.create(
                    user=referral.referrer,
                    event_type='referral_reward',
                    description=f'Referral reward for referring {referral.referred_email}',
                    amount=0,  # Would be actual reward value
                    status='completed'
                )
                
                rewarded_count += 1
                
        except Exception as e:
            logger.error(f"Error processing referral {referral.id}: {str(e)}")
    
    return {'rewarded': rewarded_count}


@shared_task
def send_usage_alerts():
    """
    Send usage alerts to users approaching their limits.
    Run daily via Celery Beat.
    """
    from whatsapp_api.billing.models import UsageRecord, Subscription, Plan
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    now = timezone.now()
    
    # Get all users with usage > 80%
    usage_records = UsageRecord.objects.filter(
        year=now.year,
        month=now.month
    )
    
    alerted_count = 0
    
    for usage in usage_records:
        try:
            if usage.message_limit > 0:
                percentage = (usage.messages_sent / usage.message_limit) * 100
                
                # Send alert at 80% and 90%
                if percentage >= 80:
                    # In production, send email/push notification
                    logger.info(f"Usage alert for user {usage.user.id}: {percentage:.1f}% used")
                    alerted_count += 1
                    
        except Exception as e:
            logger.error(f"Error checking usage for user {usage.user.id}: {str(e)}")
    
    return {'alerted': alerted_count}


@shared_task
def generate_monthly_invoices():
    """
    Generate monthly invoices for all paid subscriptions.
    Run on 1st of each month via Celery Beat.
    """
    from whatsapp_api.billing.models import Subscription, BillingHistory
    
    now = timezone.now()
    last_month = now - timedelta(days=30)
    
    # Get active paid subscriptions
    paid_subscriptions = Subscription.objects.filter(
        status='active'
    ).exclude(
        plan__tier='free'
    )
    
    invoices_created = 0
    
    for subscription in paid_subscriptions:
        try:
            # Determine billing amount based on interval
            if subscription.billing_interval == 'yearly':
                amount = subscription.plan.price_yearly / 12
            else:
                amount = subscription.plan.price_monthly
            
            # Create invoice record
            BillingHistory.objects.create(
                user=subscription.user,
                event_type='invoice_created',
                plan_name=subscription.plan.name,
                amount=amount,
                description=f'Monthly invoice for {now.strftime("%B %Y")}',
                status='pending'
            )
            
            invoices_created += 1
            
        except Exception as e:
            logger.error(f"Error generating invoice for user {subscription.user.id}: {str(e)}")
    
    return {'invoices_created': invoices_created}
