"""
Celery tasks for WhatsApp Business Automation.
Handles message sending, campaign processing, and scheduled tasks.
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
import time
import random

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_message_task(self, message_log_id, contact_id, content, user_id):
    """
    Send a single WhatsApp message.
    
    Args:
        message_log_id: ID of the MessageLog entry
        contact_id: ID of the Contact
        content: Message content
        user_id: ID of the User
    """
    from whatsapp_api.api.models import MessageLog, Contact, User
    from whatsapp_api.billing.models import UsageRecord, Subscription, Plan
    
    try:
        # Get message log
        message_log = MessageLog.objects.get(id=message_log_id)
        contact = Contact.objects.get(id=contact_id)
        user = User.objects.get(id=user_id)
        
        # Check if contact is blocked
        if contact.is_blocked:
            message_log.status = 'failed'
            message_log.error_message = 'Contact is blocked'
            message_log.save()
            return {'success': False, 'error': 'Contact is blocked'}
        
        # Check user subscription and usage limits
        subscription = getattr(user, 'subscription', None)
        
        # Get current month's usage
        now = timezone.now()
        usage, _ = UsageRecord.objects.get_or_create(
            user=user,
            year=now.year,
            month=now.month,
            defaults={
                'message_limit': subscription.plan.monthly_message_limit if subscription else 100
            }
        )
        
        # Check if user has reached limit
        if usage.messages_sent >= usage.message_limit:
            # Check if user can overage (premium plans only)
            if subscription and subscription.plan.tier in ['pro', 'enterprise']:
                # Allow with additional charge tracking (implementation depends on billing model)
                pass
            else:
                message_log.status = 'failed'
                message_log.error_message = 'Monthly message limit reached'
                message_log.save()
                return {'success': False, 'error': 'Message limit reached'}
        
        # Simulate WhatsApp API call (replace with actual WhatsApp API integration)
        # In production, this would call WhatsApp Business API
        success = _send_to_whatsapp_api(contact.phone, content)
        
        if success:
            # Update message log
            message_log.status = 'sent'
            message_log.sent_at = timezone.now()
            message_log.save()
            
            # Update usage
            usage.messages_sent += 1
            usage.save()
            
            # Update contact
            if not contact.name:
                # Could auto-fetch from WhatsApp
                pass
            
            logger.info(f"Message sent successfully to {contact.phone}")
            return {'success': True, 'message_id': message_log.id}
        else:
            # Handle failure
            message_log.status = 'failed'
            message_log.error_message = 'Failed to send message'
            message_log.save()
            
            usage.messages_failed += 1
            usage.save()
            
            return {'success': False, 'error': 'Failed to send message'}
            
    except MessageLog.DoesNotExist:
        logger.error(f"Message log {message_log_id} not found")
        return {'success': False, 'error': 'Message log not found'}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        
        # Retry logic
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            if message_log_id:
                try:
                    message_log = MessageLog.objects.get(id=message_log_id)
                    message_log.status = 'failed'
                    message_log.error_message = str(e)
                    message_log.save()
                except:
                    pass
            return {'success': False, 'error': str(e)}


def _send_to_whatsapp_api(phone, content):
    """
    Actual WhatsApp API integration.
    Replace this with your WhatsApp Business API implementation.
    """
    # Simulate API call
    time.sleep(random.uniform(0.1, 0.5))
    
    # In production, integrate with:
    # - WhatsApp Business Cloud API
    # - WhatsApp Business API (on-premise)
    # - Third-party WhatsApp aggregators
    
    # Return success/failure based on API response
    return True  # Simulate success


@shared_task
def process_scheduled_messages():
    """
    Process all pending scheduled messages that are due.
    Run every minute via Celery Beat.
    """
    from whatsapp_api.api.models import ScheduledMessage
    
    now = timezone.now()
    
    # Get all pending scheduled messages that are due
    pending_messages = ScheduledMessage.objects.filter(
        status='pending',
        scheduled_at__lte=now
    ).select_related('user', 'contact', 'template')[:100]
    
    processed_count = 0
    
    for scheduled in pending_messages:
        try:
            # Determine message content
            if scheduled.template:
                content = _process_template(scheduled.template.content, scheduled.contact)
            else:
                content = scheduled.message_content
            
            # Create message log
            message_log = scheduled.user.message_logs.create(
                contact=scheduled.contact,
                scheduled_message=scheduled,
                template=scheduled.template,
                message_content=content,
                status='pending'
            )
            
            # Queue message for sending
            send_message_task.delay(
                message_log.id,
                scheduled.contact.id,
                content,
                scheduled.user.id
            )
            
            # Update scheduled message status
            scheduled.status = 'scheduled'
            scheduled.save()
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing scheduled message {scheduled.id}: {str(e)}")
    
    return {'processed': processed_count}


@shared_task(bind=True, max_retries=3)
def process_campaign(self, campaign_id):
    """
    Process a campaign: send messages to all contacts.
    
    Args:
        campaign_id: ID of the Campaign
    """
    from whatsapp_api.api.models import Campaign, Contact
    
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        user = campaign.user
        
        # Get all contacts for this campaign
        contacts = campaign.contacts.all()
        
        # Update campaign status
        campaign.status = 'running'
        campaign.started_at = timezone.now()
        campaign.save()
        
        sent_count = 0
        failed_count = 0
        
        for contact in contacts:
            try:
                # Check if contact is blocked
                if contact.is_blocked:
                    failed_count += 1
                    continue
                
                # Determine message content
                if campaign.template:
                    content = _process_template(campaign.template.content, contact)
                else:
                    content = campaign.message_content
                
                # Create message log
                message_log = user.message_logs.create(
                    contact=contact,
                    campaign=campaign,
                    template=campaign.template,
                    message_content=content,
                    status='pending'
                )
                
                # Queue message with delay based on position
                delay = sent_count * campaign.delay_between_messages
                send_message_task.apply_async(
                    args=[message_log.id, contact.id, content, user.id],
                    countdown=delay
                )
                
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Error queuing message for contact {contact.id}: {str(e)}")
                failed_count += 1
        
        # Update campaign counts
        campaign.sent_count = sent_count
        campaign.failed_count = failed_count
        campaign.save()
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'sent': sent_count,
            'failed': failed_count
        }
        
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}
    except Exception as e:
        logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {'success': False, 'error': str(e)}


def _process_template(template_content, contact):
    """
    Replace template variables with contact data.
    
    Variables: {{name}}, {{phone}}, {{email}}, {{company}}
    """
    content = template_content
    content = content.replace('{{name}}', contact.name or 'Customer')
    content = content.replace('{{phone}}', contact.phone)
    content = content.replace('{{email}}', contact.email or '')
    content = content.replace('{{company}}', contact.company or '')
    return content


@shared_task
def retry_failed_messages():
    """
    Retry all failed messages that haven't exceeded max retries.
    """
    from whatsapp_api.api.models import MessageLog
    
    failed_messages = MessageLog.objects.filter(
        status='failed',
        retry_count__lt=3
    ).select_related('user', 'contact')[:50]
    
    retried_count = 0
    
    for message in failed_messages:
        try:
            message.status = 'pending'
            message.error_message = ''
            message.save()
            
            send_message_task.delay(
                message.id,
                message.contact.id,
                message.message_content,
                message.user.id
            )
            
            retried_count += 1
            
        except Exception as e:
            logger.error(f"Error retrying message {message.id}: {str(e)}")
    
    return {'retried': retried_count}


@shared_task
def cleanup_old_logs():
    """
    Clean up old message logs based on retention policy.
    Run daily via Celery Beat.
    """
    from whatsapp_api.api.models import MessageLog
    
    # Keep logs for 90 days
    retention_days = 90
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    deleted_count = MessageLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old message logs")
    return {'deleted': deleted_count}


@shared_task
def update_usage_analytics():
    """
    Update daily usage analytics for all users.
    Run daily via Celery Beat.
    """
    from whatsapp_api.api.models import MessageLog, Analytics, Contact, Campaign, ScheduledMessage
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    today = timezone.now().date()
    
    # Get all active users
    users = User.objects.filter(is_active=True)
    
    for user in users:
        try:
            # Calculate today's stats
            messages_sent = MessageLog.objects.filter(
                user=user,
                sent_at__date=today
            ).count()
            
            messages_delivered = MessageLog.objects.filter(
                user=user,
                status='delivered',
                delivered_at__date=today
            ).count()
            
            messages_failed = MessageLog.objects.filter(
                user=user,
                status='failed',
                created_at__date=today
            ).count()
            
            messages_read = MessageLog.objects.filter(
                user=user,
                status='read',
                read_at__date=today
            ).count()
            
            contacts_added = Contact.objects.filter(
                user=user,
                created_at__date=today
            ).count()
            
            campaigns_created = Campaign.objects.filter(
                user=user,
                created_at__date=today
            ).count()
            
            scheduled_count = ScheduledMessage.objects.filter(
                user=user,
                created_at__date=today
            ).count()
            
            # Update or create analytics record
            analytics, _ = Analytics.objects.update_or_create(
                user=user,
                date=today,
                defaults={
                    'messages_sent': messages_sent,
                    'messages_delivered': messages_delivered,
                    'messages_failed': messages_failed,
                    'messages_read': messages_read,
                    'contacts_added': contacts_added,
                    'campaigns_created': campaigns_created,
                    'scheduled_messages': scheduled_count,
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating analytics for user {user.id}: {str(e)}")
    
    return {'success': True}


@shared_task
def process_pending_webhooks():
    """
    Process pending webhook deliveries.
    """
    from whatsapp_api.api.models import WebhookDelivery
    
    pending = WebhookDelivery.objects.filter(
        status='pending',
        attempts__lt=5
    )[:20]
    
    for webhook in pending:
        try:
            webhook.deliver()
        except Exception as e:
            logger.error(f"Error delivering webhook {webhook.id}: {str(e)}")
    
    return {'processed': pending.count()}


@shared_task
def update_delivery_status(message_log_id, status, whatsapp_message_id=None):
    """
    Update message delivery status from WhatsApp webhook.
    
    Args:
        message_log_id: ID of the MessageLog
        status: New status (delivered, read, failed)
        whatsapp_message_id: WhatsApp message ID for tracking
    """
    from whatsapp_api.api.models import MessageLog
    from whatsapp_api.billing.models import UsageRecord
    
    try:
        message_log = MessageLog.objects.get(id=message_log_id)
        
        message_log.status = status
        
        if status == 'delivered':
            message_log.delivered_at = timezone.now()
        elif status == 'read':
            message_log.read_at = timezone.now()
        
        if whatsapp_message_id:
            message_log.whatsapp_message_id = whatsapp_message_id
        
        message_log.save()
        
        # Update usage counts
        if status == 'delivered':
            now = timezone.now()
            usage = UsageRecord.objects.filter(
                user=message_log.user,
                year=now.year,
                month=now.month
            ).first()
            
            if usage:
                usage.messages_delivered += 1
                usage.save()
        
        return {'success': True}
        
    except MessageLog.DoesNotExist:
        return {'success': False, 'error': 'Message log not found'}
