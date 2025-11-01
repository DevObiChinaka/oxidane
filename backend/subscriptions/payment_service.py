"""
Payment Gateway Integration Service
Handles Paystack and Stripe payment processing
"""

import requests
import hashlib
import hmac
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PaystackService:
    """
    Paystack Payment Gateway Integration
    Primary payment processor for Nigerian market
    """
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        
        if not self.secret_key:
            logger.warning("Paystack secret key not configured")
    
    def initialize_payment(self, email, amount, reference, callback_url=None, metadata=None):
        """
        Initialize a Paystack payment transaction
        
        Args:
            email: Customer email
            amount: Amount in kobo (NGN) or cents (USD)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional data to attach to transaction
            
        Returns:
            dict: Response with authorization_url and access_code
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo/cents
            "reference": reference,
            "currency": "NGN",  # Default to Nigerian Naira
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
            
        if metadata:
            payload["metadata"] = metadata
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status'):
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': data['data']['reference'],
                }
            else:
                logger.error(f"Paystack initialization failed: {data.get('message')}")
                return {
                    'success': False,
                    'error': data.get('message', 'Payment initialization failed')
                }
                
        except requests.RequestException as e:
            logger.error(f"Paystack API error: {str(e)}")
            return {
                'success': False,
                'error': 'Payment service unavailable. Please try again later.'
            }
    
    def verify_payment(self, reference):
        """
        Verify a payment transaction
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            dict: Payment verification details
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status'):
                transaction = data['data']
                
                return {
                    'success': True,
                    'verified': transaction['status'] == 'success',
                    'amount': Decimal(transaction['amount']) / 100,  # Convert from kobo to naira
                    'currency': transaction['currency'],
                    'reference': transaction['reference'],
                    'customer_email': transaction['customer']['email'],
                    'paid_at': transaction.get('paid_at'),
                    'metadata': transaction.get('metadata', {}),
                    'raw_response': transaction,
                }
            else:
                return {
                    'success': False,
                    'verified': False,
                    'error': data.get('message', 'Verification failed')
                }
                
        except requests.RequestException as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': 'Unable to verify payment'
            }
    
    def verify_webhook_signature(self, request_body, signature):
        """
        Verify Paystack webhook signature for security
        
        Args:
            request_body: Raw request body bytes
            signature: X-Paystack-Signature header value
            
        Returns:
            bool: True if signature is valid
        """
        if not self.secret_key:
            return False
            
        computed_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            request_body,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)


class StripeService:
    """
    Stripe Payment Gateway Integration
    Backup payment processor for international payments
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.publishable_key = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        
        if not self.api_key:
            logger.warning("Stripe API key not configured")
    
    def initialize_payment(self, email, amount, currency='USD', metadata=None):
        """
        Initialize Stripe payment (placeholder for future implementation)
        """
        # TODO: Implement Stripe payment initialization
        return {
            'success': False,
            'error': 'Stripe integration coming soon'
        }
    
    def verify_payment(self, payment_intent_id):
        """
        Verify Stripe payment (placeholder for future implementation)
        """
        # TODO: Implement Stripe payment verification
        return {
            'success': False,
            'error': 'Stripe integration coming soon'
        }


class PaymentService:
    """
    Unified payment service that handles multiple payment gateways
    """
    
    def __init__(self, gateway='paystack'):
        self.gateway = gateway
        
        if gateway == 'paystack':
            self.provider = PaystackService()
        elif gateway == 'stripe':
            self.provider = StripeService()
        else:
            raise ValueError(f"Unsupported payment gateway: {gateway}")
    
    def initialize_payment(self, **kwargs):
        """Initialize payment with configured gateway"""
        return self.provider.initialize_payment(**kwargs)
    
    def verify_payment(self, reference):
        """Verify payment with configured gateway"""
        return self.provider.verify_payment(reference)
    
    def verify_webhook_signature(self, request_body, signature):
        """Verify webhook signature"""
        if hasattr(self.provider, 'verify_webhook_signature'):
            return self.provider.verify_webhook_signature(request_body, signature)
        return False
