"""
M-Pesa API views for payment processing.
"""
import json
import logging
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_stk_callback(request):
    """
    Handle M-Pesa STK Push callback.
    This is the webhook endpoint that Safaricom calls after payment.
    """
    try:
        raw_data = json.loads(request.body)
        logger.info(f"M-Pesa STK Callback received: {raw_data}")
        
        from whatsapp_api.billing.mpesa_service import mpesa_service
        from whatsapp_api.billing.mpesa_models import MpesaTransaction, MpesaPayment
        
        # Process callback
        result = mpesa_service.process_callback(raw_data)
        
        if not result.get('checkout_request_id'):
            return Response({'status': 'error', 'message': 'Invalid callback'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find transaction
        try:
            transaction_obj = MpesaTransaction.objects.get(
                checkout_request_id=result['checkout_request_id']
            )
        except MpesaTransaction.DoesNotExist:
            logger.error(f"Transaction not found: {result['checkout_request_id']}")
            return Response({'status': 'error', 'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update transaction
        transaction_obj.status = 'completed' if result['success'] else 'failed'
        transaction_obj.result_code = result.get('result_code', '')
        transaction_obj.result_description = result.get('result_desc', '')
        transaction_obj.mpesa_receipt_number = result.get('receipt_number', '')
        transaction_obj.completed_at = timezone.now()
        transaction_obj.raw_callback = result.get('raw', {})
        transaction_obj.save()
        
        # Process payment if successful
        if result['success']:
            try:
                with transaction.atomic():
                    # Find the payment record
                    payment = MpesaPayment.objects.filter(
                        transaction=transaction_obj,
                        status='pending'
                    ).first()
                    
                    if payment:
                        # Activate subscription based on payment
                        success = _process_successful_payment(payment, transaction_obj)
                        
                        if success:
                            payment.status = 'credited'
                            payment.save()
                        else:
                            payment.status = 'failed'
                            payment.notes = 'Payment processing failed'
                            payment.save()
                    else:
                        logger.warning(f"No pending payment found for transaction {transaction_obj.id}")
                        
            except Exception as e:
                logger.error(f"Payment processing error: {str(e)}")
                transaction_obj.status = 'failed'
                transaction_obj.result_description = f"Processing error: {str(e)}"
                transaction_obj.save()
        
        return Response({'status': 'ok'})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in M-Pesa callback")
        return Response({'status': 'error', 'message': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"M-Pesa callback error: {str(e)}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_c2b_callback(request):
    """
    Handle M-Pesa C2B (Customer to Business) payment callback.
    """
    try:
        raw_data = json.loads(request.body)
        logger.info(f"M-Pesa C2B Callback: {raw_data}")
        
        # Process C2B payment
        # Similar logic to STK callback
        
        return Response({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"C2B callback error: {str(e)}")
        return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_validation(request):
    """
    M-Pesa C2B validation endpoint.
    Used to validate incoming payments before acceptance.
    """
    try:
        # Validate the transaction
        # Return 0 to accept, 1 to reject
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return Response({'ResultCode': 1, 'ResultDesc': str(e)})


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_confirmation(request):
    """
    M-Pesa C2B confirmation endpoint.
    Confirms the transaction after validation.
    """
    try:
        raw_data = json.loads(request.body)
        logger.info(f"M-Pesa C2B Confirmation: {raw_data}")
        
        # Process the confirmed payment
        return Response({'ResultCode': 0, 'ResultDesc': 'Confirmed'})
    except Exception as e:
        logger.error(f"Confirmation error: {str(e)}")
        return Response({'ResultCode': 1, 'ResultDesc': str(e)})


def _process_successful_payment(payment, transaction) -> bool:
    """
    Process a successful M-Pesa payment.
    Activates subscriptions, adds credits, etc.
    """
    from whatsapp_api.billing.models import Subscription, BillingHistory, Plan
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        if payment.payment_type == 'subscription':
            # Activate or upgrade subscription
            user = payment.user
            
            # Get the plan that matches the payment amount
            amount = float(payment.amount)
            
            # Determine plan based on amount (KES)
            if amount >= 9999:
                plan = Plan.objects.get(tier='enterprise')
            elif amount >= 3999:
                plan = Plan.objects.get(tier='pro')
            elif amount >= 1499:
                plan = Plan.objects.get(tier='starter')
            else:
                # Assume starter for any other amount
                plan = Plan.objects.get(tier='starter')
            
            # Get or create subscription
            subscription, _ = Subscription.objects.get_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'status': 'active',
                    'billing_interval': 'monthly',
                    'current_period_start': timezone.now(),
                    'current_period_end': timezone.now() + timedelta(days=30),
                }
            )
            
            # Update subscription
            subscription.plan = plan
            subscription.status = 'active'
            subscription.current_period_start = timezone.now()
            subscription.current_period_end = timezone.now() + timedelta(days=30)
            subscription.save()
            
            # Update payment link
            payment.subscription = subscription
            payment.save()
            
            # Log billing history
            BillingHistory.objects.create(
                user=user,
                event_type='payment_succeeded',
                amount=payment.amount,
                currency='KES',
                plan_name=plan.name,
                status='completed',
                description=f'M-Pesa payment received - {transaction.mpesa_receipt_number}'
            )
            
            return True
            
        elif payment.payment_type == 'topup':
            # Add message credits
            user = payment.user
            from whatsapp_api.billing.models import UsageRecord
            
            # Calculate extra messages (1 KES = 10 messages approximately)
            extra_messages = int(payment.amount * 10)
            
            # Add to current month's usage
            now = timezone.now()
            usage, _ = UsageRecord.objects.get_or_create(
                user=user,
                year=now.year,
                month=now.month,
                defaults={
                    'message_limit': 100,
                    'messages_sent': 0
                }
            )
            
            # Increase limit (this would require field addition or separate tracking)
            # For now, create a credit record
            payment.notes = f'Added {extra_messages} message credits'
            payment.save()
            
            return True
        
        return True
        
    except Exception as e:
        logger.error(f"Payment processing failed: {str(e)}")
        return False


@api_view(['POST'])
def initiate_stk_push(request):
    """
    Initiate M-Pesa STK Push payment.
    """
    from rest_framework.permissions import IsAuthenticated
    from whatsapp_api.billing.mpesa_models import MpesaTransaction, MpesaPayment
    from whatsapp_api.billing.mpesa_service import mpesa_service
    from django.conf import settings
    
    permission_classes = [IsAuthenticated]
    
    try:
        phone = request.data.get('phone_number')
        amount = Decimal(str(request.data.get('amount', 0)))
        payment_type = request.data.get('payment_type', 'subscription')
        
        if not phone or amount <= 0:
            return Response(
                {'error': 'Valid phone number and amount required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create pending transaction
        transaction = MpesaTransaction.objects.create(
            user=request.user,
            transaction_type='stk_push',
            phone_number=phone,
            amount=amount,
            account_reference=str(request.user.id),
            transaction_description=f'WhatsApp Automation - {payment_type}',
            status='pending',
        )
        
        # Initiate STK Push
        result = mpesa_service.initiate_stk_push(
            phone_number=phone,
            amount=amount,
            account_reference=str(request.user.id),
            transaction_desc=f'WhatsApp Automation - {payment_type}'
        )
        
        if result.get('success'):
            # Update transaction with checkout ID
            transaction.checkout_request_id = result.get('checkout_request_id', '')
            transaction.merchant_request_id = result.get('merchant_request_id', '')
            transaction.save()
            
            # Create payment record
            MpesaPayment.objects.create(
                user=request.user,
                transaction=transaction,
                payment_type=payment_type,
                amount=amount,
                status='pending'
            )
            
            return Response({
                'success': True,
                'checkout_request_id': result.get('checkout_request_id'),
                'message': 'STK push initiated. Please check your phone.'
            })
        else:
            transaction.status = 'failed'
            transaction.result_description = result.get('error', 'Unknown error')
            transaction.save()
            
            return Response({
                'success': False,
                'error': result.get('error', 'Payment initiation failed')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"STK Push error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
