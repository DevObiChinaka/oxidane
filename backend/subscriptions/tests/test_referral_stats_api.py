"""
Tests for Referral Stats API (Phase 0.5 - Task 0.5.26)

Tests comprehensive admin statistics endpoint including:
- Access control (admin-only)
- Overview statistics (total referrals, revenue, conversion rate)
- Top referrers ranking
- Trend analysis (7/30/90 days, this month/year)
- Filtering by date range, referrer, status
- Edge cases (no data, invalid filters)
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from subscriptions.models import (
    ReferralCode, Referral, ReferralCredit, SubscriptionPlan, Subscription, BillingProfile
)

User = get_user_model()


# ===========================
# FIXTURES
# ===========================

@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def user(db):
    """Regular user (referrer)"""
    return User.objects.create_user(
        username='referrer',
        email='referrer@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2(db):
    """Second user (another referrer)"""
    return User.objects.create_user(
        username='referrer2',
        email='referrer2@example.com',
        password='testpass123'
    )


@pytest.fixture
def referee(db):
    """User who was referred"""
    return User.objects.create_user(
        username='referee',
        email='referee@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Admin user with staff privileges"""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def referral_code(user):
    """Active referral code"""
    return ReferralCode.objects.create(
        code='TESTREF2025',
        referrer=user,
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('15.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('10.00'),
        max_uses=100,
        is_active=True
    )


@pytest.fixture
def referral_code2(user2):
    """Second referral code"""
    return ReferralCode.objects.create(
        code='REFERRER2',
        referrer=user2,
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('10.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('5.00'),
        max_uses=50,
        is_active=True
    )


@pytest.fixture
def completed_referrals(user, referee, referral_code):
    """Create multiple completed referrals for testing"""
    referrals = []
    for i in range(5):
        ref = Referral.objects.create(
            referral_code=referral_code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('10.00'),
            status='completed'
        )
        referrals.append(ref)
    return referrals


@pytest.fixture
def cancelled_referrals(user, referee, referral_code):
    """Create cancelled referrals"""
    referrals = []
    for i in range(2):
        ref = Referral.objects.create(
            referral_code=referral_code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('10.00'),
            status='cancelled'
        )
        referrals.append(ref)
    return referrals


@pytest.fixture
def referral_credits(user, completed_referrals):
    """Create referral credits"""
    credits = []
    for ref in completed_referrals[:2]:
        credit = ReferralCredit.objects.create(
            user=user,
            credit_percentage=Decimal('5.00'),
            earned_from_referral=ref
        )
        credits.append(credit)
    return credits


# ===========================
# ACCESS CONTROL TESTS
# ===========================

@pytest.mark.django_db
class TestReferralStatsAccessControl:
    """Test access control for referral stats API"""
    
    def test_unauthenticated_cannot_access_stats(self, api_client):
        """Unauthenticated users cannot access referral stats"""
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_access_stats(self, api_client, user):
        """Regular users (non-admin) cannot access referral stats"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access_stats(self, api_client, admin_user):
        """Admin users can access referral stats"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'overview' in response.data
        assert 'top_referrers' in response.data
        assert 'trends' in response.data


# ===========================
# OVERVIEW STATISTICS TESTS
# ===========================

@pytest.mark.django_db
class TestReferralStatsOverview:
    """Test overview statistics calculation"""
    
    def test_empty_stats(self, api_client, admin_user):
        """Stats work with no referrals"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 0
        assert response.data['overview']['completed_referrals'] == 0
        assert response.data['overview']['cancelled_referrals'] == 0
        assert response.data['overview']['conversion_rate'] == 0.0
    
    def test_total_referrals_count(
        self, api_client, admin_user, completed_referrals, cancelled_referrals
    ):
        """Total referrals count is correct"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 7  # 5 + 2
        assert response.data['overview']['completed_referrals'] == 5
        assert response.data['overview']['cancelled_referrals'] == 2
    
    def test_conversion_rate_calculation(
        self, api_client, admin_user, completed_referrals, cancelled_referrals
    ):
        """Conversion rate is calculated correctly"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        # 5 completed out of 7 total = 71.43%
        assert response.data['overview']['conversion_rate'] == 71.43
    
    def test_total_revenue_calculation(self, api_client, admin_user, completed_referrals):
        """Total revenue from completed referrals is calculated"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        # 5 referrals * $90 (after 10% discount) = $450
        total_revenue = Decimal(response.data['overview']['total_revenue_generated'])
        assert total_revenue == Decimal('450.00')
    
    def test_average_discount_calculation(self, api_client, admin_user, completed_referrals):
        """Average discount given to referees is calculated"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        # All referrals have $10 discount (10% of $100)
        avg_discount = Decimal(response.data['overview']['average_discount_given'])
        assert avg_discount == Decimal('10.00')
    
    def test_credits_awarded_count(self, api_client, admin_user, referral_credits):
        """Total credits awarded is counted"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_credits_awarded'] == 2
        assert response.data['overview']['total_credits_used'] == 0
    
    def test_credits_used_count(self, api_client, admin_user, user, referral_credits):
        """Used credits are counted separately"""
        # Create a subscription to use the credit on
        plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            base_price=Decimal('100.00'),
            billing_period='monthly'
        )
        billing_profile = BillingProfile.objects.get(user=user)
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('100.00')
        )
        
        # Mark first credit as used with subscription using the method
        referral_credits[0].use_credit(subscription)
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_credits_awarded'] == 2
        assert response.data['overview']['total_credits_used'] == 1


# ===========================
# TOP REFERRERS TESTS
# ===========================

@pytest.mark.django_db
class TestReferralStatsTopReferrers:
    """Test top referrers ranking"""
    
    def test_top_referrers_empty(self, api_client, admin_user):
        """Top referrers list is empty when no referrals"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['top_referrers'] == []
    
    def test_top_referrers_single_user(
        self, api_client, admin_user, user, completed_referrals
    ):
        """Top referrers shows single user correctly"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['top_referrers']) == 1
        
        top = response.data['top_referrers'][0]
        assert top['username'] == user.username
        assert top['email'] == user.email
        assert top['total_referrals'] == 5
        assert top['completed_referrals'] == 5
        assert Decimal(top['total_revenue']) == Decimal('450.00')
    
    def test_top_referrers_multiple_users(
        self, api_client, admin_user, user, user2, referee, 
        referral_code, referral_code2
    ):
        """Top referrers ranks multiple users by completed referrals"""
        # User1: 3 completed
        for _ in range(3):
            Referral.objects.create(
                referral_code=referral_code,
                referrer=user,
                referee=referee,
                original_amount=Decimal('100.00'),
                referee_discount_percent=Decimal('10.00'),
                status='completed'
            )
        
        # User2: 5 completed (should rank higher)
        for _ in range(5):
            Referral.objects.create(
                referral_code=referral_code2,
                referrer=user2,
                referee=referee,
                original_amount=Decimal('100.00'),
                referee_discount_percent=Decimal('5.00'),
                status='completed'
            )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['top_referrers']) == 2
        
        # User2 should be first (5 referrals)
        assert response.data['top_referrers'][0]['username'] == user2.username
        assert response.data['top_referrers'][0]['completed_referrals'] == 5
        
        # User1 should be second (3 referrals)
        assert response.data['top_referrers'][1]['username'] == user.username
        assert response.data['top_referrers'][1]['completed_referrals'] == 3
    
    def test_top_referrers_credits_tracking(
        self, api_client, admin_user, user, completed_referrals, referral_credits
    ):
        """Top referrers includes credits earned and used"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        top = response.data['top_referrers'][0]
        assert top['credits_earned'] == 2
        assert top['credits_used'] == 0


# ===========================
# TRENDS TESTS
# ===========================

@pytest.mark.django_db(transaction=True)
class TestReferralStatsTrends:
    """Test trend analysis over time"""
    
    def test_trends_last_7_days(self, db, api_client, admin_user):
        """Trends correctly count last 7 days"""
        # Create fresh users and code for this test
        user = User.objects.create_user(username='trenduser1', email='trend1@test.com', password='test')
        referee = User.objects.create_user(username='trendreferee1', email='ref1@test.com', password='test')
        code = ReferralCode.objects.create(
            code='TREND1',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('5.00')
        )
        
        now = timezone.now()
        
        # Create referrals and manually set conversion_date (auto_now_add prevents direct setting)
        ref1 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=ref1.id).update(conversion_date=now - timedelta(days=3))
        
        ref2 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=ref2.id).update(conversion_date=now - timedelta(days=10))
        
        api_client.force_authenticate(user=admin_user)
        # Filter by this specific referrer to isolate
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'referrer_id': str(user.id)}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['trends']['last_7_days'] == 1  # Only one within 7 days
    
    def test_trends_last_30_days(self, db, api_client, admin_user):
        """Trends correctly count last 30 days"""
        # Create fresh users and code for this test
        user = User.objects.create_user(username='trenduser2', email='trend2@test.com', password='test')
        referee = User.objects.create_user(username='trendreferee2', email='ref2@test.com', password='test')
        code = ReferralCode.objects.create(
            code='TREND2',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('5.00')
        )
        
        now = timezone.now()
        
        # Create referrals and manually set conversion_date (auto_now_add prevents direct setting)
        for days_ago in [5, 15, 25, 35]:
            ref = Referral.objects.create(
                referral_code=code,
                referrer=user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
            Referral.objects.filter(id=ref.id).update(conversion_date=now - timedelta(days=days_ago))
        
        api_client.force_authenticate(user=admin_user)
        # Filter by this specific referrer to isolate
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'referrer_id': str(user.id)}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['trends']['last_30_days'] == 3  # 5, 15, 25 days ago
        assert response.data['trends']['last_90_days'] == 4  # All 4
    
    def test_trends_this_month(self, db, api_client, admin_user):
        """Trends correctly count this month"""
        # Create fresh users and code for this test
        user = User.objects.create_user(username='trenduser3', email='trend3@test.com', password='test')
        referee = User.objects.create_user(username='trendreferee3', email='ref3@test.com', password='test')
        code = ReferralCode.objects.create(
            code='TREND3',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('5.00')
        )
        
        now = timezone.now()
        
        # This month
        ref1 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        # No need to update - current time is fine
        
        # Last month
        last_month = now - timedelta(days=35)
        ref2 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=ref2.id).update(conversion_date=last_month)
        
        api_client.force_authenticate(user=admin_user)
        # Filter by this specific referrer to isolate
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'referrer_id': str(user.id)}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['trends']['this_month'] == 1


# ===========================
# FILTERING TESTS
# ===========================

@pytest.mark.django_db(transaction=True)
class TestReferralStatsFiltering:
    """Test filtering statistics by various parameters"""
    
    def test_filter_by_date_range(self, db, api_client, admin_user):
        """Can filter referrals by date range"""
        # Create fresh users and code for this test
        user = User.objects.create_user(username='filteruser1', email='filter1@test.com', password='test')
        referee = User.objects.create_user(username='filterreferee1', email='fref1@test.com', password='test')
        code = ReferralCode.objects.create(
            code='FILTER1',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('5.00')
        )
        
        from django.utils.timezone import make_aware
        
        # Create referrals and manually set conversion_date
        old_ref = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=old_ref.id).update(conversion_date=make_aware(datetime(2025, 1, 15)))
        
        new_ref = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=new_ref.id).update(conversion_date=make_aware(datetime(2025, 10, 15)))
        
        api_client.force_authenticate(user=admin_user)
        
        # Filter for October onwards with user filter to isolate
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {
                'start_date': '2025-10-01',
                'referrer_id': str(user.id)
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 1
        assert response.data['filters_applied']['start_date'] == '2025-10-01'
    
    def test_filter_by_end_date(self, db, api_client, admin_user):
        """Can filter referrals by end date"""
        # Create fresh users and code for this test
        user = User.objects.create_user(username='filteruser2', email='filter2@test.com', password='test')
        referee = User.objects.create_user(username='filterreferee2', email='fref2@test.com', password='test')
        code = ReferralCode.objects.create(
            code='FILTER2',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('5.00')
        )
        
        from django.utils.timezone import make_aware
        
        ref1 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=ref1.id).update(conversion_date=make_aware(datetime(2025, 9, 15)))
        
        ref2 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=ref2.id).update(conversion_date=make_aware(datetime(2025, 11, 15)))
        
        api_client.force_authenticate(user=admin_user)
        
        # Filter up to October with user filter to isolate
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {
                'end_date': '2025-10-31',
                'referrer_id': str(user.id)
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 1
    
    def test_filter_by_referrer(
        self, api_client, admin_user, user, user2, referee, 
        referral_code, referral_code2
    ):
        """Can filter statistics by specific referrer"""
        # User1: 2 referrals
        for _ in range(2):
            Referral.objects.create(
                referral_code=referral_code,
                referrer=user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        # User2: 3 referrals
        for _ in range(3):
            Referral.objects.create(
                referral_code=referral_code2,
                referrer=user2,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        api_client.force_authenticate(user=admin_user)
        
        # Filter for user1 only
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'referrer_id': user.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 2
        assert response.data['top_referrers'] == []  # No top referrers when filtering by user
    
    def test_filter_by_status(
        self, api_client, admin_user, completed_referrals, cancelled_referrals
    ):
        """Can filter statistics by referral status"""
        api_client.force_authenticate(user=admin_user)
        
        # Filter for completed only
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'status': 'completed'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 5
        assert response.data['overview']['completed_referrals'] == 5
        assert response.data['overview']['cancelled_referrals'] == 0
    
    def test_combined_filters(self, db, api_client, admin_user):
        """Can combine multiple filters"""
        # Create fresh users and code for this test
        user = User.objects.create_user(username='filteruser3', email='filter3@test.com', password='test')
        referee = User.objects.create_user(username='filterreferee3', email='fref3@test.com', password='test')
        code = ReferralCode.objects.create(
            code='FILTER3',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('5.00')
        )
        
        from django.utils.timezone import make_aware
        
        # Create completed and cancelled referrals in October
        ref1 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        Referral.objects.filter(id=ref1.id).update(conversion_date=make_aware(datetime(2025, 10, 15)))
        
        ref2 = Referral.objects.create(
            referral_code=code,
            referrer=user,
            referee=referee,
            original_amount=Decimal('100.00'),
            status='cancelled'
        )
        Referral.objects.filter(id=ref2.id).update(conversion_date=make_aware(datetime(2025, 10, 20)))
        
        api_client.force_authenticate(user=admin_user)
        
        # Filter for October completed referrals by user
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {
                'start_date': '2025-10-01',
                'end_date': '2025-10-31',
                'referrer_id': str(user.id),
                'status': 'completed'
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 1
        assert response.data['filters_applied']['start_date'] == '2025-10-01'
        assert response.data['filters_applied']['end_date'] == '2025-10-31'
        assert response.data['filters_applied']['status'] == 'completed'


# ===========================
# ERROR HANDLING TESTS
# ===========================

@pytest.mark.django_db
class TestReferralStatsErrorHandling:
    """Test error handling for invalid inputs"""
    
    def test_invalid_start_date_format(self, api_client, admin_user):
        """Invalid start date format returns 400"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'start_date': 'invalid-date'}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'YYYY-MM-DD' in response.data['error']
    
    def test_invalid_end_date_format(self, api_client, admin_user):
        """Invalid end date format returns 400"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'end_date': '2025/11/05'}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'YYYY-MM-DD' in response.data['error']
    
    def test_invalid_referrer_id(self, api_client, admin_user):
        """Non-existent referrer_id returns empty results"""
        import uuid
        api_client.force_authenticate(user=admin_user)
        # Use a valid UUID format that doesn't exist
        fake_uuid = str(uuid.uuid4())
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'referrer_id': fake_uuid}
        )
        
        # Should still return 200 with zero referrals (filters are permissive)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 0
    
    def test_invalid_status(self, api_client, admin_user):
        """Invalid status value returns 400"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(
            '/api/admin/referrals/stats/',
            {'status': 'invalid'}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'completed' in response.data['error']
        assert 'cancelled' in response.data['error']


# ===========================
# EDGE CASES
# ===========================

@pytest.mark.django_db
class TestReferralStatsEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_all_referrals_cancelled(self, api_client, admin_user, cancelled_referrals):
        """Stats work when all referrals are cancelled"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['conversion_rate'] == 0.0
        assert Decimal(response.data['overview']['total_revenue_generated']) == Decimal('0.00')
    
    def test_large_number_of_referrals(
        self, api_client, admin_user, user, referee, referral_code
    ):
        """Stats work with large number of referrals"""
        # Create 100 referrals
        for i in range(100):
            Referral.objects.create(
                referral_code=referral_code,
                referrer=user,
                referee=referee,
                original_amount=Decimal('100.00'),
                referee_discount_percent=Decimal('10.00'),
                status='completed'
            )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overview']['total_referrals'] == 100
        assert Decimal(response.data['overview']['total_revenue_generated']) == Decimal('9000.00')
    
    def test_top_referrers_limit_to_10(
        self, api_client, admin_user, referee, referral_code
    ):
        """Top referrers list is limited to 10"""
        # Create 15 referrers with varying referral counts
        for i in range(15):
            user = User.objects.create_user(
                username=f'referrer{i}',
                email=f'referrer{i}@example.com',
                password='test123'
            )
            code = ReferralCode.objects.create(
                code=f'CODE{i}',
                referrer=user,
                referrer_discount_type='percentage',
                referrer_discount_value=Decimal('10.00'),
                referee_discount_type='percentage',
                referee_discount_value=Decimal('5.00')
            )
            # Create i+1 referrals for each
            for j in range(i + 1):
                Referral.objects.create(
                    referral_code=code,
                    referrer=user,
                    referee=referee,
                    original_amount=Decimal('100.00'),
                    status='completed'
                )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/referrals/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['top_referrers']) == 10  # Limited to 10
        # Should be sorted by completed referrals (highest first)
        assert response.data['top_referrers'][0]['completed_referrals'] > \
               response.data['top_referrers'][-1]['completed_referrals']
