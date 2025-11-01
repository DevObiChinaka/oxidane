# 🎛️ Admin Settings - Complete Structure & Organization

**Date:** October 24, 2025  
**Purpose:** Organize all platform configurations under Settings section

---

## 📍 CURRENT SETTINGS SECTION

```
Settings
├── Platform Settings  (/admin/settings)
└── Email Templates    (/admin/emails)
```

---

## 🎯 REFINED SETTINGS STRUCTURE

### **Current Admin Sidebar Structure:**

```
Overview
├── Dashboard
└── Analytics

Content Management
├── Courses
└── Lessons

User Management
├── Users
├── Signal Subscriptions
├── Mentorship Program
└── Telegram Queue

Financial
├── Pricing Plans           [EXISTING - Manage subscription plans]
├── Payments
└── Revenue Reports

Settings                     [👈 WE'RE ORGANIZING THIS]
├── Platform Settings       [EXISTING - Currently empty/placeholder]
└── Email Templates         [EXISTING - Already functional at /admin/emails]
```

### **NEW Settings Pages to Build:**

```
Settings Section (in Admin Sidebar)
│
├── ⚙️  Platform Settings      (/admin/settings)  [CURRENT PLACEHOLDER]
│   └── General platform configuration, branding, localization
│
├── 💳 Payment Gateway         (/admin/settings/payment-gateway)  [NEW]
│   └── Paystack/Stripe configuration & credentials
│
├── 📧 Email Configuration     (/admin/settings/email-config)  [NEW]
│   └── SMTP settings, email service, sending limits
│
├── 💬 Telegram Integration    (/admin/settings/telegram)  [NEW]
│   └── Bot config, groups, access rules (move from hardcoded)
│
├── 📚 Course Settings         (/admin/settings/courses)  [NEW]
│   └── Video uploads, player settings, certificates
│
├── 👥 User & Security         (/admin/settings/security)  [NEW]
│   └── Registration rules, authentication, passwords, 2FA
│
├── 🔔 Notifications           (/admin/settings/notifications)  [NEW]
│   └── Admin alerts, user notification preferences
│
├── 🛠️  System                 (/admin/settings/system)  [NEW]
│   └── Cache, backups, maintenance mode, health status
│
├── ✉️  Email Templates        (/admin/emails)  [EXISTING - Keep as is]
│   └── Already functional, no changes needed
│
└── ⚖️  Legal & Compliance     (/admin/settings/legal)  [NEW - Future]
    └── Terms, Privacy Policy (lower priority)
```

### **What Stays in Main Navigation:**

```
Financial Section (NO CHANGES)
├── 💰 Pricing Plans          [Keep here - active business tool]
├── 💳 Payments               [Keep here - transaction management]
└── 📊 Revenue Reports        [Keep here - financial analytics]
```

---

## 📋 DETAILED BREAKDOWN - PAGES TO BUILD

### **1. ⚙️ Platform Settings** (`/admin/settings`)
**Status:** Currently exists but empty/placeholder  
**Priority:** 🔴 Critical

**What to Include:**
```
Platform Information
├── Platform Name: "OxiWorld Forex Academy"
├── Tagline: "Master Forex Trading with Expert Mentorship"
├── Support Email: support@oxiworld.com
├── Contact Phone: +234-XXX-XXX-XXXX
└── Website URL: https://oxiworld.com

Localization
├── Timezone: UTC / WAT / EAT
├── Date Format: MM/DD/YYYY / DD/MM/YYYY
├── Time Format: 12h / 24h
└── Default Language: English

Branding
├── Logo Upload (Light & Dark versions)
├── Favicon Upload
├── Primary Color: #000ABE
└── Secondary Color: #00B38F

Platform Status
├── ○ Active (Public)
├── ○ Maintenance Mode
└── ○ Read-Only Mode
```

---

### **2. 💳 Payment Gateway** (`/admin/settings/payment-gateway`)
**Status:** New page to build  
**Priority:** 🔴 Critical (for Phase 2 - User Payments)

**What to Include:**
```
Primary Payment Provider
├── ○ Paystack (Recommended for Nigeria)
├── ○ Stripe (International)
└── ○ Manual Bank Transfer

Paystack Configuration
├── Public Key: pk_test_xxxxx
├── Secret Key: sk_test_xxxxx (encrypted)
├── Mode: Test / Production
├── Webhook URL: (auto-generated)
└── Status: ✅ Connected / ⚠️ Test Mode / ❌ Disconnected

Stripe Configuration (Optional)
├── Publishable Key
├── Secret Key (encrypted)
├── Mode: Test / Production
└── Webhook URL

Payment Methods
├── [✓] Card Payments (Visa, Mastercard)
├── [✓] Bank Transfer
├── [✓] USSD
└── [ ] Mobile Money

Transaction Settings
├── Auto-Verify Payments: Yes/No
├── Payment Timeout: 30 minutes
├── Failed Payment Retries: 3
└── Minimum Payment: $1.00

[Test Connection] [Save Changes]
```

---

### **3. 📧 Email Configuration** (`/admin/settings/email-config`)
**Status:** New page to build  
**Priority:** 🔴 Critical

**What to Include:**
```
Email Provider
├── ● Gmail SMTP (Current)
├── ○ SendGrid
├── ○ AWS SES
└── ○ Mailgun

SMTP Settings
├── Host: smtp.gmail.com
├── Port: 465
├── Encryption: SSL / TLS / None
├── Username: noreply@oxiworld.com
├── Password: ••••••••• (encrypted)
└── Timeout: 30 seconds

Email Addresses
├── From Email: noreply@oxiworld.com
├── From Name: OxiWorld Forex Academy
├── Reply-To: support@oxiworld.com
└── BCC Admin on Orders: Yes/No

Sending Limits
├── Daily Limit per User: 5 emails
├── Hourly Rate Limit: 100 emails
├── Marketing Emails: Enabled/Disabled
└── Email Status: Active / Paused

Email Tracking
├── Track Opens: Yes/No
├── Track Clicks: Yes/No
└── Unsubscribe Link: Always Include

[Send Test Email] [Save Changes]

Status: ✅ Email service active
Last test: Oct 24, 2025 10:30 AM
```

---

### **4. 💬 Telegram Integration** (`/admin/settings/telegram`)
**Status:** New page to build (move from hardcoded settings.py)  
**Priority:** 🔴 Critical

**What to Include:**
```
Bot Configuration
├── Bot Token: 8386662254:AAF... (encrypted)
├── Bot Username: @OxiWorldBot
├── Bot Status: ✅ Active / ❌ Disconnected
├── Connection: Polling / Webhook
└── [Test Bot Connection]

Telegram Groups (Editable List)
┌─────────────────────────────────────────┐
│ 📢 Premium Signals Group                │
│ Chat ID: -1002920074390                 │
│ Access Level: Monthly+ subscribers      │
│ Members: 89                              │
│ [Edit] [View Members] [Test Add User]   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🎓 Education/Mentorship Group           │
│ Chat ID: -4885168917                    │
│ Access Level: All paid subscribers      │
│ Members: 234                             │
│ [Edit] [View Members]                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ⭐ VIP Community Group                  │
│ Chat ID: -4811814960                    │
│ Access Level: VIP only                  │
│ Members: 14                              │
│ [Edit] [View Members]                    │
└─────────────────────────────────────────┘

[+ Add New Group]

Access Control
├── Auto-Add Verified Users: Yes/No
├── Auto-Remove Expired: Yes/No
├── Verification Method: Both / Username / User ID
└── Grace Period After Expiry: 24 hours

Welcome & Notifications
├── Send Welcome Messages: Yes/No
├── Welcome Message Template: [Edit]
├── Send Expiry Warnings: Yes/No
├── Warning Days: [7, 3, 1]
└── Removal Notification: Yes/No

[Save Changes]
```

**Note:** This replaces hardcoded `TELEGRAM_GROUPS` in settings.py

---

### **5. 📚 Course Settings** (`/admin/settings/courses`)
**Status:** New page to build  
**Priority:** 🟡 Important (for Phase 3 - Course Platform)

**What to Include:**
```
Course Access
├── Free Course Registration: Required / Not Required
├── Course Preview: Enabled/Disabled
├── Preview Lessons: 1 lesson
├── Concurrent Devices: 2
└── Download Content: Enabled/Disabled

Video Settings
├── Max Upload Size: 500 MB
├── Allowed Formats: [✓] MP4 [✓] WebM [ ] MOV
├── Default Quality: Auto / 720p / 1080p
├── Adaptive Streaming: Enabled/Disabled
└── Video Processing: Auto-optimize

Progress Tracking
├── Track Watch Time: Yes/No
├── Auto-Mark Complete at: 80%
├── Minimum Watch Time: 30 seconds
└── Save Progress Interval: 10 seconds

Certificates
├── Issue Certificates: Yes/No
├── Completion Required: 100%
├── Certificate Template: Default
└── Include Date: Yes/No

Content Protection
├── Video Watermark: Enabled/Disabled
├── Disable Right-Click: Yes/No
├── Screen Recording Alert: Yes/No
└── Geographic Restrictions: None

[Save Changes]
```

---

### **6. 👥 User & Security** (`/admin/settings/security`)
**Status:** New page to build  
**Priority:** 🟡 Important

**What to Include:**
```
Registration Settings
├── Allow New Registrations: Yes/No
├── Email Verification: Required / Optional
├── Admin Approval: Required / Not Required
├── Default User Role: Student
└── Send Welcome Email: Yes/No

Authentication
├── Social Login: Enabled/Disabled
│   ├── [✓] Google OAuth
│   ├── [ ] Facebook (Future)
│   └── [ ] Apple (Future)
├── Session Timeout: 1440 minutes (24h)
├── Max Concurrent Sessions: 3
└── Remember Me Duration: 30 days

Password Requirements
├── Minimum Length: 8 characters
├── Require Uppercase: Yes/No
├── Require Lowercase: Yes/No
├── Require Numbers: Yes/No
├── Require Special Characters: Yes/No
└── Password Expiry: Never / 90 days

Security Features
├── Two-Factor Auth: Disabled / Optional / Required
├── Require 2FA for Admins: Yes/No
├── Max Login Attempts: 5
├── Lockout Duration: 30 minutes
└── Admin IP Whitelist: Disabled

Account Management
├── Allow Account Deletion: Yes/No
├── Deletion Grace Period: 30 days
├── Export User Data (GDPR): Enabled/Disabled
└── Anonymize Deleted Users: Yes/No

Privacy & Compliance
├── GDPR Compliance: Enabled/Disabled
├── Cookie Consent: Required/Optional
├── Data Retention: 365 days
└── Terms Acceptance: Required/Optional

[Save Changes]
```

---

### **7. 🔔 Notifications** (`/admin/settings/notifications`)
**Status:** New page to build  
**Priority:** 🟢 Nice-to-Have

**What to Include:**
```
Admin Alerts (When to notify admins)
┌──────────────────────────────────────┐
│ 💳 New Payment Received              │
│ Notify via: [✓] Email [✓] Telegram  │
│ Threshold: $100+ only                │
│ Frequency: Immediately / Daily Digest│
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ ❌ Payment Failed                    │
│ Notify via: [✓] Email [ ] Telegram  │
│ Frequency: Daily Digest              │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 👤 New User Registration             │
│ Notify via: [ ] Email [ ] Telegram  │
│ Frequency: Weekly Digest             │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🚨 System Errors                     │
│ Notify via: [✓] Email [✓] Telegram  │
│ Severity: Critical & Error only      │
│ Frequency: Immediately               │
└──────────────────────────────────────┘

Alert Recipients
├── Primary Email: admin@oxiworld.com
├── Secondary Email: ops@oxiworld.com
└── Telegram Chat ID: -123456789

User Notification Defaults
├── Payment Confirmation: Enabled
├── Subscription Expiry Warning: 7, 3, 1 days
├── New Course Available: Enabled
├── Course Completion: Disabled
├── Marketing Emails: Enabled
└── Newsletter: Enabled

Notification Limits
├── Max Emails per User/Day: 5
├── Quiet Hours: Disabled
└── User Timezone: Respect user's timezone

[Save Changes]
```

---

### **8. 🛠️ System** (`/admin/settings/system`)
**Status:** New page to build  
**Priority:** 🟡 Important

**What to Include:**
```
Maintenance Mode
├── Status: ○ Active  ● Disabled
├── Message: "We're upgrading our systems..."
├── Estimated ETA: 2 hours
├── Bypass IPs: 127.0.0.1, admin IPs
├── Allow Admin Access: Yes/No
└── [Enable Maintenance Mode]

Caching
├── Cache Enabled: Yes/No
├── Cache Driver: Redis / File / Database
├── Default Duration: 15 minutes
├── Cache Size: 45.3 MB / 500 MB
└── [Clear All Cache]

Cache Settings by Type
├── Dashboard Metrics: 5 minutes
├── Course Listings: 15 minutes
├── User Profiles: 5 minutes
└── Analytics Reports: 15 minutes

Backups
├── Auto Backup: Enabled/Disabled
├── Frequency: Daily / Weekly
├── Backup Time: 02:00 UTC
├── Retain Backups: 30 days
├── Backup Location: Local / AWS S3
└── Last Backup: Oct 24, 2025 02:15 AM ✅

[Create Backup Now] [Restore from Backup]

System Health Status
┌──────────────────────────────────────┐
│ Database:         ✅ Connected       │
│ Redis Cache:      ✅ Active          │
│ Email Service:    ✅ Operational     │
│ Telegram Bot:     ✅ Connected       │
│ Payment Gateway:  ⚠️  Test Mode      │
│ Storage:          ✅ 23.4GB / 100GB  │
└──────────────────────────────────────┘

Performance
├── API Rate Limiting: Enabled/Disabled
├── Default Rate: 100 requests/hour
├── Admin Bypass: Yes/No
└── [View Rate Limit Rules]

[View System Logs] [Restart Services]
```

---

### **9. ⚖️ Legal & Compliance** (`/admin/settings/legal`)
**Status:** New page to build  
**Priority:** 🟢 Future (Month 2)

**What to Include:**
```
Legal Documents
┌──────────────────────────────────────┐
│ 📄 Terms & Conditions                │
│ Version: v1.2                         │
│ Last Updated: Oct 15, 2025            │
│ [Edit] [Preview] [Version History]   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🔒 Privacy Policy                    │
│ Version: v1.1                         │
│ Last Updated: Oct 10, 2025            │
│ [Edit] [Preview] [Version History]   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 💰 Refund Policy                     │
│ Version: v1.0                         │
│ [Edit] [Preview]                      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🍪 Cookie Policy                     │
│ [Edit] [Preview]                      │
└──────────────────────────────────────┘

Display Settings
├── Show in Footer: All documents
├── Show on Registration: Terms only
├── Force Re-acceptance on Update: Yes/No
└── Acceptance Required: Mandatory

Compliance
├── GDPR Compliant: Yes/No
├── Data Controller: OxiWorld Ltd
├── DPO Contact: dpo@oxiworld.com
└── Cookie Consent Banner: Enabled

[Save Changes]
```

---

## 🎨 IMPLEMENTATION STRATEGY

### **Build Order (Recommended):**

**🔴 PHASE 1: Critical Settings (Week 1-2)**
Build these 4 pages first - most important for platform operation:

1. ✅ **Platform Settings** (`/admin/settings`)
   - Replace empty placeholder with actual functionality
   - Platform info, branding, timezone
   - **Estimated:** 2-3 days

2. ✅ **Email Configuration** (`/admin/settings/email-config`)
   - Visual SMTP editor (currently in settings.py)
   - Test email functionality
   - **Estimated:** 2-3 days

3. ✅ **Telegram Integration** (`/admin/settings/telegram`)
   - Move hardcoded groups from settings.py to database
   - Visual group manager
   - **Estimated:** 3-4 days

4. ✅ **System Health** (`/admin/settings/system`)
   - Maintenance mode toggle
   - Cache management
   - System status dashboard
   - **Estimated:** 2-3 days

**Total Phase 1:** ~10-12 days

---

**🟡 PHASE 2: Important Settings (Week 3-4)**
Build when implementing user payments:

5. ⏳ **Payment Gateway** (`/admin/settings/payment-gateway`)
   - Paystack/Stripe configuration
   - Build when implementing Phase 2 of roadmap (Payments)
   - **Estimated:** 3-4 days

6. ⏳ **User & Security** (`/admin/settings/security`)
   - Registration, auth, 2FA settings
   - Build before public launch
   - **Estimated:** 3-4 days

**Total Phase 2:** ~7 days

---

**🟢 PHASE 3: Enhancement Settings (Week 5-6)**
Build as platform matures:

7. ⏳ **Course Settings** (`/admin/settings/courses`)
   - Build when implementing Phase 3 of roadmap (Course Platform)
   - **Estimated:** 2-3 days

8. ⏳ **Notifications** (`/admin/settings/notifications`)
   - Fine-tune alert preferences
   - **Estimated:** 2-3 days

9. ⏳ **Legal & Compliance** (`/admin/settings/legal`)
   - Policy editor with versioning
   - **Estimated:** 3-4 days

**Total Phase 3:** ~8 days

---

### **Summary by Priority:**

| Priority | Pages to Build | Time | When |
|----------|---------------|------|------|
| 🔴 Critical | 4 pages | 2 weeks | Now (Phase 1) |
| 🟡 Important | 2 pages | 1 week | Before user payments |
| 🟢 Nice-to-Have | 3 pages | 1.5 weeks | As platform grows |

**Total:** 9 new settings pages over ~4-5 weeks (alongside other development)

---

### **What Doesn't Change:**

✅ **Keep These As-Is:**
- `/admin/pricing` - Pricing Plans (in Financial section)
- `/admin/emails` - Email Templates (functional, keep in Settings)
- All other admin pages (Courses, Users, Payments, etc.)

---

## 📊 DATABASE MODEL

```python
# backend/settings/models.py

class PlatformSetting(models.Model):
    """Single source of truth for all platform settings"""
    category = models.CharField(max_length=20)  # platform, pricing, email, etc.
    key = models.CharField(max_length=100)      # smtp_host, platform_name, etc.
    value = models.JSONField()                   # Flexible storage
    is_encrypted = models.BooleanField(default=False)  # For passwords, API keys
    description = models.TextField(blank=True)
    
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['category', 'key']
```

---

## 🚀 RECOMMENDED APPROACH

**Option: Build Incrementally**

1. **Week 1:** Settings layout + Platform Settings + Pricing & Plans
2. **Week 2:** Telegram Integration + Email Configuration
3. **Week 3:** Payment Gateway + Course Settings
4. **Week 4:** User & Security + Notifications
5. **Month 2:** System & Maintenance + Legal

**Benefits:**
- Ship value quickly (can use Platform Settings immediately)
- Test each piece thoroughly
- Adjust based on feedback
- Lower risk of bugs

---

## 💡 KEY FEATURES TO INCLUDE

1. **Visual Indicators:** Connection status (✅ Active, ⚠️ Test Mode, ❌ Failed)
2. **Test Buttons:** Test email, test payment, test Telegram bot
3. **Encryption:** Auto-encrypt sensitive fields (passwords, API keys)
4. **Audit Trail:** Track who changed what and when
5. **Backup/Restore:** Save settings before major changes
6. **Validation:** Prevent invalid configs from being saved
7. **Help Text:** Tooltips explaining each setting
8. **Search:** Quick search across all settings

---

## 📞 NEXT DISCUSSION POINTS

1. **Should we start with the Settings infrastructure first?** (Layout, navigation, models)
2. **Which specific page should we build first?** (I recommend Platform Settings - simplest)
3. **Do you want placeholders for all pages or build one at a time?**
4. **Should sensitive data like API keys be editable via UI or keep in .env?** (I recommend DB with encryption)

**Ready to start building when you are!** 🎯
