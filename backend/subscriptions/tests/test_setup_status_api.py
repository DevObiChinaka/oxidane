"""
Tests for Setup Status API (Task 0.5.32)

Tests GET /api/admin/setup/status/ endpoint that provides comprehensive
platform configuration status overview for administrators.

Phase 0.5, Task 0.5.32
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from subscriptions.models import (
    TelegramConfiguration, PaymentConfiguration, EmailConfiguration,
    SubscriptionPlan, Feature, TelegramGroup
)

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create admin user for testing."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )


@pytest.fixture
def regular_user(db):
    """Create regular user for testing."""
    return User.objects.create_user(
        username='regularuser',
        email='user@test.com',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def telegram_config(db):
    """Get or create TelegramConfiguration singleton."""
    return TelegramConfiguration.get_instance()


@pytest.fixture
def payment_config(db):
    """Get or create PaymentConfiguration singleton."""
    return PaymentConfiguration.get_instance()


@pytest.fixture
def email_config(db):
    """Get or create EmailConfiguration singleton."""
    return EmailConfiguration.get_instance()


# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

@pytest.mark.django_db
class TestSetupStatusAccessControl:
    """Test access control for setup status endpoint."""
    
    def test_unauthenticated_user_cannot_access(self, api_client):
        """Unauthenticated users should be denied access."""
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_access(self, api_client, regular_user):
        """Regular users should be denied access (admin only)."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access(self, api_client, admin_user):
        """Admin users should have access."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# STATUS CHECKS TESTS
# ============================================================================

@pytest.mark.django_db
class TestSetupStatusChecks:
    """Test status check logic for different components."""
    
    def test_empty_configuration_status(self, api_client, admin_user, 
                                       telegram_config, payment_config, email_config):
        """Test status when all configurations are empty/default."""
        # Clear all configurations
        telegram_config.bot_token = ''
        telegram_config.is_enabled = False
        telegram_config.save()
        
        payment_config.paystack_secret_key = ''
        payment_config.stripe_secret_key = ''
        payment_config.save()
        
        email_config.smtp_host = ''
        email_config.smtp_username = ''
        email_config.smtp_password = ''
        email_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check structure
        assert 'setup_complete' in data
        assert 'completion_percentage' in data
        assert 'components' in data
        assert 'recommendations' in data
        assert 'summary' in data
        
        # Should not be complete
        assert data['setup_complete'] is False
        assert data['completion_percentage'] < 100
        
        # Check components
        assert 'telegram' in data['components']
        assert 'payment' in data['components']
        assert 'email' in data['components']
        assert 'database' in data['components']
        
        # None should be configured
        assert data['components']['telegram']['configured'] is False
        assert data['components']['payment']['configured'] is False
        assert data['components']['email']['configured'] is False
        
        # Should have recommendations
        assert len(data['recommendations']) > 0
    
    def test_telegram_configured_status(self, api_client, admin_user, telegram_config):
        """Test status when Telegram is configured."""
        telegram_config.bot_token = 'test_token_123'
        telegram_config.bot_username = '@test_bot'  # Must start with @
        telegram_config.is_enabled = True
        telegram_config.is_connected = True
        telegram_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        telegram_status = data['components']['telegram']
        assert telegram_status['configured'] is True
        assert telegram_status['healthy'] is True
        assert telegram_status['has_token'] is True
        assert telegram_status['has_username'] is True
        assert telegram_status['connection_status'] == 'connected'
    
    def test_payment_paystack_configured(self, api_client, admin_user, payment_config):
        """Test status when Paystack is configured."""
        payment_config.paystack_secret_key = 'sk_test_123'
        payment_config.paystack_public_key = 'pk_test_123'
        payment_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        payment_status = data['components']['payment']
        assert payment_status['configured'] is True
        assert payment_status['paystack_configured'] is True
        assert payment_status['stripe_configured'] is False
    
    def test_payment_stripe_configured(self, api_client, admin_user, payment_config):
        """Test status when Stripe is configured."""
        payment_config.stripe_secret_key = 'sk_test_456'
        payment_config.stripe_publishable_key = 'pk_test_456'
        payment_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        payment_status = data['components']['payment']
        assert payment_status['configured'] is True
        assert payment_status['paystack_configured'] is False
        assert payment_status['stripe_configured'] is True
    
    def test_payment_both_gateways_configured(self, api_client, admin_user, payment_config):
        """Test status when both payment gateways are configured."""
        payment_config.paystack_secret_key = 'sk_test_123'
        payment_config.stripe_secret_key = 'sk_test_456'
        payment_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        payment_status = data['components']['payment']
        assert payment_status['configured'] is True
        assert payment_status['paystack_configured'] is True
        assert payment_status['stripe_configured'] is True
    
    def test_email_configured_status(self, api_client, admin_user, email_config):
        """Test status when email is configured."""
        email_config.smtp_host = 'smtp.test.com'
        email_config.smtp_port = 587
        email_config.smtp_username = 'test@test.com'
        email_config.smtp_password = 'test_password'
        email_config.from_email = 'noreply@test.com'
        email_config.is_enabled = True
        email_config.is_connected = True
        email_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        email_status = data['components']['email']
        assert email_status['configured'] is True
        assert email_status['enabled'] is True
        assert email_status['has_host'] is True
        assert email_status['has_credentials'] is True
        assert email_status['connection_status'] == 'connected'
    
    def test_database_status_with_plans(self, api_client, admin_user, db):
        """Test database status when plans exist."""
        # Create subscription plan
        plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            base_price=10.00,
            billing_period='monthly',
            is_active=True
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        db_status = data['components']['database']
        assert db_status['has_active_plans'] is True
        assert db_status['plans_count'] >= 1
        assert db_status['ready'] is True
    
    def test_database_status_with_features(self, api_client, admin_user, db):
        """Test database status when features exist."""
        # Create feature
        feature = Feature.objects.create(
            key='test_feature',
            name='Test Feature',
            description='Test feature description',
            category='signals'
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        db_status = data['components']['database']
        assert db_status['features_count'] >= 1
    
    def test_database_status_with_groups(self, api_client, admin_user, db):
        """Test database status when Telegram groups exist."""
        # Create Telegram group
        group = TelegramGroup.objects.create(
            name='Test Group',
            chat_id='-1001234567890',
            group_key='test-group',
            invite_link='https://t.me/test',
            is_active=True
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        db_status = data['components']['database']
        assert db_status['active_groups_count'] >= 1


# ============================================================================
# COMPLETION CALCULATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestSetupCompletion:
    """Test setup completion percentage calculation."""
    
    def test_zero_percent_completion(self, api_client, admin_user,
                                     telegram_config, payment_config, email_config):
        """Test 0% completion when nothing is configured."""
        # Clear all configurations
        telegram_config.bot_token = ''
        telegram_config.is_enabled = False
        telegram_config.save()
        
        payment_config.paystack_secret_key = ''
        payment_config.stripe_secret_key = ''
        payment_config.save()
        
        email_config.smtp_host = ''
        email_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['completion_percentage'] == 0
        assert data['setup_complete'] is False
        assert data['summary']['completed_checks'] == 0
    
    def test_partial_completion(self, api_client, admin_user,
                               telegram_config, payment_config, email_config, db):
        """Test partial completion (e.g., 50%)."""
        # Configure only Telegram and Payment
        telegram_config.bot_token = 'test_token'
        telegram_config.is_enabled = True
        telegram_config.save()
        
        payment_config.paystack_secret_key = 'sk_test_123'
        payment_config.save()
        
        # Leave email unconfigured
        email_config.smtp_host = ''
        email_config.save()
        
        # No plans
        SubscriptionPlan.objects.all().delete()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['completion_percentage'] == 50  # 2 out of 4 checks
        assert data['setup_complete'] is False
        assert data['summary']['completed_checks'] == 2
        assert data['summary']['pending_checks'] == 2
    
    def test_full_completion(self, api_client, admin_user,
                            telegram_config, payment_config, email_config, db):
        """Test 100% completion when everything is configured."""
        # Configure Telegram
        telegram_config.bot_token = 'test_token'
        telegram_config.is_enabled = True
        telegram_config.save()
        
        # Configure Payment
        payment_config.paystack_secret_key = 'sk_test_123'
        payment_config.save()
        
        # Configure Email
        email_config.smtp_host = 'smtp.test.com'
        email_config.smtp_port = 587
        email_config.smtp_username = 'test@test.com'
        email_config.smtp_password = 'password'
        email_config.from_email = 'noreply@test.com'
        email_config.save()
        
        # Create plan
        SubscriptionPlan.objects.create(
            name='Test Plan',
            base_price=10.00,
            billing_period='monthly',
            is_active=True
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['completion_percentage'] == 100
        assert data['setup_complete'] is True
        assert data['summary']['completed_checks'] == 4
        assert data['summary']['pending_checks'] == 0


# ============================================================================
# RECOMMENDATIONS TESTS
# ============================================================================

@pytest.mark.django_db
class TestSetupRecommendations:
    """Test recommendation generation for incomplete setup."""
    
    def test_recommendations_for_unconfigured_telegram(self, api_client, admin_user,
                                                       telegram_config):
        """Test recommendations when Telegram is not configured."""
        telegram_config.bot_token = ''
        telegram_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have Telegram recommendation
        telegram_recs = [r for r in data['recommendations'] if r['component'] == 'telegram']
        assert len(telegram_recs) > 0
        assert 'telegram' in telegram_recs[0]['message'].lower()
    
    def test_recommendations_for_unconfigured_payment(self, api_client, admin_user,
                                                      payment_config):
        """Test recommendations when Payment is not configured."""
        payment_config.paystack_secret_key = ''
        payment_config.stripe_secret_key = ''
        payment_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have Payment recommendation
        payment_recs = [r for r in data['recommendations'] if r['component'] == 'payment']
        assert len(payment_recs) > 0
        assert 'payment gateway' in payment_recs[0]['message'].lower()
    
    def test_recommendations_for_unconfigured_email(self, api_client, admin_user,
                                                    email_config):
        """Test recommendations when Email is not configured."""
        email_config.smtp_host = ''
        email_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have Email recommendation
        email_recs = [r for r in data['recommendations'] if r['component'] == 'email']
        assert len(email_recs) > 0
        assert 'smtp' in email_recs[0]['message'].lower()
    
    def test_recommendations_for_missing_plans(self, api_client, admin_user, db):
        """Test recommendations when no subscription plans exist."""
        SubscriptionPlan.objects.all().delete()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have database/plans recommendation
        db_recs = [r for r in data['recommendations'] if r['component'] == 'database']
        plan_recs = [r for r in db_recs if 'plan' in r['message'].lower()]
        assert len(plan_recs) > 0
    
    def test_recommendations_for_missing_features(self, api_client, admin_user, db):
        """Test recommendations when no features exist."""
        Feature.objects.all().delete()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have database/features recommendation
        db_recs = [r for r in data['recommendations'] if r['component'] == 'database']
        feature_recs = [r for r in db_recs if 'feature' in r['message'].lower()]
        assert len(feature_recs) > 0
    
    def test_no_recommendations_when_complete(self, api_client, admin_user,
                                             telegram_config, payment_config, 
                                             email_config, db):
        """Test minimal recommendations when core setup is complete."""
        # Configure everything
        telegram_config.bot_token = 'test_token'
        telegram_config.is_enabled = True
        telegram_config.save()
        
        payment_config.paystack_secret_key = 'sk_test_123'
        payment_config.save()
        
        email_config.smtp_host = 'smtp.test.com'
        email_config.smtp_port = 587
        email_config.smtp_username = 'test@test.com'
        email_config.smtp_password = 'password'
        email_config.from_email = 'noreply@test.com'
        email_config.save()
        
        SubscriptionPlan.objects.create(
            name='Test Plan',
            base_price=10.00,
            billing_period='monthly',
            is_active=True
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Setup should be marked complete (4 core checks passed)
        assert data['setup_complete'] is True
        assert data['completion_percentage'] == 100
        # May have optional recommendations (e.g., features), but no critical ones
        critical_recs = [r for r in data['recommendations'] 
                        if r['component'] in ['telegram', 'payment', 'email']]
        assert len(critical_recs) == 0


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

@pytest.mark.django_db
class TestSetupStatusEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_telegram_enabled_but_no_token(self, api_client, admin_user, telegram_config):
        """Test Telegram status when enabled but missing token."""
        telegram_config.is_enabled = True
        telegram_config.bot_token = ''
        telegram_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        telegram_status = data['components']['telegram']
        assert telegram_status['configured'] is False
        assert telegram_status['has_token'] is False
    
    def test_email_has_host_but_no_credentials(self, api_client, admin_user, email_config):
        """Test email status when host is set but credentials missing."""
        email_config.smtp_host = 'smtp.test.com'
        email_config.smtp_username = ''
        email_config.smtp_password = ''
        email_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        email_status = data['components']['email']
        assert email_status['configured'] is False
        assert email_status['has_host'] is True
        assert email_status['has_credentials'] is False
    
    def test_inactive_plans_not_counted(self, api_client, admin_user, db):
        """Test that inactive plans are not counted in database status."""
        # Create only inactive plans
        SubscriptionPlan.objects.create(
            name='Inactive Plan',
            base_price=10.00,
            billing_period='monthly',
            is_active=False
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        db_status = data['components']['database']
        assert db_status['has_active_plans'] is False
        assert db_status['plans_count'] == 0  # Only active plans counted
    
    def test_inactive_groups_not_counted(self, api_client, admin_user, db):
        """Test that inactive Telegram groups are not counted."""
        # Create only inactive groups
        TelegramGroup.objects.create(
            name='Inactive Group',
            chat_id='-1001234567890',
            group_key='inactive-group',
            is_active=False
        )
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        db_status = data['components']['database']
        assert db_status['active_groups_count'] == 0  # Only active groups counted
    
    def test_payment_test_mode_flag(self, api_client, admin_user, payment_config):
        """Test that payment test_mode flag is included in status."""
        payment_config.is_test_mode = True
        payment_config.paystack_secret_key = 'sk_test_123'
        payment_config.save()
        
        api_client.force_authenticate(user=admin_user)
        url = reverse('subscriptions:setup-status-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        payment_status = data['components']['payment']
        assert payment_status['test_mode'] is True
