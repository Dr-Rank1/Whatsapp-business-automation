"""
Initial data seeder for Kenyan market - subscription plans in KES.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load initial subscription plans optimized for Kenyan market'

    def handle(self, *args, **options):
        from whatsapp_api.billing.models import Plan
        from whatsapp_api.api.models import MessageTemplate

        # KES Pricing for Kenyan Market
        plans = [
            {
                'name': 'Free',
                'tier': 'free',
                'description': 'Perfect for trying out WhatsApp automation',
                'price_monthly': Decimal('0'),
                'price_yearly': Decimal('0'),
                'monthly_message_limit': 100,
                'max_contacts': 50,
                'max_campaigns': 1,
                'max_scheduled_messages': 10,
                'max_templates': 5,
                'max_team_members': 1,
                'allow_bulk_sending': False,
                'allow_scheduling': False,
                'allow_analytics': False,
                'allow_api_access': False,
                'priority_support': False,
                'custom_branding': False,
                'display_order': 1,
                'is_active': True,
            },
            {
                'name': 'Starter',
                'tier': 'starter',
                'description': 'Perfect for small businesses and online sellers',
                'price_monthly': Decimal('1499'),
                'price_yearly': Decimal('14990'),  # 2 months free
                'monthly_message_limit': 2000,
                'max_contacts': 500,
                'max_campaigns': 5,
                'max_scheduled_messages': 50,
                'max_templates': 20,
                'max_team_members': 2,
                'allow_bulk_sending': True,
                'allow_scheduling': True,
                'allow_analytics': False,
                'allow_api_access': False,
                'priority_support': False,
                'custom_branding': False,
                'display_order': 2,
                'is_active': True,
            },
            {
                'name': 'Pro',
                'tier': 'pro',
                'description': 'For growing businesses with CRM needs',
                'price_monthly': Decimal('3999'),
                'price_yearly': Decimal('39990'),  # 2 months free
                'monthly_message_limit': 10000,
                'max_contacts': 2000,
                'max_campaigns': 20,
                'max_scheduled_messages': 200,
                'max_templates': 100,
                'max_team_members': 5,
                'allow_bulk_sending': True,
                'allow_scheduling': True,
                'allow_analytics': True,
                'allow_api_access': True,
                'priority_support': True,
                'custom_branding': False,
                'is_popular': True,
                'display_order': 3,
                'is_active': True,
            },
            {
                'name': 'Agency',
                'tier': 'enterprise',
                'description': 'For agencies managing multiple clients',
                'price_monthly': Decimal('9999'),
                'price_yearly': Decimal('99990'),
                'monthly_message_limit': 50000,
                'max_contacts': 10000,
                'max_campaigns': 100,
                'max_scheduled_messages': 1000,
                'max_templates': 500,
                'max_team_members': 25,
                'allow_bulk_sending': True,
                'allow_scheduling': True,
                'allow_analytics': True,
                'allow_api_access': True,
                'priority_support': True,
                'custom_branding': True,
                'display_order': 4,
                'is_active': True,
            },
        ]

        for plan_data in plans:
            plan, created = Plan.objects.update_or_create(
                tier=plan_data['tier'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.name} (KES {plan.price_monthly}/month)'))
            else:
                self.stdout.write(f'Updated plan: {plan.name} (KES {plan.price_monthly}/month)')

        # Create Kenyan-specific message templates
        self.create_kenyan_templates()
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded Kenyan market data'))

    def create_kenyan_templates(self):
        """Create pre-built templates for Kenyan market."""
        from whatsapp_api.api.models import MessageTemplate
        
        # Default user for templates (system templates)
        # In production, these would be available to all users
        templates = [
            {
                'name': 'Order Confirmed (Jumia Style)',
                'content': '''Hello {{name}}! 👋

Your order has been CONFIRMED! 🎉

Order Details:
📦 Item: {{item}}
💰 Amount: KES {{amount}}
📋 Order ID: {{order_id}}

We'll notify you once it's shipped! 🚚

Thank you for choosing us!''',
                'category': 'notification',
            },
            {
                'name': 'M-Pesa Payment Request',
                'content': '''Hi {{name}}! 💰

To complete your purchase, please follow these steps:

1. Go to M-Pesa
2. Select "Pay Bill"
3. Business Number: 123456
4. Account Number: {{order_id}}
5. Amount: KES {{amount}}

After payment, you'll receive confirmation!''',
                'category': 'notification',
            },
            {
                'name': 'Delivery Update',
                'content': '''Hello {{name}}! 📦

Great news! Your order is on its way! 🛵

📋 Tracking: {{tracking_id}}
🚚 Estimated delivery: {{delivery_date}}

We'll notify you when it arrives!

Questions? Just reply!''',
                'category': 'notification',
            },
            {
                'name': 'Real Estate Inquiry',
                'content': '''Hi {{name}}! 🏠

Thank you for your interest in our property!

Property: {{property_name}}
Location: {{location}}

📞 Call us for viewing: 0712 345 678
💬 WhatsApp us here

We're excited to help you find your dream home!''',
                'category': 'greeting',
            },
            {
                'name': 'Car Inquiry Response',
                'content': '''Hi {{name}}! 🚗

Thank you for your interest in the {{car_model}}!

📊 Price: KES {{price}}
✅ Condition: {{condition}}
📍 Location: {{location}}

For more photos and details, visit our yard or WhatsApp us!

Ready to view? Let us know!''',
                'category': 'greeting',
            },
            {
                'name': 'Price List Request',
                'content': '''Hi {{name}}! 📋

Thanks for your interest! Here's our price list:

{{price_list}}

📦 Minimum order: KES {{min_order}}
🚚 Delivery: Within Nairobi

Place your order by replying with:
- Item names
- Quantities
- Your location

We accept M-Pesa! 💰''',
                'category': 'support',
            },
            {
                'name': 'Follow-up After Sale',
                'content': '''Hi {{name}}! 👋

Just checking in! How are you enjoying your {{product}}?

We'd love to hear your feedback! 🌟

Need any support? We're here to help!

Thanks for choosing us!
{{company_name}}''',
                'category': 'followup',
            },
            {
                'name': 'Booking Confirmation',
                'content': '''Hello {{name}}! 📅

Your booking is CONFIRMED! ✅

Event: {{event_name}}
Date: {{date}}
Time: {{time}}
Venue: {{venue}}

📝 Please arrive 10 minutes early.

Any questions? Just reply!

See you there!''',
                'category': 'notification',
            },
            {
                'name': 'Sacco/Microfinance Reminder',
                'content': '''Hello {{name}}! 💼

Reminder: Your contribution of KES {{amount}} is due on {{due_date}}.

💳 Pay via M-Pesa:
- Business Number: 123456
- Account: Your member number

Questions? Call: 0712 345 678

Thank you for your partnership!''',
                'category': 'notification',
            },
            {
                'name': 'Forex/Crypto Signal',
                'content': '''📈 {{signal_type}} Signal

Pair: {{currency_pair}}
Entry: {{entry_price}}
Take Profit: {{tp1}} / {{tp2}}
Stop Loss: {{sl}}

Valid until: {{expiry}}

⚠️ Trade at your own risk. Do your own research!

#trading #forex #crypto''',
                'category': 'promotional',
            },
        ]

        # Only create if not exists
        for template_data in templates:
            template, created = MessageTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'content': template_data['content'],
                    'category': template_data['category'],
                    'user_id': 1,  # System templates owned by admin
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created template: {template.name}')
