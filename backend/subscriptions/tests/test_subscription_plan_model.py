"""
Comprehensive tests for SubscriptionPlan model.
Tests cover creation, validation, relationships, pricing, and business logic.
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from subscriptions.models import SubscriptionPlan, Feature


@pytest.mark.django_db
class TestSubscriptionPlanModel:
    """Test basic SubscriptionPlan model functionality"""
    
    def test_create_plan_success(self):
        """Test successful plan creation with required fields"""
        plan = SubscriptionPlan.objects.create(
            name='Basic Plan',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        
        assert plan.id is not None
        assert plan.name == 'Basic Plan'
        assert plan.base_price == Decimal('9.99')
        assert plan.billing_period == 'monthly'
        assert plan.slug == 'basic-plan-monthly'
        assert plan.trial_days == 0
        assert plan.is_active is True
        assert plan.is_featured is False
        assert plan.sort_order == 0
        assert plan.limits == {}
    
    def test_plan_auto_slug_generation(self):
        """Test that slug is auto-generated from name and billing period"""
        plan = SubscriptionPlan.objects.create(
            name='Premium Package',
            base_price=Decimal('49.99'),
            billing_period='yearly'
        )
        
        assert plan.slug == 'premium-package-yearly'
    
    def test_plan_slug_uniqueness(self):
        """Test that plan slugs must be unique"""
        SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan-monthly',
            base_price=Decimal('19.99'),
            billing_period='monthly'
        )
        
        # Try to create another plan with same slug
        with pytest.raises(ValidationError):
            SubscriptionPlan.objects.create(
                name='Another Pro Plan',
                slug='pro-plan-monthly',
                base_price=Decimal('29.99'),
                billing_period='monthly'
            )
    
    def test_plan_negative_price_validation(self):
        """Test that negative prices are not allowed"""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan.objects.create(
                name='Invalid Plan',
                base_price=Decimal('-10.00'),
                billing_period='monthly'
            )
        
        assert 'base_price' in str(exc_info.value)
    
    def test_plan_negative_trial_days_validation(self):
        """Test that negative trial days are not allowed"""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan.objects.create(
                name='Invalid Plan',
                base_price=Decimal('10.00'),
                billing_period='monthly',
                trial_days=-7
            )
        
        assert 'trial_days' in str(exc_info.value)
    
    def test_plan_string_representation(self):
        """Test __str__ method returns name with billing period"""
        plan = SubscriptionPlan.objects.create(
            name='Enterprise',
            base_price=Decimal('99.99'),
            billing_period='monthly'
        )
        
        assert str(plan) == 'Enterprise (Monthly)'
    
    def test_plan_billing_period_choices(self):
        """Test all billing period choices work"""
        periods = ['weekly', 'monthly', 'quarterly', 'yearly', 'lifetime']
        
        for period in periods:
            plan = SubscriptionPlan.objects.create(
                name=f'{period.title()} Plan',
                base_price=Decimal('10.00'),
                billing_period=period
            )
            assert plan.billing_period == period
    
    def test_plan_ordering(self):
        """Test plans are ordered by sort_order then base_price"""
        plan3 = SubscriptionPlan.objects.create(
            name='Plan C',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            sort_order=2
        )
        plan1 = SubscriptionPlan.objects.create(
            name='Plan A',
            base_price=Decimal('10.00'),
            billing_period='monthly',
            sort_order=0
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Plan B',
            base_price=Decimal('20.00'),
            billing_period='monthly',
            sort_order=1
        )
        
        plans = list(SubscriptionPlan.objects.all())
        assert plans[0] == plan1
        assert plans[1] == plan2
        assert plans[2] == plan3
    
    def test_plan_filter_active(self):
        """Test filtering active plans"""
        active = SubscriptionPlan.objects.create(
            name='Active Plan',
            base_price=Decimal('10.00'),
            billing_period='monthly',
            is_active=True
        )
        inactive = SubscriptionPlan.objects.create(
            name='Inactive Plan',
            base_price=Decimal('15.00'),
            billing_period='monthly',
            is_active=False
        )
        
        active_plans = SubscriptionPlan.objects.filter(is_active=True)
        assert active in active_plans
        assert inactive not in active_plans
    
    def test_plan_filter_featured(self):
        """Test filtering featured plans"""
        featured = SubscriptionPlan.objects.create(
            name='Featured Plan',
            base_price=Decimal('10.00'),
            billing_period='monthly',
            is_featured=True
        )
        regular = SubscriptionPlan.objects.create(
            name='Regular Plan',
            base_price=Decimal('15.00'),
            billing_period='monthly',
            is_featured=False
        )
        
        featured_plans = SubscriptionPlan.objects.filter(is_featured=True)
        assert featured in featured_plans
        assert regular not in featured_plans


@pytest.mark.django_db
class TestSubscriptionPlanFeatures:
    """Test SubscriptionPlan feature relationships"""
    
    def test_add_features_to_plan(self):
        """Test adding features to a plan"""
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=Decimal('29.99'),
            billing_period='monthly'
        )
        
        feature1 = Feature.objects.create(
            key='premium_signals',
            name='Premium Signals',
            category='signals'
        )
        feature2 = Feature.objects.create(
            key='telegram_access',
            name='Telegram Access',
            category='telegram'
        )
        
        plan.features.add(feature1, feature2)
        
        assert plan.features.count() == 2
        assert feature1 in plan.features.all()
        assert feature2 in plan.features.all()
    
    def test_plan_without_features(self):
        """Test plan can exist without features"""
        plan = SubscriptionPlan.objects.create(
            name='Basic Plan',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        
        assert plan.features.count() == 0
    
    def test_get_feature_count(self):
        """Test get_feature_count method"""
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=Decimal('29.99'),
            billing_period='monthly'
        )
        
        for i in range(5):
            feature = Feature.objects.create(
                key=f'feature_{i}',
                name=f'Feature {i}',
                category='signals'
            )
            plan.features.add(feature)
        
        assert plan.get_feature_count() == 5
    
    def test_get_features_by_category(self):
        """Test grouping features by category"""
        plan = SubscriptionPlan.objects.create(
            name='Complete Plan',
            base_price=Decimal('99.99'),
            billing_period='monthly'
        )
        
        # Create features in different categories
        signal_feature = Feature.objects.create(
            key='signals_premium',
            name='Premium Signals',
            category='signals'
        )
        telegram_feature = Feature.objects.create(
            key='telegram_vip',
            name='VIP Telegram',
            category='telegram'
        )
        course_feature = Feature.objects.create(
            key='courses_all',
            name='All Courses',
            category='courses'
        )
        
        plan.features.add(signal_feature, telegram_feature, course_feature)
        
        features_by_category = plan.get_features_by_category()
        
        assert 'Signals & Trading' in features_by_category
        assert 'Telegram Groups' in features_by_category
        assert 'Courses & Education' in features_by_category
        assert len(features_by_category['Signals & Trading']) == 1
    
    def test_feature_to_multiple_plans(self):
        """Test that a feature can belong to multiple plans"""
        feature = Feature.objects.create(
            key='basic_signals',
            name='Basic Signals',
            category='signals'
        )
        
        plan1 = SubscriptionPlan.objects.create(
            name='Basic',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Pro',
            base_price=Decimal('29.99'),
            billing_period='monthly'
        )
        
        plan1.features.add(feature)
        plan2.features.add(feature)
        
        assert feature in plan1.features.all()
        assert feature in plan2.features.all()
        assert feature.plans.count() == 2


@pytest.mark.django_db
class TestSubscriptionPlanPricing:
    """Test SubscriptionPlan pricing methods"""
    
    def test_get_price_display_weekly(self):
        """Test price display for weekly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Weekly Plan',
            base_price=Decimal('2.99'),
            billing_period='weekly'
        )
        
        assert plan.get_price_display() == '$2.99/wk'
    
    def test_get_price_display_monthly(self):
        """Test price display for monthly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Monthly Plan',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        
        assert plan.get_price_display() == '$9.99/mo'
    
    def test_get_price_display_quarterly(self):
        """Test price display for quarterly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Quarterly Plan',
            base_price=Decimal('24.99'),
            billing_period='quarterly'
        )
        
        assert plan.get_price_display() == '$24.99/3mo'
    
    def test_get_price_display_yearly(self):
        """Test price display for yearly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Yearly Plan',
            base_price=Decimal('99.99'),
            billing_period='yearly'
        )
        
        assert plan.get_price_display() == '$99.99/yr'
    
    def test_get_price_display_lifetime(self):
        """Test price display for lifetime plan"""
        plan = SubscriptionPlan.objects.create(
            name='Lifetime Plan',
            base_price=Decimal('499.99'),
            billing_period='lifetime'
        )
        
        assert plan.get_price_display() == '$499.99'
    
    def test_get_monthly_equivalent_weekly(self):
        """Test monthly equivalent for weekly plan (4.33 weeks per month)"""
        plan = SubscriptionPlan.objects.create(
            name='Weekly',
            base_price=Decimal('5.00'),
            billing_period='weekly'
        )
        
        # 5.00 * 4.33 = 21.65
        assert plan.get_monthly_equivalent() == Decimal('21.65')
    
    def test_get_monthly_equivalent_monthly(self):
        """Test monthly equivalent for monthly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Monthly',
            base_price=Decimal('10.00'),
            billing_period='monthly'
        )
        
        assert plan.get_monthly_equivalent() == Decimal('10.00')
    
    def test_get_monthly_equivalent_quarterly(self):
        """Test monthly equivalent for quarterly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Quarterly',
            base_price=Decimal('27.00'),
            billing_period='quarterly'
        )
        
        assert plan.get_monthly_equivalent() == Decimal('9.00')
    
    def test_get_monthly_equivalent_yearly(self):
        """Test monthly equivalent for yearly plan"""
        plan = SubscriptionPlan.objects.create(
            name='Yearly',
            base_price=Decimal('96.00'),
            billing_period='yearly'
        )
        
        assert plan.get_monthly_equivalent() == Decimal('8.00')
    
    def test_get_monthly_equivalent_lifetime(self):
        """Test monthly equivalent for lifetime plan (assumes 24 months)"""
        plan = SubscriptionPlan.objects.create(
            name='Lifetime',
            base_price=Decimal('240.00'),
            billing_period='lifetime'
        )
        
        assert plan.get_monthly_equivalent() == Decimal('10.00')


@pytest.mark.django_db
class TestSubscriptionPlanTrial:
    """Test SubscriptionPlan trial period functionality"""
    
    def test_plan_with_trial(self):
        """Test plan with trial period"""
        plan = SubscriptionPlan.objects.create(
            name='Trial Plan',
            base_price=Decimal('19.99'),
            billing_period='monthly',
            trial_days=7
        )
        
        assert plan.trial_days == 7
        assert plan.has_trial() is True
    
    def test_plan_without_trial(self):
        """Test plan without trial period"""
        plan = SubscriptionPlan.objects.create(
            name='No Trial Plan',
            base_price=Decimal('19.99'),
            billing_period='monthly',
            trial_days=0
        )
        
        assert plan.trial_days == 0
        assert plan.has_trial() is False
    
    def test_plan_30_day_trial(self):
        """Test plan with 30-day trial"""
        plan = SubscriptionPlan.objects.create(
            name='Long Trial Plan',
            base_price=Decimal('49.99'),
            billing_period='monthly',
            trial_days=30
        )
        
        assert plan.trial_days == 30
        assert plan.has_trial() is True


@pytest.mark.django_db
class TestSubscriptionPlanLimits:
    """Test SubscriptionPlan limits and quotas"""
    
    def test_plan_with_limits(self):
        """Test plan with custom limits"""
        limits = {
            'max_signals': 100,
            'max_courses': 5,
            'max_api_calls': 1000
        }
        
        plan = SubscriptionPlan.objects.create(
            name='Limited Plan',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            limits=limits
        )
        
        assert plan.limits == limits
        assert plan.limits['max_signals'] == 100
    
    def test_plan_without_limits(self):
        """Test plan without custom limits (default empty dict)"""
        plan = SubscriptionPlan.objects.create(
            name='Unlimited Plan',
            base_price=Decimal('99.99'),
            billing_period='monthly'
        )
        
        assert plan.limits == {}
    
    def test_plan_update_limits(self):
        """Test updating plan limits"""
        plan = SubscriptionPlan.objects.create(
            name='Flexible Plan',
            base_price=Decimal('39.99'),
            billing_period='monthly',
            limits={'max_signals': 50}
        )
        
        plan.limits['max_courses'] = 10
        plan.save()
        
        plan.refresh_from_db()
        assert plan.limits['max_signals'] == 50
        assert plan.limits['max_courses'] == 10


@pytest.mark.django_db
class TestSubscriptionPlanEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_plan_with_very_long_name(self):
        """Test plan with maximum length name (slug will be truncated if needed)"""
        # Use 180 chars to leave room for billing period in slug
        long_name = 'A' * 180
        plan = SubscriptionPlan.objects.create(
            name=long_name,
            base_price=Decimal('10.00'),
            billing_period='monthly'
        )
        
        assert len(plan.name) == 180
        # Slug should be auto-generated and within 200 char limit
        assert len(plan.slug) <= 200
    
    def test_plan_with_zero_price(self):
        """Test free plan with zero price"""
        plan = SubscriptionPlan.objects.create(
            name='Free Plan',
            base_price=Decimal('0.00'),
            billing_period='monthly'
        )
        
        assert plan.base_price == Decimal('0.00')
        assert plan.get_price_display() == '$0.00/mo'
    
    def test_plan_with_large_price(self):
        """Test plan with very large price"""
        plan = SubscriptionPlan.objects.create(
            name='Expensive Plan',
            base_price=Decimal('99999.99'),
            billing_period='lifetime'
        )
        
        assert plan.base_price == Decimal('99999.99')
    
    def test_plan_update_billing_period(self):
        """Test updating plan billing period"""
        plan = SubscriptionPlan.objects.create(
            name='Flexible Plan',
            base_price=Decimal('10.00'),
            billing_period='monthly'
        )
        
        plan.billing_period = 'yearly'
        plan.base_price = Decimal('100.00')
        plan.save()
        
        plan.refresh_from_db()
        assert plan.billing_period == 'yearly'
        assert plan.base_price == Decimal('100.00')
    
    def test_plan_deletion(self):
        """Test plan can be deleted"""
        plan = SubscriptionPlan.objects.create(
            name='Temporary Plan',
            base_price=Decimal('10.00'),
            billing_period='monthly'
        )
        
        plan_id = plan.id
        plan.delete()
        
        assert SubscriptionPlan.objects.filter(id=plan_id).count() == 0
    
    def test_bulk_create_plans(self):
        """Test creating multiple plans at once"""
        plans = [
            SubscriptionPlan(
                name=f'Plan {i}',
                slug=f'plan-{i}-monthly',
                base_price=Decimal(f'{i * 10}.00'),
                billing_period='monthly'
            )
            for i in range(1, 6)
        ]
        
        # Note: bulk_create bypasses save(), so we can't use full_clean()
        # This is a limitation we're aware of
        SubscriptionPlan.objects.bulk_create(plans)
        
        assert SubscriptionPlan.objects.count() == 5
    
    def test_plan_stripe_price_id(self):
        """Test plan with Stripe price ID"""
        plan = SubscriptionPlan.objects.create(
            name='Stripe Plan',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            stripe_price_id='price_1234567890abcdef'
        )
        
        assert plan.stripe_price_id == 'price_1234567890abcdef'
    
    def test_plan_unicode_in_description(self):
        """Test plan with Unicode characters in description"""
        plan = SubscriptionPlan.objects.create(
            name='International Plan',
            base_price=Decimal('19.99'),
            billing_period='monthly',
            description='Plan with emoji 🚀 and Unicode: こんにちは'
        )
        
        assert '🚀' in plan.description
        assert 'こんにちは' in plan.description
