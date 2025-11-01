from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import admin_views
from .pricing_views import PricingPlanViewSet, CouponCodeViewSet
from . import billing_views
from .user_subscription_views import UserSubscriptionViewSet
from . import mentorship_admin_views

app_name = 'subscriptions'

# API Router for pricing management
router = DefaultRouter()
router.register(r'pricing/plans', PricingPlanViewSet, basename='pricing-plans')
router.register(r'pricing/coupons', CouponCodeViewSet, basename='coupon-codes')

# User subscription management router
user_router = DefaultRouter()
user_router.register(r'subscriptions', UserSubscriptionViewSet, basename='user-subscriptions')

urlpatterns = [
    # Admin API endpoints for pricing management
    path('admin/', include(router.urls)),
    
    # User subscription management API
    path('', include(user_router.urls)),
    
    # ============================================================================
    # BILLING & TELEGRAM VERIFICATION ENDPOINTS
    # ============================================================================
    
    # Telegram Verification (User-facing)
    path('billing/telegram/generate-code/', billing_views.generate_verification_code, name='generate_verification_code'),
    path('billing/telegram/status/', billing_views.telegram_verification_status, name='telegram_verification_status'),
    path('billing/telegram/unlink/', billing_views.unlink_telegram, name='unlink_telegram'),
    
    # Telegram Verification Callback (Bot-only, uses X-Bot-Secret header)
    path('billing/telegram/verify-callback/', billing_views.telegram_verify_callback, name='telegram_verify_callback'),
    
    # ============================================================================
    # ADMIN ENDPOINTS
    # ============================================================================
    
    # Dashboard and Analytics
    path('admin/dashboard/', admin_views.admin_pricing_dashboard, name='admin_dashboard'),
    path('admin/analytics/', admin_views.subscription_analytics, name='subscription_analytics'),
    
    # Enhanced Analytics (Task 1.2)
    path('admin/analytics/dashboard/', admin_views.subscription_analytics_dashboard, name='analytics_dashboard'),
    path('admin/performance/metrics/', admin_views.performance_metrics_dashboard, name='performance_metrics'),
    path('admin/revenue/analytics/', admin_views.revenue_analytics, name='revenue_analytics'),
    path('admin/revenue/export/', admin_views.export_revenue_report, name='export_revenue_report'),
    
    # Subscription Management (Secure)
    path('admin/subscriptions/', admin_views.subscriptions_list, name='subscriptions_list'),
    path('admin/subscriptions/<uuid:subscription_id>/', admin_views.subscription_detail, name='subscription_detail'),
    
    # Pricing management
    path('admin/pricing/plans/', admin_views.admin_pricing_plans, name='admin_pricing_plans'),
    path('admin/pricing/plans/<uuid:plan_id>/', admin_views.admin_pricing_plan_detail, name='admin_pricing_plan_detail'),
    
    # Legacy endpoints (to be updated)
    path('admin/subscriptions/legacy/', admin_views.admin_subscriptions, name='admin_subscriptions_legacy'),
    path('admin/subscriptions/<uuid:subscription_id>/verify/', admin_views.admin_verify_payment, name='admin_verify_payment'),
    
    # Telegram management  
    path('admin/telegram/queue/', admin_views.admin_telegram_queue, name='admin_telegram_queue'),
    path('admin/telegram/tasks/<uuid:task_id>/action/', admin_views.admin_telegram_action, name='admin_telegram_action'),
    
    # Payment transactions
    path('admin/transactions/', admin_views.admin_payment_transactions, name='admin_payment_transactions'),
    
    # ============================================================================
    # MENTORSHIP ADMIN ENDPOINTS
    # ============================================================================
    
    # Mentorship Subscription Management
    path('admin/mentorship/subscriptions/', mentorship_admin_views.mentorship_subscription_list, name='mentorship_subscriptions'),
    path('admin/mentorship/extend/<uuid:subscription_id>/', mentorship_admin_views.extend_subscription, name='extend_mentorship_subscription'),
    
    # Mentorship Session Management
    path('admin/mentorship/sessions/', mentorship_admin_views.mentorship_session_management, name='mentorship_sessions'),
    
    # Mentorship Analytics
    path('admin/mentorship/analytics/', mentorship_admin_views.mentorship_analytics, name='mentorship_analytics'),
]