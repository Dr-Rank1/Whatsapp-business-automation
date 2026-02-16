"""
M-Pesa (Daraja API) Integration for Kenyan Market
Supports STK Push, C2B, B2C, and transaction verification
"""
import base64
import hashlib
import json
import logging
import requests
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MpesaService:
    """
    Safaricom Daraja API integration for M-Pesa payments.
    """
    
    # Environment modes
    SANDBOX = 'sandbox'
    PRODUCTION = 'production'
    
    # Endpoints
    ENDPOINTS = {
        'sandbox': {
            'oauth': 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            'stk_push': 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            'stk_query': 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query',
            'c2b_register': 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl',
            'c2b_simulate': 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate',
            'b2c': 'https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest',
            'transaction_status': 'https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query',
        },
        'production': {
            'oauth': 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            'stk_push': 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            'stk_query': 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query',
            'c2b_register': 'https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl',
            'b2c': 'https://api.safaricom.co.ke/mpesa/b2c/v1/paymentrequest',
            'transaction_status': 'https://api.safaricom.co.ke/mpesa/transactionstatus/v1/query',
        }
    }
    
    def __init__(self, environment: str = None):
        self.environment = environment or getattr(settings, 'MPESA_ENVIRONMENT', self.SANDBOX)
        self.environment_urls = self.ENDPOINTS[self.environment]
        
        # Credentials from settings
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_short_code = getattr(settings, 'MPESA_BUSINESS_SHORT_CODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.initiator_name = getattr(settings, 'MPESA_INITIATOR_NAME', '')
        self.security_credential = getattr(settings, 'MPESA_SECURITY_CREDENTIAL', '')
        
        self._access_token = None
        self._token_expiry = None
    
    def _get_access_token(self) -> str:
        """Get OAuth access token."""
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token
        
        try:
            response = requests.get(
                self.environment_urls['oauth'],
                auth=(self.consumer_key, self.consumer_secret)
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get('access_token')
                # Token expires in 1 hour (3600 seconds)
                self._token_expiry = datetime.now().timestamp() + 3500
                return self._access_token
            else:
                logger.error(f"M-Pesa OAuth failed: {response.text}")
                raise Exception("Failed to get M-Pesa access token")
                
        except Exception as e:
            logger.error(f"M-Pesa OAuth error: {str(e)}")
            raise
    
    def _generate_password(self) -> str:
        """Generate M-Pesa password (base64 of shortcode + passkey + timestamp)."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_short_code}{self.passkey}{timestamp}"
        return base64.b64encode(password_string.encode()).decode()
    
    def initiate_stk_push(
        self,
        phone_number: str,
        amount: Decimal,
        account_reference: str,
        transaction_desc: str = 'Payment'
    ) -> dict:
        """
        Initiate STK Push (Lipa Na M-Pesa Online).
        
        Args:
            phone_number: Customer phone (e.g., 254712345678)
            amount: Amount in KES
            account_reference: Your internal reference
            transaction_desc: Transaction description
            
        Returns:
            dict with checkout_request_id and response_code
        """
        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        access_token = self._get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': self._generate_password(),
            'Timestamp': timestamp,
            'TransactionType': 'CustomerBuyGoodsOnline',
            'Amount': str(int(amount)),  # Must be integer
            'PartyA': phone_number,
            'PartyB': self.business_short_code,
            'PhoneNumber': phone_number,
            'CallBackURL': getattr(settings, 'MPESA_CALLBACK_URL', ''),
            'AccountReference': str(account_reference),
            'TransactionDesc': transaction_desc
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.environment_urls['stk_push'],
                json=payload,
                headers=headers
            )
            
            result = response.json()
            
            logger.info(f"STK Push response: {result}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'response_code': result.get('ResponseCode'),
                    'response_message': result.get('ResponseDescription'),
                    'merchant_request_id': result.get('MerchantRequestID')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errorMessage', 'STK Push failed'),
                    'response_code': result.get('ResponseCode')
                }
                
        except Exception as e:
            logger.error(f"STK Push error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_stk_status(self, checkout_request_id: str) -> dict:
        """Query STK Push transaction status."""
        access_token = self._get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': self._generate_password(),
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.environment_urls['stk_query'],
                json=payload,
                headers=headers
            )
            
            result = response.json()
            
            return {
                'success': True,
                'status': result.get('ResponseCode'),
                'result_code': result.get('ResultCode'),
                'result_desc': result.get('ResultDesc'),
                'amount': result.get('Amount'),
                'mpesa_receipt': result.get('MpesaReceiptNumber'),
                'phone': result.get('PhoneNumber'),
                'transaction_date': result.get('TransactionDate')
            }
            
        except Exception as e:
            logger.error(f"STK Query error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_c2b_urls(self, confirmation_url: str, validation_url: str) -> dict:
        """Register C2B (Customer to Business) URLs."""
        access_token = self._get_access_token()
        
        payload = {
            'ShortCode': self.business_short_code,
            'ResponseType': 'Completed',
            'ConfirmationURL': confirmation_url,
            'ValidationURL': validation_url
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.environment_urls['c2b_register'],
                json=payload,
                headers=headers
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"C2B Register error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_callback(self, raw_data: dict) -> dict:
        """
        Process M-Pesa webhook callback.
        
        Expected callback structure:
        {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "...",
                    "CheckoutRequestID": "...",
                    "ResultCode": 0,  # 0 = success
                    "ResultDesc": "...",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": "10"},
                            {"Name": "MpesaReceiptNumber", "Value": "..."},
                            {"Name": "PhoneNumber", "Value": "254..."}
                        ]
                    }
                }
            }
        }
        """
        try:
            stk_callback = raw_data.get('Body', {}).get('stkCallback', {})
            
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            checkout_id = stk_callback.get('CheckoutRequestID')
            merchant_id = stk_callback.get('MerchantRequestID')
            
            # Extract metadata
            metadata = {}
            for item in stk_callback.get('CallbackMetadata', {}).get('Item', []):
                metadata[item['Name']] = item.get('Value')
            
            return {
                'success': result_code == 0,
                'result_code': result_code,
                'result_desc': result_desc,
                'checkout_request_id': checkout_id,
                'merchant_request_id': merchant_id,
                'amount': metadata.get('Amount'),
                'receipt_number': metadata.get('MpesaReceiptNumber'),
                'phone': metadata.get('PhoneNumber'),
                'transaction_date': metadata.get('TransactionDate'),
                'raw': raw_data
            }
            
        except Exception as e:
            logger.error(f"Callback processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'raw': raw_data
            }


# Singleton instance
mpesa_service = MpesaService()
