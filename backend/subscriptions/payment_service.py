"""
Payment Gateway Integration Service
Handles Paystack and Stripe payment processing

Updated: November 10, 2025
- Now reads from PaymentConfiguration model instead of settings
- Added create_customer() method
- Enhanced error handling
- Added JSON serialization helpers for Decimal types
"""

import requests
import hashlib
import hmac
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)


def make_json_serializable(obj):
    """
    Convert objects to JSON-serializable format.
    Handles Decimal, datetime, UUID, and nested structures.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    elif hasattr(obj, '__str__'):  # UUID and other objects with string representation
        return str(obj)
    return obj


class PaystackService:
    """
    Paystack Payment Gateway Integration
    Primary payment processor for Nigerian market
    
    Reads configuration from PaymentConfiguration singleton model.
    """
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        """Initialize service with configuration from PaymentConfiguration model"""
        from .models import PaymentConfiguration
        
        try:
            config = PaymentConfiguration.get_instance()
            
            # Decrypt secret key if it's encrypted (starts with 'gAAAAA')
            if config.paystack_secret_key and config.paystack_secret_key.startswith('gAAAAA'):
                self.secret_key = config.decrypt_field('paystack_secret_key')
            else:
                self.secret_key = config.paystack_secret_key
                
            self.public_key = config.paystack_public_key
            self.is_enabled = config.paystack_enabled
            self.is_test_mode = config.is_test_mode
            
            if not self.secret_key:
                logger.warning("Paystack secret key not configured in PaymentConfiguration")
            
            if not self.is_enabled:
                logger.warning("Paystack is disabled in PaymentConfiguration")
                
        except Exception as e:
            logger.error(f"Failed to load PaymentConfiguration: {str(e)}")
            self.secret_key = ''
            self.public_key = ''
            self.is_enabled = False
            self.is_test_mode = True
    
    def initialize_payment(self, email, amount, reference, callback_url=None, metadata=None, currency='NGN'):
        """
        Initialize a Paystack payment transaction
        
        Args:
            email: Customer email
            amount: Amount in base currency (e.g., 50.00 for ₦50 or $50)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional data to attach to transaction
            currency: Currency code (NGN, USD, GHS, ZAR, KES)
            
        Returns:
            dict: Response with authorization_url and access_code
        """
        if not self.is_enabled:
            return {
                'success': False,
                'error': 'Paystack payment gateway is currently disabled'
            }
        
        if not self.secret_key:
            return {
                'success': False,
                'error': 'Paystack is not configured. Please contact support.'
            }
        
        url = f"{self.BASE_URL}/transaction/initialize"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo/cents
            "reference": reference,
            "currency": currency,
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
                logger.info(f"Paystack payment initialized: {reference}")
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
                
                result = {
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
                
                # Convert all Decimal and non-serializable objects to JSON-safe types
                return make_json_serializable(result)
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
            logger.warning("Cannot verify webhook signature: Paystack secret key not configured")
            return False
        
        # Handle both bytes and string request_body
        if isinstance(request_body, str):
            request_body = request_body.encode('utf-8')
            
        computed_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            request_body,
            hashlib.sha512
        ).hexdigest()
        
        is_valid = hmac.compare_digest(computed_signature, signature)
        
        if not is_valid:
            logger.warning(f"Invalid Paystack webhook signature")
        
        return is_valid
    
    def create_customer(self, email, first_name='', last_name='', phone=''):
        """
        Create a Paystack customer
        
        Args:
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            phone: Customer phone number
            
        Returns:
            dict: Customer details with customer_code
        """
        if not self.is_enabled or not self.secret_key:
            return {
                'success': False,
                'error': 'Paystack is not configured'
            }
        
        url = f"{self.BASE_URL}/customer"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "email": email,
        }
        
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if phone:
            payload["phone"] = phone
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status'):
                customer = data['data']
                logger.info(f"Paystack customer created: {email}")
                return {
                    'success': True,
                    'customer_code': customer['customer_code'],
                    'customer_id': customer['id'],
                    'email': customer['email'],
                }
            else:
                logger.error(f"Paystack customer creation failed: {data.get('message')}")
                return {
                    'success': False,
                    'error': data.get('message', 'Customer creation failed')
                }
                
        except requests.RequestException as e:
            logger.error(f"Paystack customer creation error: {str(e)}")
            return {
                'success': False,
                'error': 'Unable to create customer'
            }
    
    def charge_authorization(self, authorization_code, email, amount, currency='NGN', metadata=None):
        """
        Charge a previously authorized card using authorization code
        Used for recurring payments and trial conversions
        
        Args:
            authorization_code: Authorization code from previous successful transaction
            email: Customer email address
            amount: Amount in base currency (e.g., 30.00 for ₦30 or $30)
            currency: Currency code (NGN, USD, etc.)
            metadata: Additional data to attach to transaction
            
        Returns:
            dict: Charge result with success status, reference, and details
        """
        if not self.is_enabled or not self.secret_key:
            return {
                'success': False,
                'error': 'Paystack is not configured'
            }
        
        url = f"{self.BASE_URL}/transaction/charge_authorization"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        # Convert amount to kobo/cents
        amount_in_kobo = int(Decimal(str(amount)) * 100)
        
        payload = {
            "authorization_code": authorization_code,
            "email": email,
            "amount": amount_in_kobo,
            "currency": currency,
        }
        
        if metadata:
            payload["metadata"] = make_json_serializable(metadata)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Parse response before raising for status to get error details
            data = response.json()
            
            if response.status_code != 200:
                error_message = data.get('message', 'Unknown error')
                logger.error(f"Paystack charge authorization failed (HTTP {response.status_code}): {error_message}")
                logger.error(f"Payload sent: {payload}")
                return {
                    'success': False,
                    'error': error_message,
                    'message': error_message
                }
            
            if data.get('status'):
                transaction = data['data']
                
                result = {
                    'success': transaction['status'] == 'success',
                    'reference': transaction['reference'],
                    'amount': Decimal(transaction['amount']) / 100,
                    'currency': transaction['currency'],
                    'status': transaction['status'],
                    'paid_at': transaction.get('paid_at'),
                    'metadata': transaction.get('metadata', {}),
                    'message': data.get('message', 'Charge successful'),
                    'raw_response': transaction,
                }
                
                if result['success']:
                    logger.info(f"Successfully charged authorization {authorization_code[:10]}... for {email}: {currency} {amount}")
                else:
                    logger.warning(f"Charge failed for {email}: {result['message']}")
                
                return make_json_serializable(result)
            else:
                logger.error(f"Paystack charge authorization failed: {data.get('message')}")
                return {
                    'success': False,
                    'error': data.get('message', 'Charge failed'),
                    'message': data.get('message', 'Charge failed')
                }
                
        except requests.RequestException as e:
            logger.error(f"Paystack charge authorization error: {str(e)}")
            return {
                'success': False,
                'error': 'Unable to process charge',
                'message': str(e)
            }
    
    def extract_authorization_from_verification(self, verification_data):
        """
        Extract authorization details from payment verification response
        Used to save payment method after successful transaction
        
        Args:
            verification_data: Response from verify_payment()
            
        Returns:
            dict: Authorization details for storing payment method or None
        """
        if not verification_data.get('success') or not verification_data.get('verified'):
            return None
        
        raw_response = verification_data.get('raw_response', {})
        authorization = raw_response.get('authorization')
        
        if not authorization:
            logger.warning("No authorization data in verification response")
            return None
        
        # Check if authorization is reusable
        if not authorization.get('reusable'):
            logger.info("Authorization is not reusable, skipping payment method save")
            return None
        
        return {
            'authorization_code': authorization['authorization_code'],
            'card_type': authorization['card_type'],
            'last4': authorization['last4'],
            'exp_month': authorization['exp_month'],
            'exp_year': authorization['exp_year'],
            'bin': authorization['bin'],
            'bank': authorization.get('bank'),
            'brand': authorization.get('brand', authorization['card_type']),
            'country_code': authorization.get('country_code'),
            'signature': authorization.get('signature'),
            'reusable': authorization['reusable'],
        }


class StripeService:
    """
    Stripe Payment Gateway Integration
    International payment processor
    
    Reads configuration from PaymentConfiguration singleton model.
    """
    
    def __init__(self):
        """Initialize service with configuration from PaymentConfiguration model"""
        from .models import PaymentConfiguration
        
        try:
            config = PaymentConfiguration.get_instance()
            
            # Decrypt secret keys if they're encrypted (start with 'gAAAAA')
            if config.stripe_secret_key and config.stripe_secret_key.startswith('gAAAAA'):
                self.secret_key = config.decrypt_field('stripe_secret_key')
            else:
                self.secret_key = config.stripe_secret_key
                
            if config.stripe_webhook_secret and config.stripe_webhook_secret.startswith('gAAAAA'):
                self.webhook_secret = config.decrypt_field('stripe_webhook_secret')
            else:
                self.webhook_secret = config.stripe_webhook_secret
                
            self.publishable_key = config.stripe_publishable_key
            self.is_enabled = config.stripe_enabled
            self.is_test_mode = config.is_test_mode
            
            if not self.secret_key:
                logger.warning("Stripe secret key not configured in PaymentConfiguration")
            
            if not self.is_enabled:
                logger.warning("Stripe is disabled in PaymentConfiguration")
                
        except Exception as e:
            logger.error(f"Failed to load PaymentConfiguration: {str(e)}")
            self.secret_key = ''
            self.publishable_key = ''
            self.webhook_secret = ''
            self.is_enabled = False
            self.is_test_mode = True
    
    def initialize_payment(self, email, amount, currency='USD', metadata=None, success_url='', cancel_url=''):
        """
        Initialize Stripe checkout session
        
        Args:
            email: Customer email
            amount: Amount in base currency (e.g., 50.00 for $50)
            currency: Currency code (USD, EUR, GBP)
            metadata: Additional data to attach
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment cancelled
            
        Returns:
            dict: Response with session_id and checkout_url
        """
        if not self.is_enabled:
            return {
                'success': False,
                'error': 'Stripe payment gateway is currently disabled'
            }
        
        if not self.secret_key:
            return {
                'success': False,
                'error': 'Stripe is not configured. Please contact support.'
            }
        
        try:
            import stripe
            stripe.api_key = self.secret_key
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': 'Subscription Payment',
                        },
                        'unit_amount': int(amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=email,
                metadata=metadata or {},
            )
            
            logger.info(f"Stripe checkout session created: {session.id}")
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url,
            }
            
        except Exception as e:
            logger.error(f"Stripe checkout session creation error: {str(e)}")
            return {
                'success': False,
                'error': f'Unable to create checkout session: {str(e)}'
            }
    
    def verify_payment(self, session_id):
        """
        Verify Stripe checkout session payment status
        
        Args:
            session_id: Stripe checkout session ID
            
        Returns:
            dict: Payment verification details
        """
        if not self.is_enabled or not self.secret_key:
            return {
                'success': False,
                'error': 'Stripe is not configured'
            }
        
        try:
            import stripe
            stripe.api_key = self.secret_key
            
            session = stripe.checkout.Session.retrieve(session_id)
            
            result = {
                'success': True,
                'verified': session.payment_status == 'paid',
                'amount': Decimal(session.amount_total) / 100,
                'currency': session.currency.upper(),
                'customer_email': session.customer_details.email if session.customer_details else '',
                'payment_intent': session.payment_intent,
                'session_id': session.id,
                'raw_response': dict(session),
            }
            
            # Convert all Decimal and non-serializable objects to JSON-safe types
            return make_json_serializable(result)
            
        except Exception as e:
            logger.error(f"Stripe verification error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': f'Unable to verify payment: {str(e)}'
            }
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw request body (string or bytes)
            signature: Stripe-Signature header value
            
        Returns:
            dict: Event object if valid, or error dict
        """
        if not self.webhook_secret:
            logger.warning("Cannot verify webhook: Stripe webhook secret not configured")
            return {
                'success': False,
                'error': 'Webhook secret not configured'
            }
        
        try:
            import stripe
            
            # Handle both bytes and string payload
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')
            
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            logger.info(f"Valid Stripe webhook received: {event['type']}")
            return {
                'success': True,
                'event': event
            }
            
        except ValueError as e:
            logger.error(f"Invalid Stripe webhook payload: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid payload'
            }
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe webhook signature: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid signature'
            }
    
    def create_customer(self, email, name='', phone='', metadata=None):
        """
        Create a Stripe customer
        
        Args:
            email: Customer email
            name: Customer full name
            phone: Customer phone number
            metadata: Additional metadata
            
        Returns:
            dict: Customer details with customer_id
        """
        if not self.is_enabled or not self.secret_key:
            return {
                'success': False,
                'error': 'Stripe is not configured'
            }
        
        try:
            import stripe
            stripe.api_key = self.secret_key
            
            customer_data = {
                'email': email,
            }
            
            if name:
                customer_data['name'] = name
            if phone:
                customer_data['phone'] = phone
            if metadata:
                customer_data['metadata'] = metadata
            
            customer = stripe.Customer.create(**customer_data)
            
            logger.info(f"Stripe customer created: {email}")
            return {
                'success': True,
                'customer_id': customer.id,
                'email': customer.email,
            }
            
        except Exception as e:
            logger.error(f"Stripe customer creation error: {str(e)}")
            return {
                'success': False,
                'error': f'Unable to create customer: {str(e)}'
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
