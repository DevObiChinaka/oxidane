# Performance analytics and aggregation models
from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

class SubscriptionAnalytics(models.Model):
    """Aggregated subscription analytics for performance optimization"""
    
    AGGREGATION_PERIODS = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    aggregation_period = models.CharField(max_length=10, choices=AGGREGATION_PERIODS)
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    
    # Subscription metrics
    total_subscriptions = models.PositiveIntegerField(default=0)
    new_subscriptions = models.PositiveIntegerField(default=0)
    renewed_subscriptions = models.PositiveIntegerField(default=0)
    cancelled_subscriptions = models.PositiveIntegerField(default=0)
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_subscription_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Plan type breakdown (JSON for flexibility)
    plan_type_breakdown = models.JSONField(default=dict, help_text="Revenue and count by plan type")
    
    # Payment status breakdown
    verified_payments = models.PositiveIntegerField(default=0)
    pending_payments = models.PositiveIntegerField(default=0)
    failed_payments = models.PositiveIntegerField(default=0)
    
    # Telegram integration metrics
    telegram_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    telegram_additions = models.PositiveIntegerField(default=0)
    telegram_failures = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    average_processing_time = models.FloatField(default=0.0, help_text="Average processing time in seconds")
    admin_actions_count = models.PositiveIntegerField(default=0)
    
    # Data freshness
    calculated_at = models.DateTimeField(auto_now=True)
    data_version = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'subscription_analytics'
        unique_together = ['aggregation_period', 'period_start']
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['aggregation_period', '-period_start']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['-calculated_at']),
        ]
    
    def __str__(self):
        return f"{self.aggregation_period} analytics for {self.period_start}"
    
    @classmethod
    def calculate_analytics(cls, period_type='daily', target_date=None):
        """Calculate and store analytics for a specific period"""
        from .models import SignalSubscription
        from .audit_models import AdminActionLog
        
        if not target_date:
            target_date = timezone.now().date()
        
        # Determine period boundaries
        period_start, period_end = cls._get_period_boundaries(period_type, target_date)
        
        # Get or create analytics record
        analytics, created = cls.objects.get_or_create(
            aggregation_period=period_type,
            period_start=period_start,
            defaults={'period_end': period_end}
        )
        
        # Calculate subscription metrics
        period_subscriptions = SignalSubscription.objects.filter(
            created_at__date__gte=period_start,
            created_at__date__lte=period_end
        )
        
        analytics.total_subscriptions = period_subscriptions.count()
        analytics.new_subscriptions = period_subscriptions.filter(
            created_at__date__gte=period_start
        ).count()
        
        # Revenue calculations
        verified_subscriptions = period_subscriptions.filter(payment_status='verified')
        analytics.total_revenue = verified_subscriptions.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        if verified_subscriptions.exists():
            analytics.average_subscription_value = verified_subscriptions.aggregate(
                avg=Avg('amount_paid')
            )['avg'] or Decimal('0.00')
        
        # Payment status breakdown
        analytics.verified_payments = period_subscriptions.filter(payment_status='verified').count()
        analytics.pending_payments = period_subscriptions.filter(payment_status='pending').count()
        analytics.failed_payments = period_subscriptions.filter(payment_status='failed').count()
        
        # Refunded amount
        analytics.refunded_amount = period_subscriptions.filter(
            payment_status='refunded'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        # Plan type breakdown
        plan_breakdown = {}
        for plan_type in ['weekly', 'monthly', 'vip']:
            plan_subs = period_subscriptions.filter(plan_type=plan_type)
            plan_breakdown[plan_type] = {
                'count': plan_subs.count(),
                'revenue': float(plan_subs.filter(payment_status='verified').aggregate(
                    total=Sum('amount_paid')
                )['total'] or Decimal('0.00'))
            }
        analytics.plan_type_breakdown = plan_breakdown
        
        # Telegram metrics
        telegram_total = period_subscriptions.exclude(telegram_status='not_added').count()
        telegram_success = period_subscriptions.filter(telegram_status='added').count()
        
        if telegram_total > 0:
            analytics.telegram_success_rate = Decimal(telegram_success / telegram_total * 100)
        analytics.telegram_additions = telegram_success
        analytics.telegram_failures = period_subscriptions.filter(telegram_status='failed_add').count()
        
        # Admin actions count
        analytics.admin_actions_count = AdminActionLog.objects.filter(
            timestamp__date__gte=period_start,
            timestamp__date__lte=period_end
        ).count()
        
        analytics.save()
        return analytics
    
    @staticmethod
    def _get_period_boundaries(period_type, target_date):
        """Get start and end dates for aggregation period"""
        if period_type == 'daily':
            return target_date, target_date
        elif period_type == 'weekly':
            start = target_date - timedelta(days=target_date.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif period_type == 'monthly':
            start = target_date.replace(day=1)
            if target_date.month == 12:
                end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
            return start, end
        elif period_type == 'quarterly':
            quarter_month = ((target_date.month - 1) // 3) * 3 + 1
            start = target_date.replace(month=quarter_month, day=1)
            if quarter_month == 10:
                end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = target_date.replace(month=quarter_month + 3, day=1) - timedelta(days=1)
            return start, end
        elif period_type == 'yearly':
            start = target_date.replace(month=1, day=1)
            end = target_date.replace(month=12, day=31)
            return start, end
        
        return target_date, target_date

class PerformanceMetrics(models.Model):
    """Real-time performance tracking for system optimization"""
    
    METRIC_CATEGORIES = [
        ('database', 'Database Performance'),
        ('api', 'API Response Times'),
        ('telegram', 'Telegram Operations'),
        ('payment', 'Payment Processing'),
        ('admin', 'Admin Dashboard'),
        ('system', 'System Resources'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    category = models.CharField(max_length=20, choices=METRIC_CATEGORIES)
    metric_name = models.CharField(max_length=100)
    
    # Performance values
    response_time_ms = models.FloatField(null=True, blank=True)
    throughput_per_second = models.FloatField(null=True, blank=True)
    error_rate_percent = models.FloatField(null=True, blank=True)
    
    # Resource usage
    cpu_usage_percent = models.FloatField(null=True, blank=True)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    
    # Context
    endpoint_path = models.CharField(max_length=200, blank=True)
    user_count = models.PositiveIntegerField(null=True, blank=True)
    concurrent_requests = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional metrics as JSON for flexibility
    additional_metrics = models.JSONField(default=dict)
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'performance_metrics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['category', '-timestamp']),
            models.Index(fields=['metric_name', '-timestamp']),
            models.Index(fields=['endpoint_path', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.category} - {self.metric_name} - {self.response_time_ms}ms"
    
    @classmethod
    def record_api_performance(cls, endpoint_path, response_time_ms, user_count=None, additional_data=None):
        """Record API performance metrics"""
        return cls.objects.create(
            category='api',
            metric_name='API Response Time',
            endpoint_path=endpoint_path,
            response_time_ms=response_time_ms,
            user_count=user_count,
            additional_metrics=additional_data or {}
        )
    
    @classmethod
    def record_database_performance(cls, query_type, execution_time_ms, additional_data=None):
        """Record database query performance"""
        return cls.objects.create(
            category='database',
            metric_name=f'Database Query - {query_type}',
            response_time_ms=execution_time_ms,
            additional_metrics=additional_data or {}
        )
    
    @classmethod
    def get_average_performance(cls, category, hours=24):
        """Get average performance metrics for a category"""
        since = timezone.now() - timedelta(hours=hours)
        
        return cls.objects.filter(
            category=category,
            timestamp__gte=since
        ).aggregate(
            avg_response_time=Avg('response_time_ms'),
            avg_throughput=Avg('throughput_per_second'),
            avg_error_rate=Avg('error_rate_percent')
        )

class CacheMetrics(models.Model):
    """Track caching performance and efficiency"""
    
    CACHE_TYPES = [
        ('redis', 'Redis Cache'),
        ('database', 'Database Query Cache'),
        ('api', 'API Response Cache'),
        ('session', 'Session Cache'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    cache_type = models.CharField(max_length=20, choices=CACHE_TYPES)
    cache_key_pattern = models.CharField(max_length=200)
    
    # Cache performance
    hit_count = models.PositiveIntegerField(default=0)
    miss_count = models.PositiveIntegerField(default=0)
    hit_rate_percent = models.FloatField(default=0.0)
    
    # Performance impact
    average_retrieval_time_ms = models.FloatField(default=0.0)
    cache_size_mb = models.FloatField(default=0.0)
    
    # Time period
    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField(db_index=True)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cache_metrics'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['cache_type', '-period_start']),
            models.Index(fields=['cache_key_pattern']),
            models.Index(fields=['-calculated_at']),
        ]
    
    def __str__(self):
        return f"{self.cache_type} - {self.hit_rate_percent}% hit rate"
    
    @property
    def total_requests(self):
        """Total cache requests"""
        return self.hit_count + self.miss_count
    
    @classmethod
    def calculate_cache_efficiency(cls, cache_type, hours=24):
        """Calculate cache efficiency metrics"""
        since = timezone.now() - timedelta(hours=hours)
        
        metrics = cls.objects.filter(
            cache_type=cache_type,
            period_start__gte=since
        ).aggregate(
            total_hits=Sum('hit_count'),
            total_misses=Sum('miss_count'),
            avg_hit_rate=Avg('hit_rate_percent'),
            avg_retrieval_time=Avg('average_retrieval_time_ms')
        )
        
        total_requests = (metrics['total_hits'] or 0) + (metrics['total_misses'] or 0)
        if total_requests > 0:
            metrics['overall_hit_rate'] = (metrics['total_hits'] or 0) / total_requests * 100
        else:
            metrics['overall_hit_rate'] = 0
        
        return metrics