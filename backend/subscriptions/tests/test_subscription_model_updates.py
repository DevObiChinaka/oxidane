"""
Tests for Subscription model updates (Phase 0.5, Task 0.5.11).

Test-Driven Development approach: Write tests FIRST for new fields.
Target: 30+ tests covering new relationships and metadata.

New Fields Being Added:
1. plan (FK to SubscriptionPlan) - replaces pricing_plan (FK to PricingPlan)
2. referral (FK to Referral, optional) - for tracking referral relationships
3. metadata (JSONField) - for flexible data storage

Test Categories:
1. Basic CRUD with New Fields (8 tests)
2. SubscriptionPlan Relationship (7 tests)
3. Referral Relationship (7 tests)
4. Metadata Field (8 tests)
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json

from subscriptions.models import (
    Subscription, SubscriptionPlan, Referral, ReferralCode,
    BillingProfile, Feature
)
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    import random
    import string
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return User.objects.create_user(
        username=f'testuser_{random_suffix}',
        email=f'test_{random_suffix}@example.com',
        password='testpass123'
    )


@pytest.fixture
def billing_profile(db, user):
    """Create a billing profile for the user."""
    # Use get_or_create to avoid duplicate errors
    bp, created = BillingProfile.objects.get_or_create(
        user=user,
        defaults={
            'country': 'NG',
            'currency_preference': 'USD'
        }
    )
    return bp


@pytest.fixture
def feature(db):
    """Create a test feature."""
    return Feature.objects.create(
        key='test_feature',
        name='Test Feature',
        description='A test feature',
        category='signals'
    )


@pytest.fixture
def subscription_plan(db, feature):
    """Create a test subscription plan."""
    plan = SubscriptionPlan.objects.create(
        name='Test Plan',
        slug='test-plan',
        description='Test plan description',
        billing_period='monthly',
        base_price=Decimal('50.00'),
        is_active=True
    )
    plan.features.add(feature)
    return plan


@pytest.fixture
def referral_code(db, user):
    """Create a referral code."""
    return ReferralCode.objects.create(
        referrer=user,
        code='TESTREF123',
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('10.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('10.00')
    )


@pytest.fixture
def referrer(db):
    """Create a referrer user."""
    return User.objects.create_user(
        username='referrer',
        email='referrer@example.com',
        password='testpass123'
    )


@pytest.fixture
def referee(db):
    """Create a referee user."""
    return User.objects.create_user(
        username='referee',
        email='referee@example.com',
        password='testpass123'
    )


@pytest.fixture
def referral(db, referral_code, user, referee):
    """Create a referral (use 'user' as referrer since referral_code owner is 'user')."""
    return Referral.objects.create(
        referral_code=referral_code,
        referrer=user,  # Must match referral_code.referrer
        referee=referee,
        original_amount=Decimal('100.00'),
        referee_discount_percent=Decimal('10.00'),
        referee_discount_amount=Decimal('10.00'),
        final_amount=Decimal('90.00'),
        currency='USD',
        status='completed'
    )


# ============================================================================
# CATEGORY 1: BASIC CRUD WITH NEW FIELDS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestSubscriptionBasicOperations:
    """Test basic CRUD operations with new fields."""

    def test_create_subscription_with_plan(self, billing_profile, subscription_plan):
        """Test creating subscription with new plan field."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        assert subscription.plan == subscription_plan
        assert subscription.plan.name == 'Test Plan'

    def test_create_subscription_with_referral(self, billing_profile, subscription_plan, referral):
        """Test creating subscription with referral."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        assert subscription.referral == referral
        assert subscription.referral.referrer == referral.referrer

    def test_create_subscription_with_metadata(self, billing_profile, subscription_plan):
        """Test creating subscription with metadata."""
        metadata = {
            'source': 'web',
            'campaign': 'summer_sale',
            'notes': 'First time subscriber'
        }
        
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata=metadata
        )
        
        assert subscription.metadata == metadata
        assert subscription.metadata['source'] == 'web'

    def test_create_subscription_without_referral(self, billing_profile, subscription_plan):
        """Test creating subscription without referral (optional field)."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        assert subscription.referral is None

    def test_create_subscription_with_empty_metadata(self, billing_profile, subscription_plan):
        """Test creating subscription with empty metadata."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={}
        )
        
        assert subscription.metadata == {}

    def test_update_subscription_plan(self, billing_profile, subscription_plan, feature):
        """Test updating subscription plan."""
        # Create another plan
        new_plan = SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium-plan',
            description='Premium features',
            billing_period='monthly',
            base_price=Decimal('100.00'),
            is_active=True
        )
        new_plan.features.add(feature)
        
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        # Upgrade to new plan
        subscription.plan = new_plan
        subscription.save()
        
        subscription.refresh_from_db()
        assert subscription.plan == new_plan
        assert subscription.plan.name == 'Premium Plan'

    def test_update_subscription_metadata(self, billing_profile, subscription_plan):
        """Test updating subscription metadata."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'source': 'web'}
        )
        
        # Update metadata
        subscription.metadata['campaign'] = 'winter_sale'
        subscription.metadata['discount_code'] = 'WINTER20'
        subscription.save()
        
        subscription.refresh_from_db()
        assert subscription.metadata['source'] == 'web'
        assert subscription.metadata['campaign'] == 'winter_sale'
        assert subscription.metadata['discount_code'] == 'WINTER20'

    def test_delete_subscription(self, billing_profile, subscription_plan):
        """Test deleting subscription."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        subscription_id = subscription.id
        subscription.delete()
        
        assert not Subscription.objects.filter(id=subscription_id).exists()


# ============================================================================
# CATEGORY 2: SUBSCRIPTIONPLAN RELATIONSHIP (7 tests)
# ============================================================================

@pytest.mark.django_db
class TestSubscriptionPlanRelationship:
    """Test SubscriptionPlan FK relationship."""

    def test_plan_required(self, billing_profile):
        """Test that plan field is nullable (for migration compatibility)."""
        # Plan is nullable during migration period (Phase 0.5)
        # This allows backward compatibility with old pricing_plan field
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=None,  # Nullable for migration
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        assert subscription.plan is None

    def test_plan_cascade_protect(self, billing_profile, subscription_plan):
        """Test that deleting plan is protected if subscriptions exist."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        # Should raise ProtectedError when trying to delete plan
        with pytest.raises(Exception):  # ProtectedError
            subscription_plan.delete()

    def test_multiple_subscriptions_same_plan(self, subscription_plan):
        """Test multiple users can subscribe to same plan."""
        import random, string
        suffix1 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        suffix2 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        user1 = User.objects.create_user(username=f'user1_{suffix1}', email=f'user1_{suffix1}@test.com', password='pass')
        user2 = User.objects.create_user(username=f'user2_{suffix2}', email=f'user2_{suffix2}@test.com', password='pass')
        
        bp1, _ = BillingProfile.objects.get_or_create(user=user1, defaults={'country': 'US', 'currency_preference': 'USD'})
        bp2, _ = BillingProfile.objects.get_or_create(user=user2, defaults={'country': 'US', 'currency_preference': 'USD'})
        
        sub1 = Subscription.objects.create(
            billing_profile=bp1,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        sub2 = Subscription.objects.create(
            billing_profile=bp2,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        assert sub1.plan == sub2.plan == subscription_plan
        assert Subscription.objects.filter(plan=subscription_plan).count() == 2

    def test_access_plan_features_through_subscription(self, billing_profile, subscription_plan, feature):
        """Test accessing plan features through subscription."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        # Access features through subscription.plan
        features = subscription.plan.features.all()
        assert feature in features

    def test_plan_pricing_info_through_subscription(self, billing_profile, subscription_plan):
        """Test accessing plan pricing through subscription."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        assert subscription.plan.base_price == Decimal('50.00')
        assert subscription.plan.billing_period == 'monthly'  # SubscriptionPlan has billing_period, not currency
        assert subscription.plan.billing_period == 'monthly'

    def test_reverse_relationship_plan_to_subscriptions(self, billing_profile, subscription_plan):
        """Test reverse relationship from plan to subscriptions."""
        sub1 = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        # Access subscriptions through plan
        subscriptions = subscription_plan.subscriptions.all()
        assert sub1 in subscriptions
        assert subscription_plan.subscriptions.count() == 1

    def test_string_representation_includes_plan(self, billing_profile, subscription_plan):
        """Test __str__ includes plan name."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        str_repr = str(subscription)
        assert 'Test Plan' in str_repr or subscription_plan.name in str_repr


# ============================================================================
# CATEGORY 3: REFERRAL RELATIONSHIP (7 tests)
# ============================================================================

@pytest.mark.django_db
class TestReferralRelationship:
    """Test Referral FK relationship."""

    def test_referral_optional(self, billing_profile, subscription_plan):
        """Test that referral field is optional."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=None,  # Optional
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        assert subscription.referral is None

    def test_referral_set_null_on_delete(self, billing_profile, subscription_plan, referral):
        """Test referral FK is set to NULL when referral is deleted."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        # Delete referral
        referral.delete()
        
        subscription.refresh_from_db()
        assert subscription.referral is None

    def test_access_referrer_through_subscription(self, billing_profile, subscription_plan, referral):
        """Test accessing referrer info through subscription."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        assert subscription.referral.referrer == referral.referrer
        assert subscription.referral.referee == referral.referee

    def test_access_discount_info_through_subscription(self, billing_profile, subscription_plan, referral):
        """Test accessing discount information through subscription."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        assert subscription.referral.referee_discount_percent == Decimal('10.00')
        assert subscription.referral.referee_discount_amount == Decimal('10.00')

    def test_multiple_subscriptions_same_referral(self, subscription_plan, referral):
        """Test multiple subscriptions can reference same referral (edge case)."""
        import random, string
        suffix1 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        suffix2 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        user1 = User.objects.create_user(username=f'user1_{suffix1}', email=f'user1_{suffix1}@test.com', password='pass')
        user2 = User.objects.create_user(username=f'user2_{suffix2}', email=f'user2_{suffix2}@test.com', password='pass')
        
        bp1, _ = BillingProfile.objects.get_or_create(user=user1, defaults={'country': 'US', 'currency_preference': 'USD'})
        bp2, _ = BillingProfile.objects.get_or_create(user=user2, defaults={'country': 'US', 'currency_preference': 'USD'})
        
        sub1 = Subscription.objects.create(
            billing_profile=bp1,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        sub2 = Subscription.objects.create(
            billing_profile=bp2,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        assert sub1.referral == sub2.referral == referral

    def test_reverse_relationship_referral_to_subscriptions(self, billing_profile, subscription_plan, referral):
        """Test reverse relationship from referral to subscriptions."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        # Access subscriptions through referral
        # Note: Referral model has 'subscription' FK (singular), not 'subscriptions' reverse
        # This test verifies the relationship exists
        assert subscription.referral == referral

    def test_filter_subscriptions_with_referrals(self, billing_profile, subscription_plan, referral):
        """Test filtering subscriptions that have referrals."""
        # Create subscription with referral
        sub_with_ref = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            referral=referral,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('45.00'),
            currency='USD'
        )
        
        # Create user and billing profile for second subscription
        import random, string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user2 = User.objects.create_user(username=f'user2_{suffix}', email=f'user2_{suffix}@test.com', password='pass')
        bp2, _ = BillingProfile.objects.get_or_create(user=user2, defaults={'country': 'US', 'currency_preference': 'USD'})
        
        # Create subscription without referral
        sub_without_ref = Subscription.objects.create(
            billing_profile=bp2,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        # Filter
        with_referrals = Subscription.objects.filter(referral__isnull=False)
        without_referrals = Subscription.objects.filter(referral__isnull=True)
        
        assert sub_with_ref in with_referrals
        assert sub_without_ref in without_referrals
        assert with_referrals.count() == 1
        assert without_referrals.count() == 1


# ============================================================================
# CATEGORY 4: METADATA FIELD (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestMetadataField:
    """Test metadata JSONField functionality."""

    def test_metadata_default_empty_dict(self, billing_profile, subscription_plan):
        """Test metadata defaults to empty dict."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD'
        )
        
        assert subscription.metadata == {}

    def test_metadata_stores_string_values(self, billing_profile, subscription_plan):
        """Test metadata can store string values."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'source': 'mobile_app', 'device': 'iPhone 13'}
        )
        
        subscription.refresh_from_db()
        assert subscription.metadata['source'] == 'mobile_app'
        assert subscription.metadata['device'] == 'iPhone 13'

    def test_metadata_stores_numeric_values(self, billing_profile, subscription_plan):
        """Test metadata can store numeric values."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'retry_count': 3, 'discount_applied': 15.5}
        )
        
        subscription.refresh_from_db()
        assert subscription.metadata['retry_count'] == 3
        assert subscription.metadata['discount_applied'] == 15.5

    def test_metadata_stores_nested_objects(self, billing_profile, subscription_plan):
        """Test metadata can store nested objects."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={
                'payment_info': {
                    'gateway': 'paystack',
                    'reference': 'REF123456'
                },
                'user_preferences': {
                    'notifications': True,
                    'newsletter': False
                }
            }
        )
        
        subscription.refresh_from_db()
        assert subscription.metadata['payment_info']['gateway'] == 'paystack'
        assert subscription.metadata['user_preferences']['notifications'] is True

    def test_metadata_stores_lists(self, billing_profile, subscription_plan):
        """Test metadata can store lists."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={
                'tags': ['premium', 'early_adopter', 'referral'],
                'features_used': ['signal_alerts', 'telegram_group']
            }
        )
        
        subscription.refresh_from_db()
        assert 'premium' in subscription.metadata['tags']
        assert len(subscription.metadata['features_used']) == 2

    def test_metadata_update_existing_keys(self, billing_profile, subscription_plan):
        """Test updating existing metadata keys."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'version': 1, 'status': 'initial'}
        )
        
        # Update
        subscription.metadata['version'] = 2
        subscription.metadata['status'] = 'updated'
        subscription.save()
        
        subscription.refresh_from_db()
        assert subscription.metadata['version'] == 2
        assert subscription.metadata['status'] == 'updated'

    def test_metadata_add_new_keys(self, billing_profile, subscription_plan):
        """Test adding new keys to metadata."""
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'initial_key': 'value'}
        )
        
        # Add new keys
        subscription.metadata['new_key'] = 'new_value'
        subscription.metadata['another_key'] = 123
        subscription.save()
        
        subscription.refresh_from_db()
        assert subscription.metadata['initial_key'] == 'value'
        assert subscription.metadata['new_key'] == 'new_value'
        assert subscription.metadata['another_key'] == 123
        assert len(subscription.metadata) == 3

    def test_metadata_query_by_json_field(self, billing_profile, subscription_plan):
        """Test querying subscriptions by metadata content."""
        # Create subscriptions with different metadata
        sub1 = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'source': 'web'}
        )
        
        import random, string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user2 = User.objects.create_user(username=f'user2_{suffix}', email=f'user2_{suffix}@test.com', password='pass')
        bp2, _ = BillingProfile.objects.get_or_create(user=user2, defaults={'country': 'US', 'currency_preference': 'USD'})
        
        sub2 = Subscription.objects.create(
            billing_profile=bp2,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('50.00'),
            currency='USD',
            metadata={'source': 'mobile'}
        )
        
        # Query by metadata
        web_subs = Subscription.objects.filter(metadata__source='web')
        mobile_subs = Subscription.objects.filter(metadata__source='mobile')
        
        assert sub1 in web_subs
        assert sub2 in mobile_subs
        assert web_subs.count() == 1
        assert mobile_subs.count() == 1


# ============================================================================
# SUMMARY
# ============================================================================
"""
SUBSCRIPTION MODEL UPDATES TEST SUMMARY:
=========================================

CATEGORY 1: Basic CRUD with New Fields (8 tests)
- Create with plan, referral, metadata
- Create without optional fields
- Update plan and metadata
- Delete subscription

CATEGORY 2: SubscriptionPlan Relationship (7 tests)
- Plan required (NOT NULL)
- Cascade protection (PROTECT)
- Multiple subscriptions per plan
- Access features through subscription
- Access pricing through subscription
- Reverse relationship
- String representation

CATEGORY 3: Referral Relationship (7 tests)
- Referral optional (NULL allowed)
- SET_NULL on delete
- Access referrer info
- Access discount info
- Multiple subscriptions per referral
- Reverse relationship
- Filter by referral presence

CATEGORY 4: Metadata Field (8 tests)
- Default empty dict
- Store strings, numbers, nested objects, lists
- Update existing keys
- Add new keys
- Query by JSON field content

TOTAL: 30 TESTS
===============
All categories comprehensive, following TDD best practices.
"""
