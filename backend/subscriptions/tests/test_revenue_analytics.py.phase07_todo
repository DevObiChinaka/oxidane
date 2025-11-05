from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal
from datetime import datetime, timedelta
from subscriptions.models import (
    PricingPlan, SignalSubscription, PaymentTransaction, Coupon, SubscriptionPlan
)

User = get_user_model()

class RevenueAnalyticsTestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test pricing plans
        self.plan1 = PricingPlan.objects.create(
            plan_type='signals_monthly',
            name='Monthly Signals',
            price=Decimal('99.99'),
            currency='USD',
            is_active=True
        )
        
        self.plan2 = PricingPlan.objects.create(
            plan_type='mentorship_basic',
            name='Basic Mentorship',
            price=Decimal('199.99'),
            currency='USD',
            is_active=True
        )
        
        today = timezone.now()
        
        # Create test coupon
        self.coupon = Coupon.objects.create(
            code='TEST20',
            description='Test coupon for revenue analytics tests',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=today - timedelta(days=30),
            valid_until=today + timedelta(days=30),
            is_active=True,
            max_uses=None,
            max_uses_per_user=1
        )
        
        # Create test transactions and subscriptions
        self._create_test_data()
    
    def _create_test_data(self):
        """Create a set of test transactions and subscriptions"""
        # Create transactions from the last 60 days
        today = timezone.now()
        
        # Regular subscriptions
        for i in range(5):
            subscription = SignalSubscription.objects.create(
                user=self.user,
                pricing_plan=self.plan1,
                plan_type=self.plan1.plan_type,
                paystack_reference=f'TEST_REF_{i}',
                amount_paid=self.plan1.price,
                telegram_username='test_user',
                subscription_start=today - timedelta(days=30),
                subscription_end=today + timedelta(days=30),
                payment_status='verified'
            )
            PaymentTransaction.objects.create(
                user=self.user,
                amount=self.plan1.price,
                signal_subscription=subscription,
                status='completed',
                created_at=today - timedelta(days=i)
            )
        
        # Discounted subscriptions with coupon
        for i in range(3):
            discounted_amount = self.plan2.price * (1 - self.coupon.discount_percentage/100)
            subscription = SignalSubscription.objects.create(
                user=self.user,
                pricing_plan=self.plan2,
                plan_type=self.plan2.plan_type,
                paystack_reference=f'TEST_REF_DISC_{i}',
                amount_paid=discounted_amount,
                telegram_username='test_user',
                subscription_start=today - timedelta(days=15),
                subscription_end=today + timedelta(days=45),
                payment_status='verified',
                coupon_used=self.coupon,
                original_amount=self.plan2.price,
                discount_amount=self.plan2.price * Decimal('0.20')  # 20% discount
            )
            PaymentTransaction.objects.create(
                user=self.user,
                amount=discounted_amount,
                signal_subscription=subscription,
                status='completed',
                created_at=today - timedelta(days=i+10)
            )
        
        # Add one refunded transaction
        refund_subscription = SignalSubscription.objects.create(
            user=self.user,
            pricing_plan=self.plan1,
            plan_type=self.plan1.plan_type,
            paystack_reference='TEST_REF_REFUND',
            amount_paid=self.plan1.price,
            telegram_username='test_user',
            subscription_start=today - timedelta(days=20),
            subscription_end=today - timedelta(days=19),
            payment_status='refunded'
        )
        PaymentTransaction.objects.create(
            user=self.user,
            amount=self.plan1.price,
            signal_subscription=refund_subscription,
            status='completed',
            refund_status='refunded',
            created_at=today - timedelta(days=20)
        )

    def test_revenue_analytics_endpoint(self):
        """Test the revenue analytics endpoint returns correct data"""
        url = '/api/subscriptions/revenue/analytics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Calculate expected values
        expected_total = (
            5 * float(self.plan1.price) +  # Regular subscriptions
            3 * float(self.plan2.price * (1 - self.coupon.discount_percentage/100))  # Discounted subscriptions
        )
        
        # Test basic metrics
        self.assertEqual(data['total_revenue'], expected_total)
        self.assertEqual(data['active_subscriptions'], 8)  # 5 regular + 3 discounted
        
        # Test coupon impact
        total_discount = 3 * float(self.plan2.price * (self.coupon.discount_percentage/100))
        self.assertEqual(data['coupon_discount_impact'], -total_discount)
        
        # Test revenue breakdown
        self.assertTrue('revenue_breakdown' in data)
        breakdown = data['revenue_breakdown']
        self.assertEqual(
            breakdown['signals_monthly'],
            5 * float(self.plan1.price)
        )
        self.assertEqual(
            breakdown['mentorship_basic'],
            3 * float(self.plan2.price * (1 - self.coupon.discount_percentage/100))
        )
    
    def test_date_range_filtering(self):
        """Test that date range filtering works correctly"""
        today = timezone.now().date()
        url = f'/api/subscriptions/revenue/analytics/?start_date={today - timedelta(days=7)}&end_date={today}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only include transactions from last 7 days
        self.assertTrue(data['total_revenue'] > 0)
        self.assertTrue(data['total_revenue'] < (5 * float(self.plan1.price) + 3 * float(self.plan2.price)))
    
    def test_refund_tracking(self):
        """Test that refunds are properly tracked"""
        url = '/api/subscriptions/revenue/analytics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify refund data
        self.assertTrue('refunds' in data)
        self.assertEqual(data['refunds']['count'], 1)
        self.assertEqual(float(data['refunds']['total']), float(self.plan1.price))