"""
Tests for User model subscription integration (Phase 1.1)
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from subscriptions.models import SubscriptionPlan, Feature
# Note: CourseAccess is the current model, Enrollment will be created in Task 1.3
from courses.models import Course, CourseAccess

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestUserSubscriptionFields:
    """Test subscription-related fields on User model"""
    
    def test_user_default_subscription_status(self):
        """User should have 'none' subscription status by default"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.subscription_status == 'none'
        assert user.current_plan is None
        assert user.subscription_start_date is None
        assert user.subscription_end_date is None
        assert user.trial_end_date is None
        assert user.trial_used is False
    
    def test_user_usage_stats_default(self):
        """User should have empty usage_stats dict by default"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.usage_stats == {}
    
    def test_subscription_status_choices(self):
        """Test all subscription status choices"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        valid_statuses = ['active', 'trialing', 'past_due', 'cancelled', 'expired', 'none']
        for status in valid_statuses:
            user.subscription_status = status
            user.save()
            user.refresh_from_db()
            assert user.subscription_status == status


class TestHasFeature:
    """Test User.has_feature() method"""
    
    @pytest.fixture
    def feature(self):
        """Create a test feature"""
        return Feature.objects.create(
            key='test_feature',
            name='Test Feature',
            category='signals',
            is_active=True
        )
    
    @pytest.fixture
    def plan_with_feature(self, feature):
        """Create a plan with the test feature"""
        plan = SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium',
            base_price=Decimal('99.99'),
            billing_period='monthly',
            is_active=True
        )
        plan.features.add(feature)
        return plan
    
    @pytest.fixture
    def plan_without_feature(self):
        """Create a plan without any features"""
        return SubscriptionPlan.objects.create(
            name='Basic Plan',
            slug='basic',
            base_price=Decimal('49.99'),
            billing_period='monthly',
            is_active=True
        )
    
    def test_has_feature_no_plan(self, feature):
        """User without plan should not have any features"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.has_feature('test_feature') is False
    
    def test_has_feature_with_plan_and_feature(self, feature, plan_with_feature):
        """User with active plan should have plan's features"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.current_plan = plan_with_feature
        user.subscription_status = 'active'
        user.subscription_start_date = timezone.now()
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        assert user.has_feature('test_feature') is True
    
    def test_has_feature_plan_without_feature(self, feature, plan_without_feature):
        """User with plan that doesn't include feature should return False"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.current_plan = plan_without_feature
        user.subscription_status = 'active'
        user.subscription_start_date = timezone.now()
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        assert user.has_feature('test_feature') is False
    
    def test_has_feature_inactive_subscription(self, feature, plan_with_feature):
        """User with expired subscription should not have features"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.current_plan = plan_with_feature
        user.subscription_status = 'expired'
        user.save()
        
        assert user.has_feature('test_feature') is False
    
    def test_has_feature_inactive_feature(self, feature, plan_with_feature):
        """Inactive features should return False even if in plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.current_plan = plan_with_feature
        user.subscription_status = 'active'
        user.subscription_start_date = timezone.now()
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        # Deactivate the feature
        feature.is_active = False
        feature.save()
        
        assert user.has_feature('test_feature') is False


class TestGetPlanLimits:
    """Test User.get_plan_limits() method"""
    
    def test_get_plan_limits_no_plan(self):
        """User without plan should return empty dict"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.get_plan_limits() == {}
    
    def test_get_plan_limits_with_limits(self):
        """User with plan should return plan limits"""
        plan = SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium',
            base_price=Decimal('99.99'),
            billing_period='monthly',
            is_active=True,
            limits={'max_signals': 100, 'max_courses': 5}
        )
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.current_plan = plan
        user.save()
        
        limits = user.get_plan_limits()
        assert limits['max_signals'] == 100
        assert limits['max_courses'] == 5
    
    def test_get_plan_limits_empty_limits(self):
        """Plan with no limits should return empty dict"""
        plan = SubscriptionPlan.objects.create(
            name='Unlimited Plan',
            slug='unlimited',
            base_price=Decimal('199.99'),
            billing_period='monthly',
            is_active=True
        )
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.current_plan = plan
        user.save()
        
        assert user.get_plan_limits() == {}


class TestIsSubscriptionActive:
    """Test User.is_subscription_active() method"""
    
    def test_no_subscription_inactive(self):
        """User with no subscription should be inactive"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.is_subscription_active() is False
    
    def test_active_subscription_valid(self):
        """User with active subscription within dates should be active"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'active'
        user.subscription_start_date = timezone.now() - timedelta(days=10)
        user.subscription_end_date = timezone.now() + timedelta(days=20)
        user.save()
        
        assert user.is_subscription_active() is True
    
    def test_active_subscription_expired(self):
        """User with active status but past end date should be inactive"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'active'
        user.subscription_start_date = timezone.now() - timedelta(days=40)
        user.subscription_end_date = timezone.now() - timedelta(days=10)
        user.save()
        
        assert user.is_subscription_active() is False
    
    def test_lifetime_subscription(self):
        """User with lifetime subscription (no end date) should be active"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'active'
        user.subscription_start_date = timezone.now()
        user.subscription_end_date = None  # Lifetime
        user.save()
        
        assert user.is_subscription_active() is True
    
    def test_trialing_valid(self):
        """User in valid trial period should be active"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'trialing'
        user.subscription_start_date = timezone.now()
        user.trial_end_date = timezone.now() + timedelta(days=7)
        user.save()
        
        assert user.is_subscription_active() is True
    
    def test_trialing_expired(self):
        """User with expired trial should be inactive"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'trialing'
        user.subscription_start_date = timezone.now() - timedelta(days=10)
        user.trial_end_date = timezone.now() - timedelta(days=3)
        user.save()
        
        assert user.is_subscription_active() is False
    
    def test_cancelled_subscription_inactive(self):
        """Cancelled subscription should be inactive"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'cancelled'
        user.save()
        
        assert user.is_subscription_active() is False


class TestStartTrial:
    """Test User.start_trial() method"""
    
    @pytest.fixture
    def trial_plan(self):
        """Create a plan with trial period"""
        return SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium',
            base_price=Decimal('99.99'),
            billing_period='monthly',
            trial_days=7,
            is_active=True
        )
    
    def test_start_trial_success(self, trial_plan):
        """Starting trial should set correct status and dates"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        result = user.start_trial(trial_plan)
        
        assert result is True
        assert user.subscription_status == 'trialing'
        assert user.current_plan == trial_plan
        assert user.trial_used is True
        assert user.trial_end_date is not None
        assert user.trial_end_date > timezone.now()
    
    def test_start_trial_already_used(self, trial_plan):
        """User who already used trial should not be able to start again"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.trial_used = True
        user.save()
        
        with pytest.raises(ValueError, match="already used their trial"):
            user.start_trial(trial_plan)
    
    def test_start_trial_no_trial_period(self):
        """Plan without trial period should raise error"""
        no_trial_plan = SubscriptionPlan.objects.create(
            name='No Trial Plan',
            slug='no-trial',
            base_price=Decimal('99.99'),
            billing_period='monthly',
            trial_days=0,
            is_active=True
        )
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        with pytest.raises(ValueError, match="does not offer a trial"):
            user.start_trial(no_trial_plan)


class TestActivateSubscription:
    """Test User.activate_subscription() method"""
    
    @pytest.fixture
    def monthly_plan(self):
        """Create a monthly plan"""
        return SubscriptionPlan.objects.create(
            name='Monthly Plan',
            slug='monthly',
            base_price=Decimal('49.99'),
            billing_period='monthly',
            is_active=True
        )
    
    @pytest.fixture
    def lifetime_plan(self):
        """Create a lifetime plan"""
        return SubscriptionPlan.objects.create(
            name='Lifetime Plan',
            slug='lifetime',
            base_price=Decimal('999.99'),
            billing_period='lifetime',
            is_active=True
        )
    
    def test_activate_monthly_subscription(self, monthly_plan):
        """Activating monthly subscription should set 30-day end date"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        result = user.activate_subscription(monthly_plan)
        
        assert result is True
        assert user.subscription_status == 'active'
        assert user.current_plan == monthly_plan
        assert user.subscription_start_date is not None
        assert user.subscription_end_date is not None
        
        # Should be approximately 30 days from now
        expected_end = timezone.now() + timedelta(days=30)
        time_diff = abs((user.subscription_end_date - expected_end).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_activate_lifetime_subscription(self, lifetime_plan):
        """Activating lifetime subscription should have no end date"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        result = user.activate_subscription(lifetime_plan)
        
        assert result is True
        assert user.subscription_status == 'active'
        assert user.current_plan == lifetime_plan
        assert user.subscription_end_date is None
    
    def test_activate_custom_duration(self, monthly_plan):
        """Activating with custom duration should override plan duration"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        result = user.activate_subscription(monthly_plan, duration_days=90)
        
        assert result is True
        expected_end = timezone.now() + timedelta(days=90)
        time_diff = abs((user.subscription_end_date - expected_end).total_seconds())
        assert time_diff < 60


class TestCancelSubscription:
    """Test User.cancel_subscription() method"""
    
    def test_cancel_active_subscription(self):
        """Cancelling active subscription should change status"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'active'
        user.save()
        
        result = user.cancel_subscription()
        
        assert result is True
        assert user.subscription_status == 'cancelled'
    
    def test_cancel_trialing_subscription(self):
        """Cancelling trial subscription should change status"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'trialing'
        user.save()
        
        result = user.cancel_subscription()
        
        assert result is True
        assert user.subscription_status == 'cancelled'
    
    def test_cancel_no_subscription(self):
        """Cancelling when no subscription should return False"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.subscription_status = 'none'
        user.save()
        
        result = user.cancel_subscription()
        
        assert result is False
        assert user.subscription_status == 'none'


class TestTrackUsage:
    """Test User.track_usage() method"""
    
    def test_track_usage_first_time(self):
        """Tracking usage for first time should initialize counter"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        user.track_usage('signals_viewed')
        
        assert user.usage_stats['signals_viewed'] == 1
    
    def test_track_usage_increment(self):
        """Tracking usage multiple times should increment counter"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        user.track_usage('signals_viewed')
        user.track_usage('signals_viewed')
        user.track_usage('signals_viewed')
        
        user.refresh_from_db()
        assert user.usage_stats['signals_viewed'] == 3
    
    def test_track_usage_custom_increment(self):
        """Tracking with custom increment should add that amount"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        user.track_usage('credits_used', increment=5)
        
        assert user.usage_stats['credits_used'] == 5
    
    def test_track_multiple_features(self):
        """Tracking different features should maintain separate counters"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        user.track_usage('signals_viewed')
        user.track_usage('courses_enrolled')
        user.track_usage('signals_viewed')
        
        user.refresh_from_db()
        assert user.usage_stats['signals_viewed'] == 2
        assert user.usage_stats['courses_enrolled'] == 1


class TestResetUsageStats:
    """Test User.reset_usage_stats() method"""
    
    def test_reset_usage_stats(self):
        """Resetting usage stats should clear all counters"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        user.track_usage('signals_viewed', increment=10)
        user.track_usage('courses_enrolled', increment=3)
        user.refresh_from_db()
        
        assert user.usage_stats != {}
        
        user.reset_usage_stats()
        user.refresh_from_db()
        
        assert user.usage_stats == {}
