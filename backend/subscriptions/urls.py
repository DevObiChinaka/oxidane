from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from . import admin_views  # DEPRECATED: Phase 0.4 admin views - will be rewritten for Phase 0.6
from .pricing_views import PricingPlanViewSet, CouponViewSet
from . import billing_views
from .user_subscription_views import UserSubscriptionViewSet
from . import mentorship_admin_views
from .api_views import (
    SubscriptionViewSet, SubscriptionPlanViewSet, FeatureViewSet, 
    CouponViewSet as APICouponViewSet, ReferralCodeViewSet, ReferralStatsViewSet,
    TelegramConfigurationViewSet, TelegramGroupViewSet, PaymentConfigurationViewSet,
    EmailConfigurationViewSet
)  # Phase 0.5 - Tasks 0.5.20-0.5.30

app_name = 'subscriptions'

# API Router for pricing management
router = DefaultRouter()
router.register(r'pricing/plans', PricingPlanViewSet, basename='pricing-plans')
router.register(r'pricing/coupons', CouponViewSet, basename='coupon-codes')

# User subscription management router
user_router = DefaultRouter()
user_router.register(r'subscriptions', UserSubscriptionViewSet, basename='user-subscriptions')

# NEW: Phase 0.5 - Tasks 0.5.20-0.5.30 - Subscription, Plan, Feature, Coupon, Referral, Telegram, Payment, Email Config API endpoints
api_router = DefaultRouter()
api_router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
api_router.register(r'plans', SubscriptionPlanViewSet, basename='plan')
api_router.register(r'features', FeatureViewSet, basename='feature')
api_router.register(r'coupons', APICouponViewSet, basename='coupon')
api_router.register(r'referrals/codes', ReferralCodeViewSet, basename='referral-code')
api_router.register(r'admin/referrals/stats', ReferralStatsViewSet, basename='referral-stats')
api_router.register(r'admin/telegram/config', TelegramConfigurationViewSet, basename='telegram-config')
api_router.register(r'admin/telegram/groups', TelegramGroupViewSet, basename='telegram-group')
api_router.register(r'admin/payment/config', PaymentConfigurationViewSet, basename='payment-config')
api_router.register(r'admin/email/config', EmailConfigurationViewSet, basename='email-config')

urlpatterns = [
    # Admin API endpoints for pricing management
    path('admin/', include(router.urls)),
    
    # NEW: Phase 0.5 - Task 0.5.20 - Comprehensive subscription API
    # Note: Already prefixed with 'api/' in main urls.py, so this becomes /api/subscriptions/
    path('', include(api_router.urls)),
    
    # User subscription management API (legacy, will be deprecated)
    # path('', include(user_router.urls)),  # Temporarily disabled to avoid conflicts
    
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
    # ADMIN ENDPOINTS - DEPRECATED (Phase 0.4)
    # ============================================================================
    # TODO Phase 0.6: Rewrite admin endpoints using Phase 0.5 models
    # These endpoints are temporarily disabled during Phase 0.5 model migration
    
    # # Dashboard and Analytics
    # path('admin/dashboard/', admin_views.admin_pricing_dashboard, name='admin_dashboard'),
    # path('admin/analytics/', admin_views.subscription_analytics, name='subscription_analytics'),
    # 
    # # Enhanced Analytics (Task 1.2)
    # path('admin/analytics/dashboard/', admin_views.subscription_analytics_dashboard, name='analytics_dashboard'),
    # path('admin/performance/metrics/', admin_views.performance_metrics_dashboard, name='performance_metrics'),
    # path('admin/revenue/analytics/', admin_views.revenue_analytics, name='revenue_analytics'),
    # path('admin/revenue/export/', admin_views.export_revenue_report, name='export_revenue_report'),
    # 
    # # Subscription Management (Secure)
    # path('admin/subscriptions/', admin_views.subscriptions_list, name='subscriptions_list'),
    # path('admin/subscriptions/<uuid:subscription_id>/', admin_views.subscription_detail, name='subscription_detail'),
    # 
    # # Pricing management
    # path('admin/pricing/plans/', admin_views.admin_pricing_plans, name='admin_pricing_plans'),
    # path('admin/pricing/plans/<uuid:plan_id>/', admin_views.admin_pricing_plan_detail, name='admin_pricing_plan_detail'),
    # 
    # # Legacy endpoints (to be updated)
    # path('admin/subscriptions/legacy/', admin_views.admin_subscriptions, name='admin_subscriptions_legacy'),
    # path('admin/subscriptions/<uuid:subscription_id>/verify/', admin_views.admin_verify_payment, name='admin_verify_payment'),
    # 
    # # Telegram management  
    # path('admin/telegram/queue/', admin_views.admin_telegram_queue, name='admin_telegram_queue'),
    # path('admin/telegram/tasks/<uuid:task_id>/action/', admin_views.admin_telegram_action, name='admin_telegram_action'),
    # 
    # # Payment transactions
    # path('admin/transactions/', admin_views.admin_payment_transactions, name='admin_payment_transactions'),
    
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