"""
Tests for Validate Referral API (Phase 0.5 - Task 0.5.35)

Public API endpoint for validating referral codes before applying them to subscriptions.

Endpoints tested:
- POST /api/v1/subscriptions/validate-referral/validate/

Test Coverage:
- Valid referral code validation
- Invalid referral codes (not found, inactive, expired, not started)
- Usage limits (total uses, self-referral)
- Discount calculations (percentage and fixed for both referrer and referee)
- Edge cases (zero price, 100% discount, unlimited usage)
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from subscriptions.models import ReferralCode

User = get_user_model()


@pytest.mark.django_db
class TestValidReferralValidation:
    """Test valid referral code validation scenarios"""
    
    def test_valid_percentage_referral_code(self):
        """Valid percentage referral code should return success with discount info"""
        client = APIClient()
        
        # Create referrer user
        referrer = User.objects.create_user(
            username='referrer',
            email='referrer@test.com',
            password='testpass123'
        )
        
        # Create valid referral code
        referral_code = ReferralCode.objects.create(
            code='REFTEST10',
            referrer=referrer,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('5.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True,
            description='Test referral code'
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'REFTEST10',
            'amount': 100.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['code'] == 'REFTEST10'
        assert data['referrer']['username'] == 'referrer'
        assert data['referrer']['discount_type'] == 'percentage'
        assert data['referrer']['discount_value'] == 5.0
        assert data['referrer']['discount_display'] == '5% off'
        assert data['referee']['discount_type'] == 'percentage'
        assert data['referee']['discount_value'] == 10.0
        assert data['referee']['discount_display'] == '10% off'
        assert 'discount_calculation' in data['referrer']
        assert 'discount_calculation' in data['referee']
        assert data['referee']['discount_calculation']['original_price'] == 100.0
        assert data['referee']['discount_calculation']['discount_amount'] == 10.0
        assert data['referee']['discount_calculation']['final_price'] == 90.0
        assert 'Referral code applied!' in data['message']
    
    def test_valid_fixed_referral_code(self):
        """Valid fixed amount referral code should return success"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='referrer2',
            email='referrer2@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='REF50OFF',
            referrer=referrer,
            referrer_discount_type='fixed',
            referrer_discount_value=Decimal('25.00'),
            referee_discount_type='fixed',
            referee_discount_value=Decimal('50.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'ref50off',  # Test case-insensitive
            'amount': 200.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['code'] == 'REF50OFF'
        assert data['referee']['discount_type'] == 'fixed'
        assert data['referee']['discount_value'] == 50.0
        assert data['referee']['discount_display'] == '$50.00 off'
        assert data['referee']['discount_calculation']['discount_amount'] == 50.0
        assert data['referee']['discount_calculation']['final_price'] == 150.0
    
    def test_valid_referral_without_amount(self):
        """Valid referral code without amount should return basic info"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='referrer3',
            email='referrer3@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='BASICREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('15.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'BASICREF'
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['code'] == 'BASICREF'
        assert 'discount_calculation' not in data['referee']  # No amount provided
        assert data['referee']['discount_type'] == 'percentage'
        assert data['referee']['discount_value'] == 15.0
    
    def test_referral_with_usage_stats(self):
        """Referral code response should include usage statistics"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='referrer4',
            email='referrer4@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='LIMITEDREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('20.00'),
            max_uses=100,
            current_uses=25,
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'LIMITEDREF'
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['usage']['current_uses'] == 25
        assert data['usage']['max_uses'] == 100
        assert data['usage']['remaining_uses'] == 75
    
    def test_referral_with_unlimited_usage(self):
        """Referral code with unlimited usage should show null max_uses"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='referrer5',
            email='referrer5@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='UNLIMITEDREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            max_uses=None,
            current_uses=500,
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'UNLIMITEDREF'
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['usage']['max_uses'] is None
        assert data['usage']['remaining_uses'] is None
        assert data['usage']['current_uses'] == 500
    
    def test_referral_with_validity_period(self):
        """Referral code response should include validity period"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='referrer6',
            email='referrer6@test.com',
            password='testpass123'
        )
        
        now = timezone.now()
        valid_from = now - timedelta(days=5)
        valid_until = now + timedelta(days=25)
        
        referral_code = ReferralCode.objects.create(
            code='TIMEDREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'TIMEDREF'
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert 'validity' in data
        assert data['validity']['valid_from'] is not None
        assert data['validity']['valid_until'] is not None


@pytest.mark.django_db
class TestInvalidReferralCodes:
    """Test invalid referral code scenarios"""
    
    def test_missing_code(self):
        """Missing code should return MISSING_CODE error"""
        client = APIClient()
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'amount': 100.00
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'MISSING_CODE'
        assert 'required' in data['error'].lower()
    
    def test_nonexistent_code(self):
        """Non-existent referral code should return REFERRAL_NOT_FOUND error"""
        client = APIClient()
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'NONEXISTENT'
        }, format='json')
        
        assert response.status_code == 404
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'REFERRAL_NOT_FOUND'
        assert data['code'] == 'NONEXISTENT'
        assert 'not found' in data['error'].lower()
    
    def test_inactive_code(self):
        """Inactive referral code should return REFERRAL_INACTIVE error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='inactive_referrer',
            email='inactive@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='INACTIVEREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=False
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'INACTIVEREF'
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'REFERRAL_INACTIVE'
        assert 'no longer active' in data['error'].lower()
    
    def test_expired_code(self):
        """Expired referral code should return EXPIRED error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='expired_referrer',
            email='expired@test.com',
            password='testpass123'
        )
        
        now = timezone.now()
        referral_code = ReferralCode.objects.create(
            code='EXPIREDREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            valid_from=now - timedelta(days=30),
            valid_until=now - timedelta(days=1),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'EXPIREDREF'
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'EXPIRED'
        assert 'expired' in data['error'].lower()
        assert 'expired_at' in data
    
    def test_future_code(self):
        """Future referral code should return NOT_STARTED error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='future_referrer',
            email='future@test.com',
            password='testpass123'
        )
        
        now = timezone.now()
        referral_code = ReferralCode.objects.create(
            code='FUTUREREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            valid_from=now + timedelta(days=5),
            valid_until=now + timedelta(days=35),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'FUTUREREF'
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'NOT_STARTED'
        assert 'will be valid from' in data['error'].lower()
        assert 'valid_from' in data


@pytest.mark.django_db
class TestReferralUsageLimits:
    """Test referral code usage limit scenarios"""
    
    def test_usage_limit_reached(self):
        """Referral code at max usage should return USAGE_LIMIT_REACHED error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='limit_referrer',
            email='limit@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='LIMITEDREF2',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            max_uses=10,
            current_uses=10,
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'LIMITEDREF2'
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'USAGE_LIMIT_REACHED'
        assert 'usage limit' in data['error'].lower()
        assert data['max_uses'] == 10
        assert data['current_uses'] == 10
    
    def test_usage_limit_exceeded(self):
        """Referral code exceeding max usage should return error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='exceeded_referrer',
            email='exceeded@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='EXCEEDEDREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            max_uses=5,
            current_uses=7,  # Exceeded
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'EXCEEDEDREF'
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'USAGE_LIMIT_REACHED'
    
    def test_self_referral_prevention(self):
        """User trying to use their own referral code should return SELF_REFERRAL error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='selfreferrer',
            email='self@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='MYOWNREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'MYOWNREF',
            'user_id': str(referrer.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'SELF_REFERRAL'
        assert 'cannot use your own' in data['error'].lower()
    
    def test_different_user_can_use_code(self):
        """Different user should be able to use referral code"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='referrer_diff',
            email='referrer_diff@test.com',
            password='testpass123'
        )
        
        referee = User.objects.create_user(
            username='referee_diff',
            email='referee_diff@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='DIFFUSERREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'DIFFUSERREF',
            'user_id': str(referee.id)
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True


@pytest.mark.django_db
class TestDiscountCalculations:
    """Test referral discount calculation accuracy"""
    
    def test_percentage_discount_calculation(self):
        """Percentage discounts should be calculated correctly for both parties"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='calc_referrer',
            email='calc@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='CALC20',
            referrer=referrer,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('15.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('20.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'CALC20',
            'amount': 100.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        
        # Referee gets 20% off
        assert data['referee']['discount_calculation']['original_price'] == 100.0
        assert data['referee']['discount_calculation']['discount_amount'] == 20.0
        assert data['referee']['discount_calculation']['final_price'] == 80.0
        assert data['referee']['discount_calculation']['savings_percentage'] == 20.0
        
        # Referrer gets 15% off
        assert data['referrer']['discount_calculation']['original_price'] == 100.0
        assert data['referrer']['discount_calculation']['discount_amount'] == 15.0
        assert data['referrer']['discount_calculation']['final_price'] == 85.0
        assert data['referrer']['discount_calculation']['savings_percentage'] == 15.0
    
    def test_fixed_discount_calculation(self):
        """Fixed discounts should be calculated correctly for both parties"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='fixed_referrer',
            email='fixed@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='FIXED30',
            referrer=referrer,
            referrer_discount_type='fixed',
            referrer_discount_value=Decimal('20.00'),
            referee_discount_type='fixed',
            referee_discount_value=Decimal('30.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'FIXED30',
            'amount': 150.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        
        # Referee gets $30 off
        assert data['referee']['discount_calculation']['discount_amount'] == 30.0
        assert data['referee']['discount_calculation']['final_price'] == 120.0
        
        # Referrer gets $20 off
        assert data['referrer']['discount_calculation']['discount_amount'] == 20.0
        assert data['referrer']['discount_calculation']['final_price'] == 130.0
    
    def test_mixed_discount_types(self):
        """Referrer and referee can have different discount types"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='mixed_referrer',
            email='mixed@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='MIXED',
            referrer=referrer,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='fixed',
            referee_discount_value=Decimal('25.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'MIXED',
            'amount': 200.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        
        # Referee gets $25 off (fixed)
        assert data['referee']['discount_type'] == 'fixed'
        assert data['referee']['discount_calculation']['discount_amount'] == 25.0
        assert data['referee']['discount_calculation']['final_price'] == 175.0
        
        # Referrer gets 10% off (percentage)
        assert data['referrer']['discount_type'] == 'percentage'
        assert data['referrer']['discount_calculation']['discount_amount'] == 20.0
        assert data['referrer']['discount_calculation']['final_price'] == 180.0
    
    def test_discount_doesnt_go_negative(self):
        """Discount should not make final price negative"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='negative_referrer',
            email='negative@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='HUGEDISCOUNT',
            referrer=referrer,
            referrer_discount_type='fixed',
            referrer_discount_value=Decimal('200.00'),
            referee_discount_type='fixed',
            referee_discount_value=Decimal('200.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'HUGEDISCOUNT',
            'amount': 50.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        
        # Discount capped at original price
        assert data['referee']['discount_calculation']['discount_amount'] == 50.0
        assert data['referee']['discount_calculation']['final_price'] == 0.0


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_zero_price_validation(self):
        """Referral code should handle zero price gracefully"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='zero_referrer',
            email='zero@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='ZEROREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'ZEROREF',
            'amount': 0.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['referee']['discount_calculation']['final_price'] == 0.0
    
    def test_100_percent_discount(self):
        """100% discount should work correctly"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='hundred_referrer',
            email='hundred@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='FREE100',
            referrer=referrer,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('50.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('100.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'FREE100',
            'amount': 100.00
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['referee']['discount_calculation']['discount_amount'] == 100.0
        assert data['referee']['discount_calculation']['final_price'] == 0.0
    
    def test_invalid_amount_format(self):
        """Invalid amount should return INVALID_AMOUNT error"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='invalid_referrer',
            email='invalid@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='VALIDREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'VALIDREF',
            'amount': 'invalid'
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['valid'] is False
        assert data['error_code'] == 'INVALID_AMOUNT'
    
    def test_case_insensitive_code_matching(self):
        """Referral codes should match case-insensitively"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='case_referrer',
            email='case@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='CASETEST',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        # Try with lowercase
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': 'casetest'
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['code'] == 'CASETEST'
    
    def test_whitespace_handling(self):
        """Referral code validation should handle whitespace"""
        client = APIClient()
        
        referrer = User.objects.create_user(
            username='space_referrer',
            email='space@test.com',
            password='testpass123'
        )
        
        referral_code = ReferralCode.objects.create(
            code='SPACEREF',
            referrer=referrer,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        # Try with leading/trailing spaces
        response = client.post('/api/v1/subscriptions/validate-referral/validate/', {
            'code': '  SPACEREF  '
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['code'] == 'SPACEREF'
