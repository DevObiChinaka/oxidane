"""
Tests for payment method tokenization and auto-renewal functionality
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from subscriptions.models import (
    BillingProfile,
    PaymentMethod,
    Subscription,
    SubscriptionPlan,
    Feature
)

User = get_user_model()


class PaymentMethodTokenizationTestCase(TestCase):
    """Test payment method saving and tokenization"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # Billing profile should be auto-created by signal
        self.billing_profile = BillingProfile.objects.get(user=self.user)
        
        # Create feature and plan
        self.feature = Feature.objects.create(
            key='premium_signals',
            name='Premium Signals',
            description='Access to premium trading signals'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly Signals',
            slug='monthly-signals',
            description='Monthly subscription with trial',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            trial_days=7,
            is_active=True
        )
        self.plan.features.add(self.feature)
    
    @patch('subscriptions.views.payment_method_views.PaystackService')
    def test_save_payment_method_success(self, mock_paystack_class):
        """Test successfully saving payment method from Paystack transaction"""
        # Mock Paystack service
        mock_service = MagicMock()
        mock_paystack_class.return_value = mock_service
        
        # Mock verify_payment response
        mock_service.verify_payment.return_value = {
            'success': True,
            'data': {
                'amount': 3000,
                'currency': 'NGN',
                'transaction_date': '2025-11-12T10:30:00',
                'reference': 'ref_test123',
                'customer': {
                    'email': 'test@example.com'
                },
                'authorization': {
                    'authorization_code': 'AUTH_test123',
                    'bin': '408408',
                    'last4': '4081',
                    'exp_month': '12',
                    'exp_year': '2030',
                    'channel': 'card',
                    'card_type': 'visa ',
                    'bank': 'TEST BANK',
                    'country_code': 'NG',
                    'brand': 'visa',
                    'reusable': True,
                    'signature': 'SIG_test'
                }
            }
        }
        
        # Mock extract_authorization
        mock_service.extract_authorization_from_verification.return_value = {
            'authorization_code': 'AUTH_test123',
            'card_type': 'visa',
            'last4': '4081',
            'exp_month': '12',
            'exp_year': '2030',
            'bank': 'TEST BANK',
            'brand': 'visa'
        }
        
        # Make request
        response = self.client.post('/api/payment-methods/save/', {
            'reference': 'ref_test123'
        })
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Payment method saved successfully')
        self.assertTrue(response.data['is_default'])
        
        # Verify payment method created
        payment_method = PaymentMethod.objects.get(billing_profile=self.billing_profile)
        self.assertEqual(payment_method.gateway_authorization_code, 'AUTH_test123')
        self.assertEqual(payment_method.card_last4, '4081')
        self.assertEqual(payment_method.card_brand, 'visa')
        self.assertEqual(payment_method.card_exp_month, '12')
        self.assertEqual(payment_method.card_exp_year, '2030')
        self.assertTrue(payment_method.is_default)
        self.assertTrue(payment_method.is_active)
        
        # Verify service calls
        mock_service.verify_payment.assert_called_once_with('ref_test123')
        mock_service.extract_authorization_from_verification.assert_called_once()
    
    @patch('subscriptions.views.payment_method_views.PaystackService')
    def test_save_second_payment_method_not_default(self, mock_paystack_class):
        """Test second payment method is not auto-set as default"""
        # Create first payment method
        PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_first',
            card_last4='1234',
            card_brand='mastercard',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        # Mock Paystack service
        mock_service = MagicMock()
        mock_paystack_class.return_value = mock_service
        
        mock_service.verify_payment.return_value = {
            'success': True,
            'data': {
                'amount': 3000,
                'currency': 'NGN',
                'transaction_date': '2025-11-12T10:30:00',
                'reference': 'ref_second',
                'customer': {'email': 'test@example.com'},
                'authorization': {
                    'authorization_code': 'AUTH_second',
                    'bin': '408408',
                    'last4': '4081',
                    'exp_month': '12',
                    'exp_year': '2030',
                    'channel': 'card',
                    'card_type': 'visa',
                    'bank': 'TEST BANK',
                    'country_code': 'NG',
                    'brand': 'visa',
                    'reusable': True
                }
            }
        }
        
        mock_service.extract_authorization_from_verification.return_value = {
            'authorization_code': 'AUTH_second',
            'card_type': 'visa',
            'last4': '4081',
            'exp_month': '12',
            'exp_year': '2030',
            'bank': 'TEST BANK',
            'brand': 'visa'
        }
        
        # Make request
        response = self.client.post('/api/payment-methods/save/', {
            'reference': 'ref_second'
        })
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_default'])
        
        # Verify second payment method not default
        second_method = PaymentMethod.objects.get(
            billing_profile=self.billing_profile,
            gateway_authorization_code='AUTH_second'
        )
        self.assertFalse(second_method.is_default)
        
        # Verify first method still default
        first_method = PaymentMethod.objects.get(
            billing_profile=self.billing_profile,
            gateway_authorization_code='AUTH_first'
        )
        self.assertTrue(first_method.is_default)
    
    @patch('subscriptions.views.payment_method_views.PaystackService')
    def test_save_payment_method_failed_verification(self, mock_paystack_class):
        """Test failed payment verification"""
        # Mock Paystack service
        mock_service = MagicMock()
        mock_paystack_class.return_value = mock_service
        
        mock_service.verify_payment.return_value = {
            'success': False,
            'message': 'Transaction not found'
        }
        
        # Make request
        response = self.client.post('/api/payment-methods/save/', {
            'reference': 'ref_invalid'
        })
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Payment verification failed', response.data['error'])
        
        # Verify no payment method created
        self.assertFalse(PaymentMethod.objects.filter(billing_profile=self.billing_profile).exists())
    
    @patch('subscriptions.views.payment_method_views.PaystackService')
    def test_save_payment_method_missing_authorization(self, mock_paystack_class):
        """Test payment verification returns no authorization code"""
        # Mock Paystack service
        mock_service = MagicMock()
        mock_paystack_class.return_value = mock_service
        
        mock_service.verify_payment.return_value = {
            'success': True,
            'data': {
                'amount': 3000,
                'currency': 'NGN',
                'reference': 'ref_no_auth',
                'customer': {'email': 'test@example.com'}
                # Missing authorization object
            }
        }
        
        mock_service.extract_authorization_from_verification.return_value = None
        
        # Make request
        response = self.client.post('/api/payment-methods/save/', {
            'reference': 'ref_no_auth'
        })
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('authorization code', response.data['error'].lower())
        
        # Verify no payment method created
        self.assertFalse(PaymentMethod.objects.filter(billing_profile=self.billing_profile).exists())
    
    def test_save_payment_method_no_billing_profile(self):
        """Test saving payment method without billing profile"""
        # Delete billing profile
        self.billing_profile.delete()
        
        # Make request
        response = self.client.post('/api/payment-methods/save/', {
            'reference': 'ref_test123'
        })
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('billing profile', response.data['error'].lower())
    
    def test_save_payment_method_unauthenticated(self):
        """Test saving payment method without authentication"""
        # Logout
        self.client.force_authenticate(user=None)
        
        # Make request
        response = self.client.post('/api/payment-methods/save/', {
            'reference': 'ref_test123'
        })
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_payment_methods(self):
        """Test listing user's payment methods"""
        # Create payment methods
        PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_1',
            card_last4='1234',
            card_brand='visa',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_2',
            card_last4='5678',
            card_brand='mastercard',
            card_exp_month='12',
            card_exp_year='2029',
            is_default=False,
            is_active=True
        )
        
        # Create inactive payment method (should not appear)
        PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_inactive',
            card_last4='9999',
            card_brand='visa',
            card_exp_month='01',
            card_exp_year='2026',
            is_default=False,
            is_active=False
        )
        
        # Make request
        response = self.client.get('/api/payment-methods/')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active methods
        
        # Verify data structure
        default_method = next(m for m in response.data if m['is_default'])
        self.assertEqual(default_method['card_last4'], '1234')
        self.assertEqual(default_method['card_brand'], 'visa')
        self.assertIn('id', default_method)
        self.assertNotIn('gateway_authorization_code', default_method)  # Security
    
    def test_set_default_payment_method(self):
        """Test setting default payment method"""
        # Create payment methods
        method1 = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_1',
            card_last4='1234',
            card_brand='visa',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        method2 = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_2',
            card_last4='5678',
            card_brand='mastercard',
            card_exp_month='12',
            card_exp_year='2029',
            is_default=False,
            is_active=True
        )
        
        # Make request to set method2 as default
        response = self.client.patch(f'/api/payment-methods/{method2.id}/set-default/')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Default payment method updated successfully')
        
        # Verify method2 is now default
        method2.refresh_from_db()
        self.assertTrue(method2.is_default)
        
        # Verify method1 is no longer default
        method1.refresh_from_db()
        self.assertFalse(method1.is_default)
    
    def test_set_default_inactive_payment_method(self):
        """Test setting inactive payment method as default"""
        # Create inactive payment method
        inactive_method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_inactive',
            card_last4='1234',
            card_brand='visa',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=False,
            is_active=False
        )
        
        # Make request
        response = self.client.patch(f'/api/payment-methods/{inactive_method.id}/set-default/')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inactive', response.data['error'].lower())
    
    def test_delete_payment_method(self):
        """Test deleting payment method"""
        # Create payment method
        method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_1',
            card_last4='1234',
            card_brand='visa',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        # Make request
        response = self.client.delete(f'/api/payment-methods/{method.id}/')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Payment method deleted successfully')
        
        # Verify method deactivated (not deleted)
        method.refresh_from_db()
        self.assertFalse(method.is_active)
    
    def test_delete_payment_method_disables_auto_renewal(self):
        """Test deleting payment method disables auto-renewal on subscriptions"""
        # Create payment method
        method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_1',
            card_last4='1234',
            card_brand='visa',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        # Create subscription with auto-renewal
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.plan,
            status='active',
            auto_renew=True,
            payment_method=method,
            amount_paid=Decimal('30.00'),
            currency='USD'
        )
        
        # Make request to delete payment method
        response = self.client.delete(f'/api/payment-methods/{method.id}/')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify auto-renewal disabled
        subscription.refresh_from_db()
        self.assertFalse(subscription.auto_renew)
        self.assertIsNone(subscription.payment_method)
    
    def test_delete_other_user_payment_method(self):
        """Test user cannot delete another user's payment method"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_billing = BillingProfile.objects.get(user=other_user)
        
        # Create payment method for other user
        other_method = PaymentMethod.objects.create(
            billing_profile=other_billing,
            payment_type='card',
            gateway_authorization_code='AUTH_other',
            card_last4='9999',
            card_brand='visa',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        # Try to delete other user's method
        response = self.client.delete(f'/api/payment-methods/{other_method.id}/')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify method still active
        other_method.refresh_from_db()
        self.assertTrue(other_method.is_active)


class AuthorizationCodeExtractionTestCase(TestCase):
    """Test authorization code extraction from Paystack response"""
    
    @patch('subscriptions.payment_service.PaymentConfiguration')
    def test_extract_authorization_success(self, mock_config):
        """Test successful authorization code extraction"""
        from subscriptions.payment_service import PaystackService
        
        # Mock configuration
        mock_config.objects.filter.return_value.first.return_value = MagicMock(
            paystack_secret_key='sk_test_123'
        )
        
        service = PaystackService()
        
        # Mock verification data
        verification_data = {
            'data': {
                'authorization': {
                    'authorization_code': 'AUTH_test123',
                    'bin': '408408',
                    'last4': '4081',
                    'exp_month': '12',
                    'exp_year': '2030',
                    'channel': 'card',
                    'card_type': 'visa ',
                    'bank': 'TEST BANK',
                    'country_code': 'NG',
                    'brand': 'visa',
                    'reusable': True,
                    'signature': 'SIG_test'
                }
            }
        }
        
        # Extract authorization
        result = service.extract_authorization_from_verification(verification_data)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['authorization_code'], 'AUTH_test123')
        self.assertEqual(result['card_type'], 'visa')
        self.assertEqual(result['last4'], '4081')
        self.assertEqual(result['exp_month'], '12')
        self.assertEqual(result['exp_year'], '2030')
        self.assertEqual(result['bank'], 'TEST BANK')
        self.assertEqual(result['brand'], 'visa')
    
    @patch('subscriptions.payment_service.PaymentConfiguration')
    def test_extract_authorization_not_reusable(self, mock_config):
        """Test authorization marked as not reusable"""
        from subscriptions.payment_service import PaystackService
        
        mock_config.objects.filter.return_value.first.return_value = MagicMock(
            paystack_secret_key='sk_test_123'
        )
        
        service = PaystackService()
        
        verification_data = {
            'data': {
                'authorization': {
                    'authorization_code': 'AUTH_test123',
                    'reusable': False  # Not reusable
                }
            }
        }
        
        # Extract authorization
        result = service.extract_authorization_from_verification(verification_data)
        
        # Should return None for non-reusable
        self.assertIsNone(result)
    
    @patch('subscriptions.payment_service.PaymentConfiguration')
    def test_extract_authorization_missing_data(self, mock_config):
        """Test extraction with missing authorization data"""
        from subscriptions.payment_service import PaystackService
        
        mock_config.objects.filter.return_value.first.return_value = MagicMock(
            paystack_secret_key='sk_test_123'
        )
        
        service = PaystackService()
        
        # No authorization in data
        verification_data = {
            'data': {
                'amount': 3000,
                'reference': 'ref_test'
            }
        }
        
        result = service.extract_authorization_from_verification(verification_data)
        self.assertIsNone(result)
