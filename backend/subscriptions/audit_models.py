# Audit and logging models for subscription management
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import json

User = get_user_model()

class AdminActionLog(models.Model):
    """Comprehensive audit log for all admin actions"""
    
    SENSITIVITY_LEVELS = [
        ('LOW', 'Low - General operations'),
        ('NORMAL', 'Normal - Standard admin actions'),
        ('FINANCIAL', 'Financial - Payment/subscription related'),
        ('HIGH', 'High - Critical security operations'),
        ('CRITICAL', 'Critical - System-wide changes'),
    ]
    
    ACTION_TYPES = [
        # Subscription actions
        ('VIEW_SUBSCRIPTIONS_LIST', 'View Subscriptions List'),
        ('VIEW_SUBSCRIPTION_DETAIL', 'View Subscription Detail'), 
        ('MODIFY_SUBSCRIPTION', 'Modify Subscription'),
        ('VERIFY_PAYMENT', 'Verify Payment'),
        ('PROCESS_REFUND', 'Process Refund'),
        ('EXTEND_SUBSCRIPTION', 'Extend Subscription'),
        
        # User management actions
        ('VIEW_USERS_LIST', 'View Users List'),
        ('VIEW_USER_DETAIL', 'View User Detail'),
        ('MODIFY_USER', 'Modify User Account'),
        ('ACTIVATE_USER', 'Activate User'),
        ('DEACTIVATE_USER', 'Deactivate User'),
        
        # Telegram actions
        ('TELEGRAM_ADD_USER', 'Add User to Telegram'),
        ('TELEGRAM_REMOVE_USER', 'Remove User from Telegram'),
        ('TELEGRAM_BROADCAST', 'Send Telegram Broadcast'),
        
        # System actions
        ('LOGIN_ADMIN', 'Admin Login'),
        ('LOGOUT_ADMIN', 'Admin Logout'),
        ('EXPORT_DATA', 'Export Data'),
        ('SYSTEM_CONFIG', 'System Configuration'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partially Completed'),
        ('PENDING', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who performed the action
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,  # Never delete audit logs
        related_name='admin_actions_performed'
    )
    
    # What action was performed
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    sensitivity = models.CharField(max_length=10, choices=SENSITIVITY_LEVELS, default='NORMAL')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    # When and where
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Request details
    request_method = models.CharField(max_length=10, blank=True)  # GET, POST, etc.
    request_path = models.CharField(max_length=500, blank=True)
    request_params = models.JSONField(default=dict, blank=True)
    
    # Response details
    response_status_code = models.IntegerField(null=True, blank=True)
    duration_ms = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    
    # Affected resources
    target_user_id = models.UUIDField(null=True, blank=True, help_text="User affected by action")
    target_subscription_id = models.UUIDField(null=True, blank=True, help_text="Subscription affected")
    resource_ids = models.JSONField(default=list, blank=True, help_text="Other affected resource IDs")
    
    # Action details and results
    action_description = models.TextField(blank=True, help_text="Human-readable action description")
    changes_made = models.JSONField(default=dict, blank=True, help_text="Before/after values")
    error_message = models.TextField(blank=True, help_text="Error details if action failed")
    
    # Compliance and retention
    requires_retention = models.BooleanField(default=True, help_text="Must be kept for compliance")
    retention_years = models.PositiveIntegerField(default=7, help_text="Years to retain this log")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_action_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['sensitivity', '-timestamp']),
            models.Index(fields=['target_user_id']),
            models.Index(fields=['target_subscription_id']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.email} - {self.action_type} - {self.status}"
    
    @property
    def is_financial_action(self):
        """Check if this is a financial/payment related action"""
        return self.sensitivity in ['FINANCIAL', 'HIGH', 'CRITICAL']
    
    @property  
    def retention_end_date(self):
        """Calculate when this log can be deleted"""
        from datetime import timedelta
        return self.created_at + timedelta(days=365 * self.retention_years)

class SubscriptionChangeLog(models.Model):
    """Detailed change tracking for subscription modifications"""
    
    CHANGE_TYPES = [
        ('STATUS_CHANGE', 'Payment Status Change'),
        ('PERIOD_EXTENSION', 'Subscription Period Extended'),
        ('PERIOD_SHORTENING', 'Subscription Period Shortened'), 
        ('AMOUNT_ADJUSTMENT', 'Amount Adjusted'),
        ('PLAN_UPGRADE', 'Plan Upgraded'),
        ('PLAN_DOWNGRADE', 'Plan Downgraded'),
        ('TELEGRAM_UPDATE', 'Telegram Status Updated'),
        ('REFUND_PROCESSED', 'Refund Processed'),
        ('MANUAL_VERIFICATION', 'Manual Payment Verification'),
        ('ADMIN_NOTE_ADDED', 'Admin Note Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to subscription and admin action
    subscription = models.ForeignKey(
        'SignalSubscription', 
        on_delete=models.CASCADE,
        related_name='change_history'
    )
    admin_action_log = models.ForeignKey(
        AdminActionLog,
        on_delete=models.CASCADE,
        related_name='subscription_changes'
    )
    
    # Change details
    change_type = models.CharField(max_length=25, choices=CHANGE_TYPES)
    field_name = models.CharField(max_length=50, help_text="Database field that was changed")
    
    # Before/after values (stored as JSON for flexibility)
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Change justification
    reason = models.TextField(blank=True, help_text="Reason for the change")
    business_justification = models.TextField(blank=True, help_text="Business reason (customer service, etc.)")
    
    # Financial impact (if applicable)
    financial_impact = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Financial impact of change (positive = revenue, negative = cost)"
    )
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'subscription_change_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['subscription', '-timestamp']),
            models.Index(fields=['change_type', '-timestamp']),
            models.Index(fields=['admin_action_log']),
        ]
    
    def __str__(self):
        return f"{self.subscription.user.email} - {self.change_type} - {self.timestamp}"
    
    @property
    def change_summary(self):
        """Human-readable change summary"""
        if self.field_name == 'payment_status':
            return f"Payment status: {self.previous_value} → {self.new_value}"
        elif self.field_name == 'subscription_end':
            return f"End date: {self.previous_value} → {self.new_value}"
        elif self.field_name == 'amount_paid':
            return f"Amount: {self.previous_value} → {self.new_value}"
        return f"{self.field_name}: {self.previous_value} → {self.new_value}"

class DataAccessLog(models.Model):
    """Log access to sensitive financial data for compliance"""
    
    ACCESS_TYPES = [
        ('VIEW_PAYMENT_DETAILS', 'View Payment Details'),
        ('EXPORT_FINANCIAL_DATA', 'Export Financial Data'),
        ('ACCESS_TRANSACTION_HISTORY', 'Access Transaction History'),
        ('VIEW_REVENUE_REPORTS', 'View Revenue Reports'),
        ('ACCESS_USER_FINANCIAL_INFO', 'Access User Financial Information'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    admin_user = models.ForeignKey(User, on_delete=models.PROTECT)
    access_type = models.CharField(max_length=30, choices=ACCESS_TYPES)
    
    # What data was accessed
    data_classification = models.CharField(max_length=20, default='FINANCIAL')
    records_accessed = models.PositiveIntegerField(help_text="Number of records accessed")
    data_summary = models.JSONField(default=dict, help_text="Summary of what data was accessed")
    
    # Access context
    business_purpose = models.TextField(help_text="Business reason for accessing this data")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField()
    session_id = models.CharField(max_length=100, blank=True)
    
    # Compliance tracking
    compliance_category = models.CharField(max_length=20, default='PCI_DSS')
    retention_required = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'data_access_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['access_type', '-timestamp']),
            models.Index(fields=['data_classification']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.email} - {self.access_type} - {self.records_accessed} records"

class SystemMetrics(models.Model):
    """Track system performance and usage metrics"""
    
    METRIC_TYPES = [
        ('API_RESPONSE_TIME', 'API Response Time'),
        ('DATABASE_QUERY_TIME', 'Database Query Performance'),
        ('ADMIN_SESSION_COUNT', 'Active Admin Sessions'),
        ('SUBSCRIPTION_PROCESSING_TIME', 'Subscription Processing Time'),
        ('TELEGRAM_OPERATION_TIME', 'Telegram Operation Time'),
        ('CACHE_HIT_RATE', 'Cache Performance'),
        ('ERROR_RATE', 'System Error Rate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20, help_text="ms, count, percentage, etc.")
    
    # Context
    endpoint_path = models.CharField(max_length=200, blank=True)
    user_count = models.PositiveIntegerField(null=True, blank=True)
    additional_context = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'system_metrics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', '-timestamp']),
            models.Index(fields=['endpoint_path', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_type}: {self.metric_value}{self.metric_unit}"