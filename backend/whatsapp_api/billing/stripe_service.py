"""
Stripe payment integration service.
Handles checkout sessions, webhooks, and subscription management.
"""
import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service class for Stripe operations."""
    
    def __init__(self):
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    # ==================== CUSTOMER OPERATIONS ====================
    
    def create_customer(self, user, email=None):
        """Create a Stripe customer for a user."""
        try:
            customer = stripe.Customer.create(
                email=email or user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                }
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise
    
    def get_customer(self, customer_id):
        """Retrieve a Stripe customer."""
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer: {e}")
            raise
    
    def update_customer(self, customer_id, **kwargs):
        """Update a Stripe customer."""
        try:
            return stripe.Customer.modify(customer_id, **kwargs)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer: {e}")
            raise
    
    # ==================== SUBSCRIPTION OPERATIONS ====================
    
    def create_checkout_session(
        self,
        user,
        plan,
        success_url,
        cancel_url,
        coupon_code=None,
        trial_days=7
    ):
        """
        Create a Stripe checkout session for subscription.
        """
        try:
            # Get or create customer
            from .models import Subscription
            subscription = getattr(user, 'subscription', None)
            
            if subscription and subscription.stripe_customer_id:
                customer_id = subscription.stripe_customer_id
            else:
                customer = self.create_customer(user)
                customer_id = customer.id
            
            # Determine price ID based on billing interval
            price_id = plan.stripe_price_id_monthly
            
            # Build session params
            session_params = {
                'customer': customer_id,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'plan_tier': plan.tier,
                },
                'allow_promotion_codes': True,
                'subscription_data': {
                    'metadata': {
                        'user_id': str(user.id),
                        'plan_id': str(plan.id),
                    },
                },
            }
            
            # Add trial if specified
            if trial_days > 0:
                session_params['subscription_data']['trial_period_days'] = trial_days
            
            # Apply coupon if provided
            if coupon_code:
                from .models import Coupon
                try:
                    coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                    if coupon.is_valid():
                        if coupon.discount_type == 'percentage':
                            session_params['discounts'] = [{
                                'coupon': self.create_coupon(coupon)
                            }]
                        elif coupon.discount_type == 'fixed':
                            session_params['discounts'] = [{
                                'coupon': self.create_coupon(coupon)
                            }]
                except Coupon.DoesNotExist:
                    pass
            
            session = stripe.checkout.Session.create(**session_params)
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
    
    def create_coupon(self, coupon):
        """
        Create a Stripe coupon from our Coupon model.
        """
        try:
            stripe_coupon = stripe.Coupon.create(
                percent_off=coupon.discount_value if coupon.discount_type == 'percentage' else None,
                amount_off=int(coupon.discount_value * 100) if coupon.discount_type == 'fixed' else None,
                currency='usd',
                duration='once',
                max_redemptions=coupon.max_uses - coupon.current_uses,
            )
            return stripe_coupon.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe coupon: {e}")
            return None
    
    def create_portal_session(self, customer_id, return_url):
        """Create a customer portal session for managing subscription."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            raise
    
    def cancel_subscription(self, subscription_id, at_period_end=True):
        """Cancel a subscription."""
        try:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=at_period_end
            )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise
    
    def reactivate_subscription(self, subscription_id):
        """Reactivate a canceled subscription."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to reactivate subscription: {e}")
            raise
    
    def change_plan(self, subscription_id, new_price_id):
        """Change subscription to a different plan."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update the subscription item with new price
            stripe.SubscriptionItem.modify(
                subscription['items']['data'][0].id,
                price=new_price_id,
            )
            
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to change plan: {e}")
            raise
    
    # ==================== PAYMENT METHODS ====================
    
    def attach_payment_method(self, customer_id, payment_method_id):
        """Attach a payment method to a customer."""
        try:
            return stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise
    
    def detach_payment_method(self, payment_method_id):
        """Detach a payment method from a customer."""
        try:
            return stripe.PaymentMethod.detach(payment_method_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to detach payment method: {e}")
            raise
    
    def set_default_payment_method(self, customer_id, payment_method_id):
        """Set default payment method for a customer."""
        try:
            return stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id
                }
            )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to set default payment method: {e}")
            raise
    
    # ==================== WEBHOOK HANDLING ====================
    
    def construct_webhook_event(self, payload, signature):
        """Construct and verify webhook event."""
        try:
            return stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise
        except ValueError:
            logger.error("Invalid payload")
            raise
    
    def handle_webhook(self, event):
        """
        Handle Stripe webhook events.
        Returns True if handled successfully.
        """
        from .models import (
            Subscription, UsageRecord, BillingHistory, 
            UserCoupon, Coupon
        )
        
        event_type = event['type']
        data = event['data']['object']
        
        handlers = {
            'checkout.session.completed': self.handle_checkout_completed,
            'customer.subscription.created': self.handle_subscription_created,
            'customer.subscription.updated': self.handle_subscription_updated,
            'customer.subscription.deleted': self.handle_subscription_deleted,
            'invoice.paid': self.handle_invoice_paid,
            'invoice.payment_failed': self.handle_invoice_payment_failed,
            'invoice.payment_succeeded': self.handle_invoice_paid,
            'customer.deleted': self.handle_customer_deleted,
            'coupon.redemption.created': self.handle_coupon_redemption,
        }
        
        handler = handlers.get(event_type)
        if handler:
            try:
                return handler(data, event)
            except Exception as e:
                logger.error(f"Error handling {event_type}: {e}")
                return False
        
        logger.info(f"Unhandled webhook event: {event_type}")
        return True
    
    def handle_checkout_completed(self, session, event):
        """Handle successful checkout session."""
        from .models import Subscription, Plan
        
        user_id = session.get('metadata', {}).get('user_id')
        if not user_id:
            return False
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return False
        
        plan_id = session.get('metadata', {}).get('plan_id')
        if not plan_id:
            return False
        
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            logger.error(f"Plan {plan_id} not found")
            return False
        
        # Create or update subscription
        subscription, _ = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': plan,
                'stripe_customer_id': session.get('customer'),
            }
        )
        
        if session.get('subscription'):
            subscription.stripe_subscription_id = session.get('subscription')
            subscription.status = 'trialing' if session.get('subscription', {}).get('status') == 'trialing' else 'active'
        
        subscription.save()
        
        # Record billing history
        BillingHistory.objects.create(
            user=user,
            event_type='subscription_created',
            stripe_event_id=event.get('id'),
            stripe_invoice_id=session.get('invoice'),
            amount=Decimal(str(session.get('amount_total', 0) / 100)),
            plan_name=plan.name,
            status='completed',
        )
        
        return True
    
    def handle_subscription_created(self, subscription_data, event):
        """Handle new subscription."""
        from .models import Subscription, BillingHistory
        
        user_id = subscription_data.get('metadata', {}).get('user_id')
        if not user_id:
            return False
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return False
        
        try:
            subscription = Subscription.objects.get(user=user)
            subscription.stripe_subscription_id = subscription_data.get('id')
            subscription.status = subscription_data.get('status', 'active')
            
            # Set period dates
            if subscription_data.get('current_period_start'):
                subscription.current_period_start = timezone.datetime.fromtimestamp(
                    subscription_data['current_period_start'],
                    tz=timezone.utc
                )
            if subscription_data.get('current_period_end'):
                subscription.current_period_end = timezone.datetime.fromtimestamp(
                    subscription_data['current_period_end'],
                    tz=timezone.utc
                )
            
            subscription.save()
            
            BillingHistory.objects.create(
                user=user,
                event_type='subscription_created',
                stripe_event_id=event.get('id'),
                plan_name=subscription.plan.name,
                status='completed',
            )
            
        except Subscription.DoesNotExist:
            pass
        
        return True
    
    def handle_subscription_updated(self, subscription_data, event):
        """Handle subscription updates."""
        from .models import Subscription, BillingHistory
        
        subscription_id = subscription_data.get('id')
        if not subscription_id:
            return False
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        except Subscription.DoesNotExist:
            return False
        
        # Update status
        old_status = subscription.status
        new_status = subscription_data.get('status')
        
        if new_status and old_status != new_status:
            subscription.status = new_status
            
            if new_status == 'canceled':
                subscription.canceled_at = timezone.now()
        
        # Update period dates
        if subscription_data.get('current_period_start'):
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription_data['current_period_start'],
                tz=timezone.utc
            )
        if subscription_data.get('current_period_end'):
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription_data['current_period_end'],
                tz=timezone.utc
            )
        
        subscription.save()
        
        # Record history
        BillingHistory.objects.create(
            user=subscription.user,
            event_type='subscription_updated',
            stripe_event_id=event.get('id'),
            plan_name=subscription.plan.name,
            description=f'Status: {old_status} -> {new_status}',
            status='completed',
        )
        
        return True
    
    def handle_subscription_deleted(self, subscription_data, event):
        """Handle subscription cancellation."""
        from .models import Subscription, BillingHistory
        
        subscription_id = subscription_data.get('id')
        if not subscription_id:
            return False
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
            subscription.save()
            
            BillingHistory.objects.create(
                user=subscription.user,
                event_type='subscription_canceled',
                stripe_event_id=event.get('id'),
                plan_name=subscription.plan.name,
                status='completed',
            )
            
        except Subscription.DoesNotExist:
            pass
        
        return True
    
    def handle_invoice_paid(self, invoice_data, event):
        """Handle successful payment."""
        from .models import Subscription, BillingHistory
        
        customer_id = invoice_data.get('customer')
        if not customer_id:
            return False
        
        try:
            subscription = Subscription.objects.get(stripe_customer_id=customer_id)
        except Subscription.DoesNotExist:
            return False
        
        # Update subscription dates
        if invoice_data.get('period_start'):
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                invoice_data['period_start'],
                tz=timezone.utc
            )
        if invoice_data.get('period_end'):
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                invoice_data['period_end'],
                tz=timezone.utc
            )
        
        subscription.last_payment_date = timezone.now()
        subscription.last_payment_status = 'succeeded'
        subscription.save()
        
        # Record billing history
        BillingHistory.objects.create(
            user=subscription.user,
            event_type='payment_succeeded',
            stripe_event_id=event.get('id'),
            stripe_invoice_id=invoice_data.get('id'),
            amount=Decimal(str(invoice_data.get('amount_paid', 0) / 100)),
            currency=invoice_data.get('currency', 'usd'),
            plan_name=subscription.plan.name,
            status='completed',
        )
        
        return True
    
    def handle_invoice_payment_failed(self, invoice_data, event):
        """Handle failed payment."""
        from .models import Subscription, BillingHistory
        
        customer_id = invoice_data.get('customer')
        if not customer_id:
            return False
        
        try:
            subscription = Subscription.objects.get(stripe_customer_id=customer_id)
        except Subscription.DoesNotExist:
            return False
        
        subscription.status = 'past_due'
        subscription.last_payment_status = 'failed'
        subscription.save()
        
        BillingHistory.objects.create(
            user=subscription.user,
            event_type='payment_failed',
            stripe_event_id=event.get('id'),
            stripe_invoice_id=invoice_data.get('id'),
            amount=Decimal(str(invoice_data.get('amount_due', 0) / 100)),
            currency=invoice_data.get('currency', 'usd'),
            plan_name=subscription.plan.name,
            status='failed',
            failure_message=invoice_data.get('host_invoice_description', 'Payment failed'),
        )
        
        return True
    
    def handle_customer_deleted(self, customer_data, event):
        """Handle customer deletion."""
        from .models import Subscription
        
        customer_id = customer_data.get('id')
        if not customer_id:
            return False
        
        Subscription.objects.filter(stripe_customer_id=customer_id).update(
            status='canceled'
        )
        
        return True
    
    def handle_coupon_redemption(self, redemption_data, event):
        """Handle coupon redemption."""
        coupon_id = redemption_data.get('coupon')
        customer_id = redemption_data.get('customer')
        
        if not coupon_id or not customer_id:
            return False
        
        try:
            from .models import Coupon, UserCoupon, Subscription
            stripe_coupon = stripe.Coupon.retrieve(coupon_id)
            
            coupon = Coupon.objects.filter(
                code__icontains=stripe_coupon.get('id', '')
            ).first()
            
            if coupon:
                subscription = Subscription.objects.filter(
                    stripe_customer_id=customer_id
                ).first()
                
                if subscription:
                    coupon.current_uses += 1
                    coupon.save()
                    
                    UserCoupon.objects.create(
                        user=subscription.user,
                        coupon=coupon,
                    )
                    
        except Exception as e:
            logger.error(f"Error handling coupon redemption: {e}")
        
        return True


# Create service instance
stripe_service = StripeService()
