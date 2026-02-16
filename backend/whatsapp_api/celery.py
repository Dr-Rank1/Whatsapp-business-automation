"""
Celery configuration for WhatsApp Business Automation.
Handles background tasks for scheduled messages, campaigns, and usage tracking.
"""
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_api.settings')

app = Celery('whatsapp_api')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule for recurring tasks
app.conf.beat_schedule = {
    # Process scheduled messages every minute
    'process-scheduled-messages': {
        'task': 'whatsapp_api.api.tasks.process_scheduled_messages',
        'schedule': 60.0,  # Every minute
    },
    
    # Cleanup old message logs weekly
    'cleanup-old-logs': {
        'task': 'whatsapp_api.api.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Update usage analytics daily
    'update-usage-analytics': {
        'task': 'whatsapp_api.api.tasks.update_usage_analytics',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    
    # Send trial expiration reminders
    'check-trial-expiration': {
        'task': 'whatsapp_api.billing.tasks.check_trial_expiration',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    
    # Process pending webhooks
    'process-webhooks': {
        'task': 'whatsapp_api.api.tasks.process_pending_webhooks',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# Task settings
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Task routing for different queues
app.conf.task_routes = {
    'whatsapp_api.api.tasks.send_message_*': {'queue': 'messages'},
    'whatsapp_api.api.tasks.process_campaign_*': {'queue': 'campaigns'},
    'whatsapp_api.billing.tasks.*': {'queue': 'billing'},
}

# Rate limiting
app.conf.task_default_rate_limit = '100/m'

# Result expiration
app.conf.result_expires = 86400  # 24 hours

# Task track started
app.conf.task_track_started = True

# Task time limits
app.conf.task_soft_time_limit = 300  # 5 minutes
app.conf.task_time_limit = 600  # 10 minutes

# Retry settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
