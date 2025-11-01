"""
Comprehensive tests for ReferralCode model.

Test Categories:
1. Model creation and validation
2. Code formatting and validation
3. Validity checks (time-based)
4. Usage limits and tracking
5. Discount calculations (referrer and referee)
6. Edge cases and constraints
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import time

from subscriptions.models import ReferralCode

User = get_user_model()


class TestReferralCodeModel(TestCase):
    """Test basic ReferralCode model creation and validation"""
    
    def setUp(self):
        """Create test users"""
        self.user1 = User.objects.create_user(
            username='referrer1',
            email='referrer1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='referrer2',
            email='referrer2@test.com',
            password='testpass123'
        )
    
    def test_create_referral_code_success(self):
        """Test creating a referral code with valid data"""
        referral = ReferralCode.objects.create(
            code='REFER2024',
            referrer=self.user1,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('15.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00')
        )
        
        self.assertEqual(referral.code, 'REFER2024')
        self.assertEqual(referral.referrer, self.user1)
        self.assertEqual(referral.referrer_discount_value, Decimal('15.00'))
        self.assertEqual(referral.referee_discount_value, Decimal('10.00'))
        self.assertTrue(referral.is_active)
        self.assertEqual(referral.current_uses, 0)
    
    def test_referral_code_auto_uppercase(self):
        """Test that referral code is automatically converted to uppercase"""
        referral = ReferralCode.objects.create(
            code='lowercase',
            referrer=self.user1
        )
        
        self.assertEqual(referral.code, 'LOWERCASE')
    
    def test_referral_code_strips_whitespace(self):
        """Test that referral code strips leading/trailing whitespace"""
        referral = ReferralCode.objects.create(
            code='  SPACED  ',
            referrer=self.user1
        )
        
        self.assertEqual(referral.code, 'SPACED')
    
    def test_referral_code_uniqueness(self):
        """Test that referral codes must be unique"""
        ReferralCode.objects.create(
            code='UNIQUE123',
            referrer=self.user1
        )
        
        # Try to create another with same code
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            ReferralCode.objects.create(
                code='UNIQUE123',
                referrer=self.user2
            )
    
    def test_referral_code_invalid_characters(self):
        """Test that referral codes with invalid characters are rejected"""
        with self.assertRaises(ValidationError) as context:
            ReferralCode.objects.create(
                code='INVALID-CODE!',  # Hyphen and ! are invalid
                referrer=self.user1
            )
        
        self.assertIn('code', str(context.exception))
    
    def test_referral_code_minimum_length(self):
        """Test that referral codes must be at least 3 characters"""
        with self.assertRaises(ValidationError) as context:
            ReferralCode.objects.create(
                code='AB',  # Too short
                referrer=self.user1
            )
        
        self.assertIn('code', str(context.exception))
    
    def test_referral_code_string_representation(self):
        """Test string representation of referral code"""
        referral = ReferralCode.objects.create(
            code='TESTCODE',
            referrer=self.user1
        )
        
        self.assertIn('TESTCODE', str(referral))
        self.assertIn(self.user1.username, str(referral))
    
    def test_referral_discount_validation_over_100_percent(self):
        """Test that percentage discounts over 100% are rejected"""
        with self.assertRaises(ValidationError) as context:
            ReferralCode.objects.create(
                code='OVER100',
                referrer=self.user1,
                referrer_discount_type='percentage',
                referrer_discount_value=Decimal('150.00')
            )
        
        self.assertIn('referrer_discount_value', str(context.exception))
    
    def test_referral_discount_validation_negative(self):
        """Test that negative discount values are rejected"""
        with self.assertRaises(ValidationError) as context:
            ReferralCode.objects.create(
                code='NEGATIVE',
                referrer=self.user1,
                referrer_discount_type='percentage',
                referrer_discount_value=Decimal('-10.00')
            )
        
        self.assertIn('referrer_discount_value', str(context.exception))
    
    def test_referee_discount_validation_over_100_percent(self):
        """Test that referee percentage discounts over 100% are rejected"""
        with self.assertRaises(ValidationError) as context:
            ReferralCode.objects.create(
                code='OVER100',
                referrer=self.user1,
                referee_discount_type='percentage',
                referee_discount_value=Decimal('150.00')
            )
        
        self.assertIn('referee_discount_value', str(context.exception))
    
    def test_referral_code_ordering(self):
        """Test that referral codes are ordered by created_at descending"""
        # Create multiple referral codes with slight delays
        ref1 = ReferralCode.objects.create(code='FIRST', referrer=self.user1)
        time.sleep(0.01)
        ref2 = ReferralCode.objects.create(code='SECOND', referrer=self.user1)
        time.sleep(0.01)
        ref3 = ReferralCode.objects.create(code='THIRD', referrer=self.user1)
        
        codes = list(ReferralCode.objects.all())
        self.assertEqual(codes[0].code, 'THIRD')
        self.assertEqual(codes[1].code, 'SECOND')
        self.assertEqual(codes[2].code, 'FIRST')


class TestReferralCodeValidity(TestCase):
    """Test referral code validity checks"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_referral_code_valid_now(self):
        """Test that a valid referral code passes validation"""
        referral = ReferralCode.objects.create(
            code='VALID',
            referrer=self.user,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        self.assertTrue(referral.is_valid())
        self.assertTrue(referral.can_be_used())
    
    def test_referral_code_not_started(self):
        """Test that a referral code not yet valid fails validation"""
        referral = ReferralCode.objects.create(
            code='FUTURE',
            referrer=self.user,
            valid_from=timezone.now() + timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        self.assertFalse(referral.is_valid())
        self.assertFalse(referral.can_be_used())
    
    def test_referral_code_expired(self):
        """Test that an expired referral code fails validation"""
        referral = ReferralCode.objects.create(
            code='EXPIRED',
            referrer=self.user,
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1)
        )
        
        self.assertFalse(referral.is_valid())
        self.assertFalse(referral.can_be_used())
    
    def test_referral_code_inactive(self):
        """Test that an inactive referral code fails validation"""
        referral = ReferralCode.objects.create(
            code='INACTIVE',
            referrer=self.user,
            is_active=False
        )
        
        self.assertFalse(referral.is_valid())
        self.assertFalse(referral.can_be_used())
    
    def test_referral_code_no_expiration(self):
        """Test that a referral code with no expiration is valid"""
        referral = ReferralCode.objects.create(
            code='NOEXPIRY',
            referrer=self.user,
            valid_until=None
        )
        
        self.assertTrue(referral.is_valid())
        self.assertTrue(referral.can_be_used())
    
    def test_referral_code_invalid_date_range(self):
        """Test that invalid date range is rejected"""
        with self.assertRaises(ValidationError) as context:
            ReferralCode.objects.create(
                code='BADRANGE',
                referrer=self.user,
                valid_from=timezone.now() + timedelta(days=30),
                valid_until=timezone.now() + timedelta(days=1)
            )
        
        self.assertIn('valid_until', str(context.exception))


class TestReferralCodeUsageLimits(TestCase):
    """Test referral code usage limits and tracking"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_referral_usage_available_unlimited(self):
        """Test that unlimited referral codes always have usage available"""
        referral = ReferralCode.objects.create(
            code='UNLIMITED',
            referrer=self.user,
            max_uses=None
        )
        
        self.assertTrue(referral.is_usage_available())
        self.assertIsNone(referral.get_remaining_uses())
    
    def test_referral_usage_available_with_limit(self):
        """Test that referral codes with usage limits work correctly"""
        referral = ReferralCode.objects.create(
            code='LIMITED',
            referrer=self.user,
            max_uses=10,
            current_uses=5
        )
        
        self.assertTrue(referral.is_usage_available())
        self.assertEqual(referral.get_remaining_uses(), 5)
    
    def test_referral_usage_exhausted(self):
        """Test that exhausted referral codes cannot be used"""
        referral = ReferralCode.objects.create(
            code='EXHAUSTED',
            referrer=self.user,
            max_uses=10,
            current_uses=10
        )
        
        self.assertFalse(referral.is_usage_available())
        self.assertEqual(referral.get_remaining_uses(), 0)
        self.assertFalse(referral.can_be_used())
    
    def test_increment_usage(self):
        """Test incrementing referral code usage"""
        referral = ReferralCode.objects.create(
            code='INCREMENT',
            referrer=self.user,
            current_uses=0
        )
        
        referral.increment_usage()
        referral.refresh_from_db()
        
        self.assertEqual(referral.current_uses, 1)
    
    def test_can_be_used_valid_with_usage(self):
        """Test that valid referral codes with usage available can be used"""
        referral = ReferralCode.objects.create(
            code='CANUSE',
            referrer=self.user,
            max_uses=10,
            current_uses=5
        )
        
        self.assertTrue(referral.can_be_used())
    
    def test_can_be_used_expired(self):
        """Test that expired referral codes cannot be used even with usage available"""
        referral = ReferralCode.objects.create(
            code='EXPIREDUSAGE',
            referrer=self.user,
            max_uses=10,
            current_uses=0,
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1)
        )
        
        self.assertFalse(referral.can_be_used())
    
    def test_can_be_used_exhausted(self):
        """Test that exhausted referral codes cannot be used even if not expired"""
        referral = ReferralCode.objects.create(
            code='EXHAUSTEDVALID',
            referrer=self.user,
            max_uses=5,
            current_uses=5,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        self.assertFalse(referral.can_be_used())
    
    def test_negative_usage_validation(self):
        """Test that negative current_uses is rejected"""
        with self.assertRaises(ValidationError):
            ReferralCode.objects.create(
                code='NEGATIVEUSES',
                referrer=self.user,
                current_uses=-1
            )


class TestReferralCodeDiscountCalculation(TestCase):
    """Test discount calculation for referrer and referee"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_referrer_percentage_discount_calculation(self):
        """Test percentage discount calculation for referrer"""
        referral = ReferralCode.objects.create(
            code='REFER20',
            referrer=self.user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('20.00')
        )
        
        result = referral.calculate_referrer_discount(Decimal('100.00'))
        
        self.assertEqual(result['original_price'], Decimal('100.00'))
        self.assertEqual(result['discount_amount'], Decimal('20.00'))
        self.assertEqual(result['final_price'], Decimal('80.00'))
        self.assertEqual(result['savings_percentage'], Decimal('20.00'))
    
    def test_referee_percentage_discount_calculation(self):
        """Test percentage discount calculation for referee"""
        referral = ReferralCode.objects.create(
            code='REFER15',
            referrer=self.user,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('15.00')
        )
        
        result = referral.calculate_referee_discount(Decimal('100.00'))
        
        self.assertEqual(result['original_price'], Decimal('100.00'))
        self.assertEqual(result['discount_amount'], Decimal('15.00'))
        self.assertEqual(result['final_price'], Decimal('85.00'))
        self.assertEqual(result['savings_percentage'], Decimal('15.00'))
    
    def test_referrer_fixed_discount_calculation(self):
        """Test fixed amount discount calculation for referrer"""
        referral = ReferralCode.objects.create(
            code='REFER25',
            referrer=self.user,
            referrer_discount_type='fixed',
            referrer_discount_value=Decimal('25.00')
        )
        
        result = referral.calculate_referrer_discount(Decimal('100.00'))
        
        self.assertEqual(result['original_price'], Decimal('100.00'))
        self.assertEqual(result['discount_amount'], Decimal('25.00'))
        self.assertEqual(result['final_price'], Decimal('75.00'))
        self.assertEqual(result['savings_percentage'], Decimal('25.00'))
    
    def test_referee_fixed_discount_calculation(self):
        """Test fixed amount discount calculation for referee"""
        referral = ReferralCode.objects.create(
            code='REFER30',
            referrer=self.user,
            referee_discount_type='fixed',
            referee_discount_value=Decimal('30.00')
        )
        
        result = referral.calculate_referee_discount(Decimal('100.00'))
        
        self.assertEqual(result['original_price'], Decimal('100.00'))
        self.assertEqual(result['discount_amount'], Decimal('30.00'))
        self.assertEqual(result['final_price'], Decimal('70.00'))
        self.assertEqual(result['savings_percentage'], Decimal('30.00'))
    
    def test_discount_cannot_be_negative(self):
        """Test that discount cannot make price negative"""
        referral = ReferralCode.objects.create(
            code='HUGE',
            referrer=self.user,
            referrer_discount_type='fixed',
            referrer_discount_value=Decimal('150.00')
        )
        
        result = referral.calculate_referrer_discount(Decimal('100.00'))
        
        # Discount capped at original price
        self.assertEqual(result['discount_amount'], Decimal('100.00'))
        self.assertEqual(result['final_price'], Decimal('0.00'))
    
    def test_100_percent_discount(self):
        """Test 100% discount for referrer"""
        referral = ReferralCode.objects.create(
            code='FREE',
            referrer=self.user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('100.00')
        )
        
        result = referral.calculate_referrer_discount(Decimal('100.00'))
        
        self.assertEqual(result['discount_amount'], Decimal('100.00'))
        self.assertEqual(result['final_price'], Decimal('0.00'))
        self.assertEqual(result['savings_percentage'], Decimal('100.00'))
    
    def test_discount_on_zero_price(self):
        """Test discount calculation on zero price"""
        referral = ReferralCode.objects.create(
            code='ZEROPRICE',
            referrer=self.user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('20.00')
        )
        
        result = referral.calculate_referrer_discount(Decimal('0.00'))
        
        self.assertEqual(result['discount_amount'], Decimal('0.00'))
        self.assertEqual(result['final_price'], Decimal('0.00'))
        self.assertEqual(result['savings_percentage'], Decimal('0.00'))
    
    def test_get_referrer_discount_display_percentage(self):
        """Test formatted display of referrer percentage discount"""
        referral = ReferralCode.objects.create(
            code='DISPLAY',
            referrer=self.user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('25.00')
        )
        
        self.assertEqual(referral.get_referrer_discount_display(), '25% off')
    
    def test_get_referrer_discount_display_fixed(self):
        """Test formatted display of referrer fixed discount"""
        referral = ReferralCode.objects.create(
            code='DISPLAY',
            referrer=self.user,
            referrer_discount_type='fixed',
            referrer_discount_value=Decimal('50.00')
        )
        
        self.assertEqual(referral.get_referrer_discount_display(), '$50.00 off')
    
    def test_get_referee_discount_display_percentage(self):
        """Test formatted display of referee percentage discount"""
        referral = ReferralCode.objects.create(
            code='DISPLAY',
            referrer=self.user,
            referee_discount_type='percentage',
            referee_discount_value=Decimal('15.00')
        )
        
        self.assertEqual(referral.get_referee_discount_display(), '15% off')


class TestReferralCodeEdgeCases(TestCase):
    """Test edge cases and special scenarios"""
    
    def setUp(self):
        """Create test users"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_referral_code_with_description(self):
        """Test referral code with description"""
        referral = ReferralCode.objects.create(
            code='DESCRIBED',
            referrer=self.user1,
            description='Special referral for friends'
        )
        
        self.assertEqual(referral.description, 'Special referral for friends')
    
    def test_referral_code_valid_characters(self):
        """Test that alphanumeric and underscore are valid"""
        referral = ReferralCode.objects.create(
            code='ABC123_XYZ',
            referrer=self.user1
        )
        
        self.assertEqual(referral.code, 'ABC123_XYZ')
    
    def test_referral_code_deletion(self):
        """Test referral code deletion"""
        referral = ReferralCode.objects.create(
            code='DELETE',
            referrer=self.user1
        )
        
        referral_id = referral.id
        referral.delete()
        
        self.assertFalse(ReferralCode.objects.filter(id=referral_id).exists())
    
    def test_user_can_have_multiple_referral_codes(self):
        """Test that a user can have multiple referral codes"""
        ref1 = ReferralCode.objects.create(
            code='USER1CODE1',
            referrer=self.user1
        )
        ref2 = ReferralCode.objects.create(
            code='USER1CODE2',
            referrer=self.user1
        )
        
        user_codes = ReferralCode.objects.filter(referrer=self.user1)
        self.assertEqual(user_codes.count(), 2)
    
    def test_referral_code_update(self):
        """Test updating referral code properties"""
        referral = ReferralCode.objects.create(
            code='UPDATE',
            referrer=self.user1,
            referrer_discount_value=Decimal('10.00')
        )
        
        referral.referrer_discount_value = Decimal('20.00')
        referral.save()
        referral.refresh_from_db()
        
        self.assertEqual(referral.referrer_discount_value, Decimal('20.00'))
    
    def test_referral_code_unicode_in_description(self):
        """Test that Unicode characters in description work"""
        referral = ReferralCode.objects.create(
            code='UNICODE',
            referrer=self.user1,
            description='Special discount 🎉 for friends!'
        )
        
        self.assertIn('🎉', referral.description)
    
    def test_referral_code_cascades_on_user_delete(self):
        """Test that referral codes are deleted when user is deleted"""
        referral = ReferralCode.objects.create(
            code='CASCADE',
            referrer=self.user2
        )
        
        referral_id = referral.id
        self.user2.delete()
        
        self.assertFalse(ReferralCode.objects.filter(id=referral_id).exists())
    
    def test_filter_active_referral_codes(self):
        """Test filtering active referral codes"""
        ReferralCode.objects.create(
            code='ACTIVE1',
            referrer=self.user1,
            is_active=True
        )
        ReferralCode.objects.create(
            code='ACTIVE2',
            referrer=self.user1,
            is_active=True
        )
        ReferralCode.objects.create(
            code='INACTIVE',
            referrer=self.user1,
            is_active=False
        )
        
        active_codes = ReferralCode.objects.filter(is_active=True)
        self.assertEqual(active_codes.count(), 2)
    
    def test_different_discounts_for_referrer_and_referee(self):
        """Test that referrer and referee can have different discounts"""
        referral = ReferralCode.objects.create(
            code='DIFFERENT',
            referrer=self.user1,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('20.00'),
            referee_discount_type='fixed',
            referee_discount_value=Decimal('50.00')
        )
        
        referrer_result = referral.calculate_referrer_discount(Decimal('100.00'))
        referee_result = referral.calculate_referee_discount(Decimal('100.00'))
        
        self.assertEqual(referrer_result['discount_amount'], Decimal('20.00'))
        self.assertEqual(referee_result['discount_amount'], Decimal('50.00'))
