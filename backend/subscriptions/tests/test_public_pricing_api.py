"""
Tests for Public Pricing API (Task 0.5.33)

Tests GET /api/v1/subscriptions/plans/ endpoint with multi-currency support.
Public endpoint for displaying subscription plans on pricing page.

Phase 0.5, Task 0.5.33
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from subscriptions.models import (
    SubscriptionPlan, Feature, ExchangeRate
)

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests."""
    return APIClient()


@pytest.fixture
def feature1(db):
    """Create first feature."""
    return Feature.objects.create(
        key='premium_signals',
        name='Premium Trading Signals',
        description='Access to premium signals',
        category='signals',
        icon='📈'
    )


@pytest.fixture
def feature2(db):
    """Create second feature."""
    return Feature.objects.create(
        key='vip_telegram',
        name='VIP Telegram Group',
        description='Access to VIP group',
        category='telegram',
        icon='💎'
    )


@pytest.fixture
def active_plan(db, feature1, feature2):
    """Create active subscription plan with features."""
    plan = SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium-monthly',
        description='Premium features for serious traders',
        base_price=Decimal('99.00'),
        billing_period='monthly',
        trial_days=7,
        is_active=True,
        is_featured=True,
        sort_order=1
    )
    plan.features.add(feature1, feature2)
    return plan


@pytest.fixture
def inactive_plan(db):
    """Create inactive subscription plan."""
    return SubscriptionPlan.objects.create(
        name='Inactive Plan',
        slug='inactive-monthly',
        description='This plan is not available',
        base_price=Decimal('49.00'),
        billing_period='monthly',
        is_active=False
    )


@pytest.fixture
def yearly_plan(db):
    """Create yearly subscription plan."""
    return SubscriptionPlan.objects.create(
        name='Yearly Plan',
        slug='premium-yearly',
        description='Best value - yearly subscription',
        base_price=Decimal('999.00'),
        billing_period='yearly',
        is_active=True,
        is_featured=False,
        sort_order=2
    )


@pytest.fixture
def exchange_rates(db):
    """Create exchange rates for testing."""
    # USD to NGN
    ExchangeRate.objects.create(
        base_currency='USD',
        target_currency='NGN',
        rate=Decimal('1500.00')
    )
    # USD to GBP
    ExchangeRate.objects.create(
        base_currency='USD',
        target_currency='GBP',
        rate=Decimal('0.80')
    )
    # USD to EUR
    ExchangeRate.objects.create(
        base_currency='USD',
        target_currency='EUR',
        rate=Decimal('0.92')
    )


# ============================================================================
# PUBLIC ACCESS TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingAccess:
    """Test public access to pricing API."""
    
    def test_unauthenticated_can_access(self, api_client, active_plan):
        """Unauthenticated users can access public pricing API."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.json()
    
    def test_authenticated_user_can_access(self, api_client, active_plan, db):
        """Authenticated users can access public pricing API."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        api_client.force_authenticate(user=user)
        
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.json()


# ============================================================================
# PLAN LISTING TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingList:
    """Test listing subscription plans."""
    
    def test_list_only_active_plans(self, api_client, active_plan, inactive_plan):
        """Should return only active plans."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have pagination
        assert 'results' in data
        assert 'count' in data
        
        # Should only return active plan
        assert data['count'] == 1
        assert data['results'][0]['name'] == 'Premium Plan'
        assert data['results'][0]['is_active'] is True
    
    def test_list_includes_features(self, api_client, active_plan):
        """Should include plan features in response."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        assert 'features' in plan
        assert len(plan['features']) == 2
        
        # Check feature structure
        feature = plan['features'][0]
        assert 'id' in feature
        assert 'name' in feature
        assert 'icon' in feature
        assert 'category' in feature
    
    def test_list_orders_by_sort_order(self, api_client, active_plan, yearly_plan):
        """Should order plans by sort_order and base_price."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['count'] == 2
        # First plan should have lower sort_order
        assert data['results'][0]['name'] == 'Premium Plan'
        assert data['results'][1]['name'] == 'Yearly Plan'
    
    def test_list_empty_when_no_active_plans(self, api_client, inactive_plan):
        """Should return empty list when no active plans exist."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 0
        assert len(data['results']) == 0


# ============================================================================
# CURRENCY CONVERSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingCurrency:
    """Test multi-currency support."""
    
    def test_default_currency_is_usd(self, api_client, active_plan):
        """Should default to USD when no currency parameter provided."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        assert plan['currency'] == 'USD'
        assert plan['price'] == 99.00
        assert plan['base_price_usd'] == 99.00
    
    def test_convert_to_ngn(self, api_client, active_plan, exchange_rates):
        """Should convert price to NGN."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url, {'currency': 'NGN'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        assert plan['currency'] == 'NGN'
        # 99 USD * 1500 = 148,500 NGN
        assert plan['price'] == 148500.00
        assert plan['base_price_usd'] == 99.00
    
    def test_convert_to_gbp(self, api_client, active_plan, exchange_rates):
        """Should convert price to GBP."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url, {'currency': 'GBP'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        assert plan['currency'] == 'GBP'
        # 99 USD * 0.80 = 79.20 GBP
        assert plan['price'] == 79.20
        assert plan['base_price_usd'] == 99.00
    
    def test_convert_to_eur(self, api_client, active_plan, exchange_rates):
        """Should convert price to EUR."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url, {'currency': 'EUR'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        assert plan['currency'] == 'EUR'
        # 99 USD * 0.92 = 91.08 EUR
        assert plan['price'] == 91.08
        assert plan['base_price_usd'] == 99.00
    
    def test_fallback_to_usd_when_rate_not_found(self, api_client, active_plan):
        """Should fallback to USD when exchange rate not found."""
        url = reverse('subscriptions:v1-plans-list')
        # Request currency without exchange rate
        response = api_client.get(url, {'currency': 'JPY'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        # Should fallback to USD
        assert plan['currency'] == 'USD'
        assert plan['price'] == 99.00
        assert plan['base_price_usd'] == 99.00
    
    def test_currency_case_insensitive(self, api_client, active_plan, exchange_rates):
        """Currency parameter should be case-insensitive."""
        url = reverse('subscriptions:v1-plans-list')
        
        # Test lowercase
        response = api_client.get(url, {'currency': 'ngn'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['results'][0]['currency'] == 'NGN'
        
        # Test mixed case
        response = api_client.get(url, {'currency': 'GbP'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['results'][0]['currency'] == 'GBP'


# ============================================================================
# PLAN DETAIL TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingDetail:
    """Test retrieving individual plan details."""
    
    def test_retrieve_plan_details(self, api_client, active_plan):
        """Should retrieve plan details."""
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': active_plan.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['id'] == str(active_plan.id)
        assert data['name'] == 'Premium Plan'
        assert data['description'] == 'Premium features for serious traders'
        assert data['base_price'] == 99.00
        assert data['billing_period'] == 'monthly'
        assert data['trial_days'] == 7
        assert data['is_featured'] is True
    
    def test_retrieve_with_currency_conversion(self, api_client, active_plan, exchange_rates):
        """Should convert price when retrieving single plan."""
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': active_plan.id})
        response = api_client.get(url, {'currency': 'NGN'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['currency'] == 'NGN'
        assert data['price'] == 148500.00
        assert data['base_price_usd'] == 99.00
    
    def test_retrieve_inactive_plan_not_found(self, api_client, inactive_plan):
        """Should return 404 when retrieving inactive plan."""
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': inactive_plan.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_retrieve_nonexistent_plan(self, api_client):
        """Should return 404 for nonexistent plan."""
        from uuid import uuid4
        fake_id = uuid4()
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': fake_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# FILTERING TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingFilters:
    """Test filtering subscription plans."""
    
    def test_filter_by_billing_period(self, api_client, active_plan, yearly_plan):
        """Should filter plans by billing period."""
        url = reverse('subscriptions:v1-plans-list')
        
        # Filter for monthly plans
        response = api_client.get(url, {'billing_period': 'monthly'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['results'][0]['billing_period'] == 'monthly'
        
        # Filter for yearly plans
        response = api_client.get(url, {'billing_period': 'yearly'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['results'][0]['billing_period'] == 'yearly'
    
    def test_filter_by_featured(self, api_client, active_plan, yearly_plan):
        """Should filter featured plans."""
        url = reverse('subscriptions:v1-plans-list')
        
        # Filter for featured plans
        response = api_client.get(url, {'is_featured': 'true'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['results'][0]['is_featured'] is True
        
        # Filter for non-featured plans
        response = api_client.get(url, {'is_featured': 'false'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['results'][0]['is_featured'] is False
    
    def test_search_by_name(self, api_client, active_plan, yearly_plan):
        """Should search plans by name."""
        url = reverse('subscriptions:v1-plans-list')
        
        response = api_client.get(url, {'search': 'Yearly'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert 'Yearly' in data['results'][0]['name']
    
    def test_search_by_description(self, api_client, active_plan, yearly_plan):
        """Should search plans by description."""
        url = reverse('subscriptions:v1-plans-list')
        
        response = api_client.get(url, {'search': 'traders'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert 'traders' in data['results'][0]['description'].lower()
    
    def test_order_by_price_ascending(self, api_client, active_plan, yearly_plan):
        """Should order plans by price ascending."""
        url = reverse('subscriptions:v1-plans-list')
        
        response = api_client.get(url, {'ordering': 'base_price'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Premium (99) should come before Yearly (999)
        assert data['results'][0]['base_price'] < data['results'][1]['base_price']
    
    def test_order_by_price_descending(self, api_client, active_plan, yearly_plan):
        """Should order plans by price descending."""
        url = reverse('subscriptions:v1-plans-list')
        
        response = api_client.get(url, {'ordering': '-base_price'})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Yearly (999) should come before Premium (99)
        assert data['results'][0]['base_price'] > data['results'][1]['base_price']


# ============================================================================
# RESPONSE STRUCTURE TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingResponseStructure:
    """Test response structure and data format."""
    
    def test_response_has_required_fields(self, api_client, active_plan):
        """Response should include all required fields."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan = data['results'][0]
        required_fields = [
            'id', 'name', 'description', 'price', 'currency', 
            'base_price_usd', 'base_price', 'billing_period', 
            'billing_period_display', 'trial_days', 'is_featured',
            'features', 'limits'
        ]
        
        for field in required_fields:
            assert field in plan, f"Missing required field: {field}"
    
    def test_feature_structure(self, api_client, active_plan):
        """Features should have correct structure."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        feature = data['results'][0]['features'][0]
        required_fields = ['id', 'key', 'name', 'description', 'icon', 'category']
        
        for field in required_fields:
            assert field in feature, f"Missing required feature field: {field}"
    
    def test_pagination_structure(self, api_client, active_plan, yearly_plan):
        """Response should include pagination metadata."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check pagination fields
        assert 'count' in data
        assert 'next' in data
        assert 'previous' in data
        assert 'results' in data
        
        assert data['count'] == 2
        assert isinstance(data['results'], list)


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

@pytest.mark.django_db
class TestPublicPricingEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_multiple_currency_conversions_for_multiple_plans(self, api_client, 
                                                               active_plan, yearly_plan, 
                                                               exchange_rates):
        """Should convert all plans to requested currency."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url, {'currency': 'NGN'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All plans should be in NGN
        for plan in data['results']:
            assert plan['currency'] == 'NGN'
            assert plan['price'] > plan['base_price_usd']  # NGN rate > 1
    
    def test_plan_with_no_features(self, api_client, yearly_plan):
        """Should handle plans with no features."""
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': yearly_plan.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'features' in data
        assert isinstance(data['features'], list)
        assert len(data['features']) == 0
    
    def test_plan_with_zero_price(self, api_client, db):
        """Should handle free plans (zero price)."""
        free_plan = SubscriptionPlan.objects.create(
            name='Free Plan',
            slug='free',
            description='Free forever',
            base_price=Decimal('0.00'),
            billing_period='monthly',
            is_active=True
        )
        
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': free_plan.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['price'] == 0.00
        assert data['base_price'] == 0.00
    
    def test_currency_conversion_with_zero_price(self, api_client, db, exchange_rates):
        """Should handle currency conversion for free plans."""
        free_plan = SubscriptionPlan.objects.create(
            name='Free Plan',
            slug='free',
            description='Free forever',
            base_price=Decimal('0.00'),
            billing_period='monthly',
            is_active=True
        )
        
        url = reverse('subscriptions:v1-plans-detail', kwargs={'pk': free_plan.id})
        response = api_client.get(url, {'currency': 'NGN'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['price'] == 0.00
        assert data['currency'] == 'NGN'
    
    def test_combined_filters(self, api_client, active_plan, yearly_plan):
        """Should handle multiple filters simultaneously."""
        url = reverse('subscriptions:v1-plans-list')
        response = api_client.get(url, {
            'billing_period': 'monthly',
            'is_featured': 'true',
            'ordering': 'base_price'
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should match only the monthly featured plan
        assert data['count'] == 1
        assert data['results'][0]['billing_period'] == 'monthly'
        assert data['results'][0]['is_featured'] is True
