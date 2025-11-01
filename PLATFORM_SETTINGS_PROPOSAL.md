# Platform Settings Proposal - Oxidane Forex Academy
**Date:** October 24, 2025  
**Status:** Discussion Document

## Executive Summary

Based on the analysis of the Oxidane platform, this document proposes necessary settings for optimal administration, user experience, and business operations. The platform currently handles:
- Forex signal subscriptions (weekly, monthly, VIP)
- Mentorship programs
- Course management
- Payment processing
- Telegram group management
- Email notifications

---

## 1. PRICING & SUBSCRIPTION SETTINGS

### 1.1 Plan Configuration
**Location:** `/admin/pricing` (to be implemented)

#### Required Settings:

**A. Default Pricing Plans**
```
├── Signal Subscriptions
│   ├── Weekly ($X)
│   ├── Monthly ($Y)
│   └── Yearly ($Z with X% discount)
├── Mentorship Programs
│   ├── Basic Mentorship (One-time fee)
│   └── Advanced Mentorship (Coming soon)
└── VIP Plans
    ├── Weekly VIP ($A)
    ├── Monthly VIP ($B)
    └── Yearly VIP ($C with Y% discount)
```

**Settings to Configure:**
- ✅ **Price per plan** (USD, NGN, EUR, GBP)
- ✅ **Billing cycle** (one-time, weekly, monthly, yearly)
- ✅ **Plan description** (user-facing)
- ✅ **Features list** (JSON array for pricing page display)
- ✅ **Discount percentage** (0-100%)
- ✅ **Promotional pricing** (temporary price + date range)
- ✅ **Plan visibility** (active/inactive)
- ✅ **Featured status** (highlight on pricing page)
- ✅ **Sort order** (display priority)
- ✅ **Call-to-action text** ("Get Started", "Subscribe Now", etc.)

**Currently Missing:**
- ⚠️ **Trial period settings** (7-day free trial, 14-day money-back)
- ⚠️ **Auto-renewal settings** (enable/disable by plan)
- ⚠️ **Grace period** (days after expiration before access removal)
- ⚠️ **Upgrade/downgrade rules** (prorated refunds, immediate vs end-of-cycle)

---

### 1.2 Currency & Payment Settings

**Multi-Currency Support:**
```json
{
  "default_currency": "USD",
  "supported_currencies": ["USD", "NGN", "EUR", "GBP"],
  "exchange_rate_provider": "manual|api",
  "exchange_rates": {
    "USD_NGN": 1580.00,
    "USD_EUR": 0.92,
    "USD_GBP": 0.79
  },
  "auto_update_rates": false,
  "update_frequency_hours": 24
}
```

**Payment Gateway Settings:**
```json
{
  "payment_provider": "paystack|stripe|flutterwave",
  "test_mode": true,
  "payment_methods": {
    "card": true,
    "bank_transfer": true,
    "ussd": true,
    "mobile_money": true,
    "qr_code": false
  },
  "minimum_payment_amount": 1.00,
  "payment_verification_timeout_minutes": 30,
  "auto_verify_payments": false,
  "webhook_url": "https://yourdomain.com/api/webhooks/payment"
}
```

**Currently Missing:**
- ⚠️ **Payment gateway credentials** (API keys, secret keys)
- ⚠️ **Webhook security** (signature verification)
- ⚠️ **Failed payment retry logic** (attempts, intervals)
- ⚠️ **Refund policy settings** (automatic vs manual, time limits)

---

### 1.3 Discount & Coupon Settings

**Coupon Management:**
```
Settings:
├── Maximum coupons per user (e.g., 3)
├── Stackable coupons (yes/no)
├── Apply to promotional prices (yes/no)
├── Coupon visibility (public vs private codes)
├── Auto-expire unused coupons (days)
└── Notification on coupon expiry (yes/no)
```

**Referral Program Settings:**
```json
{
  "referral_enabled": true,
  "referrer_reward_type": "percentage|fixed|credit",
  "referrer_reward_value": 10,
  "referee_reward_type": "percentage|fixed",
  "referee_reward_value": 5,
  "minimum_referrals_for_bonus": 5,
  "bonus_reward": 50.00,
  "payout_method": "wallet_credit|bank_transfer",
  "minimum_payout_threshold": 20.00
}
```

**Currently Missing:**
- ⚠️ **Referral tracking system**
- ⚠️ **Affiliate program infrastructure**
- ⚠️ **User wallet/credit system**

---

## 2. TELEGRAM INTEGRATION SETTINGS

### 2.1 Telegram Bot Configuration
**Location:** `/admin/settings/telegram`

**Current Settings (from settings.py):**
```python
TELEGRAM_BOT_TOKEN = "8386662254:AAFwqfss8wXc6SULYyX73yVvJ6OV686JI1I"
TELEGRAM_GROUPS = {
    'premium_signals': {
        'name': 'OxiWorld Premium Signals',
        'chat_id': '-1002920074390',
        'type': 'group',
        'access_level': 'premium'
    },
    'education_group': {
        'name': 'OxiWorld Forex Mentorship',
        'chat_id': '-4885168917',
        'type': 'group',
        'access_level': 'basic'
    },
    'vip_community': {
        'name': 'OxiWorld VIP Members',
        'chat_id': '-4811814960',
        'type': 'group',
        'access_level': 'vip'
    }
}
```

**Enhanced Settings Needed:**
```json
{
  "bot_enabled": true,
  "bot_username": "@OxiWorldBot",
  "auto_add_verified_users": true,
  "auto_remove_expired_users": true,
  "welcome_message_enabled": true,
  "welcome_message_template": "Welcome {{user.first_name}}! You now have access to {{plan.name}}.",
  "expiry_warning_enabled": true,
  "expiry_warning_days": [7, 3, 1],
  "removal_grace_period_hours": 24,
  "manual_verification_required": false,
  "telegram_verification_method": "username|user_id|both"
}
```

**Group Access Rules:**
```json
{
  "signals_weekly": ["education_group"],
  "signals_monthly": ["premium_signals", "education_group"],
  "signals_yearly": ["premium_signals", "education_group"],
  "mentorship_basic": ["education_group"],
  "vip_weekly": ["vip_community", "premium_signals", "education_group"],
  "vip_monthly": ["vip_community", "premium_signals", "education_group"],
  "vip_yearly": ["vip_community", "premium_signals", "education_group"]
}
```

**Bot Command Settings:**
```json
{
  "commands_enabled": true,
  "available_commands": {
    "/start": {"enabled": true, "admin_only": false},
    "/verify": {"enabled": true, "admin_only": false},
    "/status": {"enabled": true, "admin_only": false},
    "/renew": {"enabled": true, "admin_only": false},
    "/help": {"enabled": true, "admin_only": false},
    "/broadcast": {"enabled": true, "admin_only": true},
    "/stats": {"enabled": true, "admin_only": true}
  }
}
```

**Currently Missing:**
- ⚠️ **Bot command handlers** (need implementation)
- ⚠️ **Telegram webhook setup** (vs polling)
- ⚠️ **Rate limiting** (prevent spam)
- ⚠️ **Moderation tools** (ban, mute, warn)
- ⚠️ **Message templates** (announcements, alerts)

---

## 3. EMAIL NOTIFICATION SETTINGS

### 3.1 Email System Configuration
**Location:** `/admin/settings/email`

**Current Settings (from settings.py):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_TIMEOUT = 30
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = f'OxiWorld <{EMAIL_HOST_USER}>'
```

**Enhanced Email Settings:**
```json
{
  "email_provider": "gmail|sendgrid|ses|mailgun",
  "sending_enabled": true,
  "test_mode": false,
  "from_name": "OxiWorld Forex Academy",
  "from_email": "noreply@oxiworld.com",
  "reply_to_email": "support@oxiworld.com",
  "max_send_rate_per_hour": 100,
  "retry_failed_emails": true,
  "retry_attempts": 3,
  "retry_delay_minutes": 15,
  "track_opens": true,
  "track_clicks": true,
  "unsubscribe_link_enabled": true,
  "unsubscribe_page_url": "https://oxiworld.com/unsubscribe"
}
```

### 3.2 Email Template Settings

**Notification Types:**
```
✅ Registration & Verification
   ├── Welcome email
   ├── Email verification (OTP)
   └── Account activated

✅ Payment & Subscription
   ├── Payment confirmed
   ├── Subscription activated
   ├── Payment failed
   ├── Refund processed
   └── Invoice/receipt

✅ Subscription Lifecycle
   ├── Expiry warning (7 days, 3 days, 1 day)
   ├── Subscription expired
   ├── Renewal reminder
   └── Upgrade suggestion

✅ Telegram Access
   ├── Telegram verification instructions
   ├── Group access granted
   └── Group access removed

⚠️ Course & Learning (TO ADD)
   ├── Course enrollment
   ├── New lesson available
   ├── Course completion
   └── Certificate ready

⚠️ Marketing & Engagement (TO ADD)
   ├── Newsletter
   ├── Special offers
   ├── Event invitations
   └── Re-engagement campaigns
```

**Email Frequency Settings:**
```json
{
  "daily_email_limit_per_user": 5,
  "marketing_emails_enabled": true,
  "transactional_emails_always_send": true,
  "quiet_hours_enabled": false,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "timezone": "UTC",
  "unsubscribe_categories": [
    {"key": "marketing", "label": "Marketing & Promotions", "default": true},
    {"key": "newsletter", "label": "Weekly Newsletter", "default": true},
    {"key": "product_updates", "label": "Product Updates", "default": true},
    {"key": "transactional", "label": "Account & Orders", "locked": true}
  ]
}
```

**Currently Missing:**
- ⚠️ **Email scheduling system** (send at optimal times)
- ⚠️ **A/B testing for email templates**
- ⚠️ **Email analytics dashboard** (open rate, click rate, bounce rate)
- ⚠️ **Personalization variables** (beyond basic user data)

---

## 4. COURSE & CONTENT SETTINGS

### 4.1 Course Management Settings
**Location:** `/admin/settings/courses`

**Content Settings:**
```json
{
  "default_course_status": "draft",
  "auto_publish_on_complete": false,
  "require_admin_approval": true,
  "allow_free_courses": true,
  "max_video_size_mb": 500,
  "allowed_video_formats": ["mp4", "webm", "mov"],
  "video_processing_enabled": true,
  "generate_thumbnails": true,
  "thumbnail_timestamps": [0, 30, 60],
  "enable_subtitles": false,
  "supported_subtitle_formats": ["srt", "vtt"]
}
```

**Access Control:**
```json
{
  "free_course_registration_required": true,
  "premium_course_access": "subscription|one_time_payment|both",
  "course_preview_enabled": true,
  "preview_lessons_count": 1,
  "download_enabled": false,
  "offline_viewing_days": 0,
  "concurrent_device_limit": 2,
  "ip_geofencing_enabled": false,
  "allowed_countries": []
}
```

**Progress Tracking:**
```json
{
  "track_watch_time": true,
  "minimum_watch_percentage_for_completion": 80,
  "auto_mark_complete": false,
  "issue_certificates": true,
  "certificate_template_id": "default",
  "certificate_requires_quiz": false,
  "minimum_quiz_score": 70
}
```

**Currently Missing:**
- ⚠️ **Video streaming optimization** (CDN integration)
- ⚠️ **DRM/watermarking** (content protection)
- ⚠️ **Interactive elements** (quizzes, assessments)
- ⚠️ **Discussion forums** (per course/lesson)
- ⚠️ **Certificate generation system**

---

## 5. USER MANAGEMENT SETTINGS

### 5.1 Authentication & Security
**Location:** `/admin/settings/security`

**Account Settings:**
```json
{
  "registration_enabled": true,
  "registration_approval_required": false,
  "email_verification_required": true,
  "email_verification_timeout_hours": 24,
  "allow_social_login": true,
  "social_providers": ["google", "facebook", "apple"],
  "username_required": true,
  "username_min_length": 3,
  "username_max_length": 30,
  "password_min_length": 8,
  "password_require_uppercase": true,
  "password_require_lowercase": true,
  "password_require_number": true,
  "password_require_special_char": true,
  "password_expiry_days": 0
}
```

**Session Settings:**
```json
{
  "session_timeout_minutes": 1440,
  "session_remember_me_days": 30,
  "max_concurrent_sessions": 3,
  "force_logout_on_password_change": true,
  "two_factor_auth_enabled": false,
  "two_factor_required_for_admins": false,
  "ip_whitelist_enabled": false,
  "suspicious_activity_detection": true
}
```

**Data Privacy:**
```json
{
  "gdpr_compliance_enabled": true,
  "data_retention_days": 365,
  "allow_account_deletion": true,
  "account_deletion_grace_period_days": 30,
  "export_user_data_enabled": true,
  "anonymize_deleted_users": true,
  "cookie_consent_required": true,
  "terms_version": "1.0",
  "force_terms_acceptance": true
}
```

**Currently Missing:**
- ⚠️ **Account deletion workflow**
- ⚠️ **Data export functionality**
- ⚠️ **Cookie consent banner**
- ⚠️ **Privacy policy versioning**

---

## 6. ANALYTICS & REPORTING SETTINGS

### 6.1 Tracking Configuration
**Location:** `/admin/settings/analytics`

**Analytics Providers:**
```json
{
  "google_analytics_enabled": false,
  "google_analytics_id": "",
  "facebook_pixel_enabled": false,
  "facebook_pixel_id": "",
  "custom_tracking_enabled": true,
  "anonymize_ip": true,
  "track_user_behavior": true,
  "track_course_completion": true,
  "track_payment_funnel": true
}
```

**Reporting Settings:**
```json
{
  "reports_enabled": true,
  "export_formats": ["pdf", "excel", "csv"],
  "scheduled_reports_enabled": false,
  "email_reports_to": ["admin@oxiworld.com"],
  "report_frequency": "weekly|monthly|quarterly",
  "cache_reports_minutes": 15,
  "max_export_records": 10000
}
```

**Metrics to Track:**
```
✅ Already Tracking:
   ├── User registrations & growth
   ├── Subscription analytics (by plan, status)
   ├── Revenue metrics (MRR, ARR, churn)
   ├── Payment transactions
   ├── Course enrollments & completions
   ├── Telegram group membership
   └── Admin audit logs

⚠️ Missing Metrics:
   ├── User engagement (DAU, MAU, session duration)
   ├── Course completion rates (by lesson, by course)
   ├── Email campaign performance
   ├── Referral conversion rates
   ├── Customer lifetime value (CLV)
   ├── Churn prediction
   ├── Support ticket metrics
   └── System performance (API response times, errors)
```

---

## 7. SYSTEM & OPERATIONAL SETTINGS

### 7.1 Performance Settings
**Location:** `/admin/settings/system`

**Caching:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'oxidane',
        'TIMEOUT': 900  # 15 minutes default
    }
}

CACHE_SETTINGS = {
    'dashboard_metrics': 300,      # 5 minutes
    'pricing_plans': 3600,         # 1 hour
    'course_list': 900,            # 15 minutes
    'user_profile': 300,           # 5 minutes
    'analytics_reports': 900,      # 15 minutes
    'export_data': 900,            # 15 minutes
}
```

**Rate Limiting:**
```json
{
  "rate_limit_enabled": true,
  "default_rate_limit": "100/hour",
  "api_endpoints": {
    "/api/auth/login/": "5/minute",
    "/api/auth/register/": "3/hour",
    "/api/payment/initiate/": "10/hour",
    "/api/admin/*": "1000/hour"
  },
  "bypass_rate_limit_for_admins": true,
  "rate_limit_response_type": "429_error|captcha"
}
```

**File Storage:**
```json
{
  "storage_backend": "local|s3|cloudinary",
  "max_upload_size_mb": 50,
  "allowed_file_extensions": [
    "jpg", "jpeg", "png", "gif", "svg",
    "mp4", "webm", "mov",
    "pdf", "doc", "docx", "xls", "xlsx"
  ],
  "auto_delete_unused_files_days": 30,
  "cdn_enabled": false,
  "cdn_url": ""
}
```

**Currently Missing:**
- ⚠️ **Redis cache implementation** (currently using default/memory)
- ⚠️ **CDN integration** (for video delivery)
- ⚠️ **Background task queue** (Celery setup)
- ⚠️ **Database optimization** (indexing, partitioning)

---

### 7.2 Backup & Maintenance
**Location:** `/admin/settings/maintenance`

**Backup Settings:**
```json
{
  "auto_backup_enabled": false,
  "backup_frequency": "daily|weekly|monthly",
  "backup_time": "02:00",
  "backup_location": "local|s3|google_drive",
  "retain_backups_count": 30,
  "backup_includes": {
    "database": true,
    "media_files": true,
    "user_uploads": true,
    "logs": false
  },
  "backup_notifications": ["admin@oxiworld.com"]
}
```

**Maintenance Mode:**
```json
{
  "maintenance_mode_enabled": false,
  "maintenance_message": "We're currently upgrading our systems. We'll be back shortly!",
  "maintenance_bypass_ips": ["127.0.0.1"],
  "maintenance_bypass_admin": true,
  "maintenance_eta": null,
  "maintenance_page_custom_html": ""
}
```

**Health Monitoring:**
```json
{
  "health_checks_enabled": true,
  "check_frequency_minutes": 5,
  "checks": {
    "database": true,
    "redis_cache": true,
    "email_service": true,
    "telegram_bot": true,
    "external_apis": true,
    "disk_space": true
  },
  "alert_threshold_errors_per_hour": 10,
  "alert_recipients": ["admin@oxiworld.com"],
  "alert_methods": ["email", "telegram"]
}
```

---

## 8. NOTIFICATION & ALERT SETTINGS

### 8.1 Admin Notifications
**Location:** `/admin/settings/notifications`

**Critical Alerts:**
```json
{
  "new_payment_alert": {
    "enabled": true,
    "channels": ["email", "telegram"],
    "recipients": ["admin@oxiworld.com"],
    "threshold": 100.00,
    "message_template": "New payment: {{amount}} {{currency}} from {{user}}"
  },
  "failed_payment_alert": {
    "enabled": true,
    "channels": ["email"],
    "aggregate": true,
    "frequency": "hourly"
  },
  "new_user_registration": {
    "enabled": false,
    "channels": ["email"],
    "daily_digest": true
  },
  "system_error_alert": {
    "enabled": true,
    "channels": ["email", "telegram"],
    "severity_levels": ["error", "critical"]
  },
  "subscription_expiry_alert": {
    "enabled": true,
    "channels": ["telegram"],
    "advance_notice_days": 7,
    "daily_digest": true
  }
}
```

### 8.2 User Notifications
**Location:** User preferences + System defaults

**Notification Preferences (User Customizable):**
```json
{
  "default_preferences": {
    "email_notifications": {
      "payment_confirmation": true,
      "subscription_expiry_warning": true,
      "new_course_available": true,
      "lesson_completed": false,
      "marketing_emails": true,
      "newsletter": true
    },
    "telegram_notifications": {
      "signal_alerts": true,
      "group_announcements": true,
      "subscription_reminders": true
    },
    "in_app_notifications": {
      "payment_updates": true,
      "course_updates": true,
      "system_announcements": true
    }
  },
  "allow_user_customization": true,
  "notification_center_enabled": true,
  "notification_retention_days": 30
}
```

---

## 9. LOCALIZATION & TIMEZONE SETTINGS

### 9.1 Multi-Language Support
**Location:** `/admin/settings/localization`

**Language Settings:**
```json
{
  "default_language": "en",
  "supported_languages": ["en", "es", "fr", "pt"],
  "auto_detect_language": true,
  "allow_user_language_selection": true,
  "translate_emails": true,
  "translate_interface": true,
  "translate_course_content": false,
  "fallback_language": "en"
}
```

**Regional Settings:**
```json
{
  "default_timezone": "UTC",
  "detect_user_timezone": true,
  "display_dates_format": "MM/DD/YYYY",
  "display_time_format": "12h|24h",
  "first_day_of_week": "monday|sunday",
  "default_currency_display": "symbol|code",
  "number_format": {
    "decimal_separator": ".",
    "thousands_separator": ",",
    "decimal_places": 2
  }
}
```

---

## 10. ADVANCED FEATURES (FUTURE)

### 10.1 Features to Consider

**Community Features:**
- ⚠️ User forums/discussion boards
- ⚠️ Live chat support
- ⚠️ User-to-user messaging
- ⚠️ Leaderboards & gamification
- ⚠️ User profiles (public/private)
- ⚠️ Social sharing integration

**Learning Features:**
- ⚠️ Quizzes & assessments
- ⚠️ Certificates & badges
- ⚠️ Learning paths
- ⚠️ Personalized recommendations
- ⚠️ Note-taking system
- ⚠️ Bookmarks & favorites

**Business Intelligence:**
- ⚠️ Predictive analytics (churn, upsell)
- ⚠️ A/B testing framework
- ⚠️ Customer segmentation
- ⚠️ Automated marketing workflows
- ⚠️ Revenue forecasting
- ⚠️ Cohort analysis

**Mobile App Settings:**
- ⚠️ Push notification configuration
- ⚠️ Offline mode settings
- ⚠️ App version management
- ⚠️ Deep linking configuration

---

## 11. IMPLEMENTATION PRIORITY

### Phase 1: Critical (Immediate)
1. ✅ **Payment Gateway Integration** - Connect Paystack/Stripe
2. ⚠️ **Email Service Verification** - Ensure deliverability
3. ⚠️ **Telegram Bot Webhook** - Replace polling with webhooks
4. ⚠️ **Redis Cache Setup** - Performance optimization
5. ⚠️ **Backup System** - Data protection

### Phase 2: Essential (1-2 weeks)
1. ⚠️ **Settings UI Implementation** - Admin panel for all settings
2. ⚠️ **Currency Management** - Exchange rate system
3. ⚠️ **Coupon System Enhancement** - Advanced coupon features
4. ⚠️ **Rate Limiting** - API protection
5. ⚠️ **Error Monitoring** - Sentry or similar

### Phase 3: Important (1 month)
1. ⚠️ **Referral System** - User acquisition
2. ⚠️ **Analytics Dashboard Enhancement** - More metrics
3. ⚠️ **Email Campaign Manager** - Marketing automation
4. ⚠️ **CDN Integration** - Video delivery
5. ⚠️ **Certificate System** - Course completion

### Phase 4: Nice-to-Have (2-3 months)
1. ⚠️ **Multi-language Support** - i18n
2. ⚠️ **Community Features** - Forums, chat
3. ⚠️ **Mobile App** - iOS/Android
4. ⚠️ **Advanced Analytics** - Predictive models
5. ⚠️ **White-label Options** - Partner integration

---

## 12. CONFIGURATION FILE STRUCTURE

### Proposed Settings Organization

```
backend/oxidane/
├── settings/
│   ├── __init__.py
│   ├── base.py              # Base settings
│   ├── development.py        # Dev environment
│   ├── production.py         # Production environment
│   ├── testing.py           # Test environment
│   └── local.py             # Local overrides (gitignored)
├── config/
│   ├── pricing.json         # Pricing plan configs
│   ├── email_templates.json # Email template settings
│   ├── telegram.json        # Telegram bot settings
│   └── features.json        # Feature flags
```

**Database-Driven Settings:**
Create a `PlatformSettings` model:

```python
class PlatformSettings(models.Model):
    """Store platform-wide settings in database"""
    CATEGORIES = [
        ('payment', 'Payment & Pricing'),
        ('email', 'Email Configuration'),
        ('telegram', 'Telegram Integration'),
        ('courses', 'Course Management'),
        ('security', 'Security & Privacy'),
        ('analytics', 'Analytics & Reporting'),
        ('system', 'System Configuration'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORIES)
    key = models.CharField(max_length=100)
    value = models.JSONField()
    description = models.TextField()
    is_sensitive = models.BooleanField(default=False)
    requires_restart = models.BooleanField(default=False)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['category', 'key']
```

---

## 13. RECOMMENDATIONS

### Immediate Actions:

1. **Create Settings Management Page** (`/admin/settings`)
   - Categories: Payment, Email, Telegram, Courses, Security, System
   - Visual interface for non-technical admins
   - Validation before saving
   - Audit trail for all changes

2. **Migrate Hardcoded Values to Settings**
   - Move TELEGRAM_GROUPS to database
   - Move pricing logic to PricingPlan model
   - Environment-specific configs to proper files

3. **Implement Feature Flags**
   - Gradual rollout of new features
   - A/B testing capability
   - Easy enable/disable without deployment

4. **Documentation**
   - Admin guide for each setting
   - Default vs custom values
   - Impact assessment (what changes when settings update)

5. **Backup & Recovery**
   - Settings backup before changes
   - Rollback capability
   - Version history

---

## Questions for Discussion:

1. **Pricing Strategy:**
   - What should be the default prices for each plan?
   - Should we support multiple currencies from the start?
   - Auto-renewal by default or opt-in?

2. **Telegram Access:**
   - Should users be auto-added to groups or require manual verification?
   - How long should grace period be after subscription expires?
   - Should we have a public Telegram channel for marketing?

3. **Email Frequency:**
   - How many reminder emails before subscription expires?
   - Should we send renewal reminders after expiry?
   - Marketing email frequency limits?

4. **Course Access:**
   - Premium courses: subscription-based or one-time payment?
   - Should free courses require registration?
   - Concurrent device access limits?

5. **Data & Privacy:**
   - GDPR compliance required (EU users)?
   - Data retention period?
   - Allow users to delete their accounts?

6. **Analytics:**
   - Which external analytics tools to integrate?
   - Custom vs third-party analytics?
   - Data anonymization requirements?

---

## Next Steps:

1. **Review this document** and provide feedback
2. **Prioritize settings** based on business needs
3. **Design settings UI** (wireframes/mockups)
4. **Implement Phase 1** (critical settings)
5. **Test & iterate** with real data

---

**Document Version:** 1.0  
**Last Updated:** October 24, 2025  
**Author:** GitHub Copilot  
**Status:** Awaiting Review & Discussion
