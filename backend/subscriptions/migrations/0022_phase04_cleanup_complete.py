# Generated manually on 2025-11-05

from django.db import migrations


class Migration(migrations.Migration):
    """
    No-op migration to mark cleanup complete.
    
    Phase 0.4 models were already removed manually:
    - AdminActionLog
    - DataAccessLog  
    - PaymentTransaction
    - PricingPlan
    - SignalSubscription
    - SubscriptionChangeLog
    - TelegramGroupManagement
    - CacheMetrics
    - PerformanceMetrics
    - SubscriptionAnalytics
    - SystemMetrics
    
    All tables have been cleaned up. This migration acknowledges
    the state without attempting to drop non-existent tables.
    """

    dependencies = [
        ('subscriptions', '0021_remove_deprecated_phase04_models'),
    ]

    operations = [
        # No operations needed - cleanup already complete
    ]
