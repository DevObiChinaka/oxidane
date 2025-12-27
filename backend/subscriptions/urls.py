from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import admin_views  # Phase 0.5 unified subscriptions management
from . import payment_admin_views  # Payment transactions management
from .pricing_views import PricingPlanViewSet, CouponViewSet
from . import billing_views
from .user_subscription_views import UserSubscriptionViewSet
from . import user_views  # Function-based user views
from . import mentorship_admin_views
from .api_views import (
    SubscriptionViewSet, SubscriptionPlanViewSet, FeatureViewSet, 
    CouponViewSet as APICouponViewSet,
    TelegramConfigurationViewSet, TelegramGroupViewSet, PaymentConfigurationViewSet,
    EmailConfigurationViewSet, SetupStatusViewSet, PublicPricingViewSet, ValidateCouponViewSet,
        SubscriptionUpgradeViewSet, SubscriptionDowngradeViewSet,
    CurrencyConversionViewSet
)  # Phase 0.5 - Tasks 0.5.20-0.5.36
from .views import (
    InitializePaymentView, VerifyPaymentView, PaymentHistoryView,
    InvoiceDownloadView, paystack_webhook, stripe_webhook,
    CheckSubscriptionConflictView, charge_with_saved_card, check_pending_payment
)  # Phase 2.1 - Payment API Endpoints
from .views.payment_method_views import (
    save_payment_method, list_payment_methods, 
    set_default_payment_method, delete_payment_method,
    get_payment_config
)  # Payment method tokenization for auto-renewal
# REMOVED: Telegram webhooks - Using polling instead (no ngrok needed)
# from .views.telegram_webhook import (
#     telegram_webhook, set_telegram_webhook, get_webhook_info
# )  # Phase 2.2 - Telegram Auto-Add Webhook (DEPRECATED - Using polling)

app_name = 'subscriptions'

# API Router for pricing management
router = DefaultRouter()
router.register(r'pricing/plans', PricingPlanViewSet, basename='pricing-plans')
router.register(r'pricing/coupons', CouponViewSet, basename='coupon-codes')

# User subscription management router
user_router = DefaultRouter()
user_router.register(r'subscriptions', UserSubscriptionViewSet, basename='user-subscriptions')

# NEW: Phase 0.5 - Tasks 0.5.20-0.5.30 - Subscription, Plan, Feature, Coupon, Telegram, Payment, Email Config API endpoints
api_router = DefaultRouter()
api_router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
api_router.register(r'admin/plans', SubscriptionPlanViewSet, basename='plan')
api_router.register(r'admin/features', FeatureViewSet, basename='feature')
api_router.register(r'admin/coupons', APICouponViewSet, basename='coupon')
api_router.register(r'admin/telegram/config', TelegramConfigurationViewSet, basename='telegram-config')
api_router.register(r'admin/telegram/groups', TelegramGroupViewSet, basename='telegram-group')
api_router.register(r'admin/payment/config', PaymentConfigurationViewSet, basename='payment-config')
api_router.register(r'admin/email/config', EmailConfigurationViewSet, basename='email-config')
api_router.register(r'admin/setup/status', SetupStatusViewSet, basename='setup-status')

# NEW: Phase 0.5 - Task 0.5.33-0.5.36 - Public versioned API (v1)
v1_router = DefaultRouter()
v1_router.register(r'subscriptions/plans', PublicPricingViewSet, basename='v1-plans')
v1_router.register(r'subscriptions/validate-coupon', ValidateCouponViewSet, basename='v1-validate-coupon')
v1_router.register(r'subscriptions', SubscriptionUpgradeViewSet, basename='v1-subscription-upgrade')
v1_router.register(r'subscriptions', SubscriptionDowngradeViewSet, basename='v1-subscription-downgrade')
v1_router.register(r'currency', CurrencyConversionViewSet, basename='v1-currency')  # Live currency conversion

urlpatterns = [
    # Admin API endpoints for pricing management
    path('admin/', include(router.urls)),
    
    # User subscription management API - ViewSet routes
    # This includes: /api/subscriptions/<id>/auto-renewal/
    path('', include(user_router.urls)),
    
    # User subscription management API - Function-based view
    # MUST be before api_router to avoid being matched as detail view with pk='my-subscriptions'
    # Path: /api/subscriptions/my-subscriptions/
    path('subscriptions/my-subscriptions/', user_views.my_subscriptions, name='my-subscriptions'),
    
    # NEW: Phase 0.5 - Task 0.5.20 - Comprehensive subscription API
    # Note: Already prefixed with 'api/' in main urls.py, so this becomes /api/subscriptions/
    path('', include(api_router.urls)),
    
    # NEW: Phase 0.5 - Task 0.5.33 - Public versioned API (v1)
    # Note: Already prefixed with 'api/' in main urls.py, so this becomes /api/v1/subscriptions/plans/
    path('v1/', include(v1_router.urls)),
    
    # ============================================================================
    # BILLING & TELEGRAM VERIFICATION ENDPOINTS
    # ============================================================================
    
    # Telegram Verification (User-facing)
    path('billing/telegram/generate-code/', billing_views.generate_verification_code, name='generate_verification_code'),
    path('billing/telegram/verify-username/', billing_views.verify_telegram_username, name='verify_telegram_username'),
    path('billing/telegram/confirm/', billing_views.confirm_telegram_verification, name='confirm_telegram_verification'),
    path('billing/telegram/status/', billing_views.telegram_verification_status, name='telegram_verification_status'),
    path('billing/telegram/unlink/', billing_views.unlink_telegram, name='unlink_telegram'),
    
    # Telegram Verification Callback (Bot-only, uses X-Bot-Secret header) - DEPRECATED, kept for backward compatibility
    path('billing/telegram/verify-callback/', billing_views.telegram_verify_callback, name='telegram_verify_callback'),
    
    # DEV ONLY: Skip Telegram verification for local testing
    # path('dev/skip-telegram-verification/', dev_verify_telegram.dev_skip_telegram_verification, name='dev_skip_telegram'),
    
    # ============================================================================
    # PAYMENT API ENDPOINTS - Phase 2.1 (November 10, 2025)
    # ============================================================================
    
    # Payment Initialization & Verification
    path('payments/initialize/', InitializePaymentView.as_view(), name='initialize_payment'),
    path('payments/charge-saved-card/', charge_with_saved_card, name='charge_with_saved_card'),
    path('payments/verify/', VerifyPaymentView.as_view(), name='verify_payment'),
    path('payments/check-pending/', check_pending_payment, name='check_pending_payment'),
    path('payments/check-conflict/', CheckSubscriptionConflictView.as_view(), name='check_subscription_conflict'),
    
    # Payment Webhooks (CSRF exempt)
    path('payments/webhook/paystack/', paystack_webhook, name='paystack_webhook'),
    path('payments/webhook/stripe/', stripe_webhook, name='stripe_webhook'),
    
    # Payment History & Invoices
    path('payments/history/', PaymentHistoryView.as_view(), name='payment_history'),
    path('payments/<int:payment_id>/invoice/', InvoiceDownloadView.as_view(), name='payment_invoice'),
    
    # Payment Method Management (Auto-renewal tokenization)
    path('payment-methods/config/', get_payment_config, name='get_payment_config'),
    path('payment-methods/save/', save_payment_method, name='save_payment_method'),
    path('payment-methods/', list_payment_methods, name='list_payment_methods'),
    path('payment-methods/<uuid:payment_method_id>/set-default/', set_default_payment_method, name='set_default_payment_method'),
    path('payment-methods/<uuid:payment_method_id>/', delete_payment_method, name='delete_payment_method'),
    
    # ============================================================================
    # TELEGRAM AUTO-ADD - Phase 2.2 (November 10, 2025)
    # ============================================================================
    # REMOVED: Using polling instead of webhooks (no ngrok/public URL needed)
    # See: subscriptions/tasks.py::process_telegram_updates()
    # Celery Beat runs every 10 seconds to poll for messages
    
    # # Telegram Webhook (receives join request updates) - DEPRECATED
    # path('telegram/webhook/', telegram_webhook, name='telegram_webhook'),
    # 
    # # Webhook Management (admin endpoints) - DEPRECATED  
    # path('telegram/set-webhook/', set_telegram_webhook, name='set_telegram_webhook'),
    # path('telegram/webhook-info/', get_webhook_info, name='get_telegram_webhook_info'),
    
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
    
    # ============================================================================
    # PHASE 0.5: Unified Subscriptions Management
    # ============================================================================
    path('admin/subscriptions-management/', admin_views.subscription_management_list, name='subscription_management_list'),
    path('admin/subscriptions-management/<uuid:subscription_id>/update/', admin_views.update_subscription_action, name='update_subscription_action'),
    path('admin/subscriptions-management/plans/', admin_views.subscription_plans_filter, name='subscription_plans_filter'),
    
    # ============================================================================
    # SYSTEM HEALTH & MONITORING
    # ============================================================================
    path('admin/health/', admin_views.system_health_check, name='system_health'),
    
    # ============================================================================
    # PAYMENT TRANSACTIONS MANAGEMENT
    # ============================================================================
    path('admin/payments/transactions/', payment_admin_views.payment_transactions_list, name='payment_transactions_list'),
    path('admin/revenue/analytics/', payment_admin_views.revenue_analytics, name='revenue_analytics'),
]