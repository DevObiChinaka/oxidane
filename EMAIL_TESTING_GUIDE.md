# Email System Testing Guide

## Quick Start

### 1. Seed System Emails (First Time Only)
```bash
cd backend
python manage.py seed_system_emails
```

This creates 11 protected email templates:
- Email Verification
- Password Reset
- Sign-in Alert
- Payment Confirmation/Failed/Refunded
- Subscription Activated/Expiring/Renewed
- Telegram Added/Removed

### 2. Run Integration Tests
```bash
cd backend
python test_email_system.py
```

This will test:
- ✅ System email templates exist
- ✅ Protection mechanisms work
- ✅ Gmail SMTP sends emails
- ✅ EmailLog entries are created
- ✅ Subscription filtering works

### 3. Manual Testing in UI

**Access the Email Management Page:**
```
http://localhost:3000/admin/emails
```

**Test Each Tab:**

#### Tab 1: System Emails
- [ ] See all 11 system templates
- [ ] "Always Active" badge visible
- [ ] Edit button works (can modify content)
- [ ] Preview button shows email
- [ ] No Delete button present
- [ ] Try to deactivate via Edit → should fail with error

#### Tab 2: Custom Templates
- [ ] Create new template button works
- [ ] Select template type auto-fills suggestions
- [ ] HTML editor works
- [ ] Preview shows correct rendering
- [ ] Send button opens SendEmailModal
- [ ] Delete button works for custom templates

#### Tab 3: Recent Activity
- [ ] Shows last 50 sent emails
- [ ] Displays recipient, template, status, timestamp
- [ ] Status badges colored correctly (green=sent, red=failed)
- [ ] Refresh button reloads data

### 4. Test Email Sending

**Via UI (SendEmailModal):**

1. Go to Custom Templates tab
2. Click Send on any template (or create test template)
3. Test each recipient type:
   - [ ] All Users
   - [ ] Active Subscribers
   - [ ] Inactive Users
   - [ ] By Subscription Plan (select weekly/monthly/etc)
   - [ ] Specific Users

4. Check Results:
   - [ ] Success notification appears
   - [ ] Shows sent/failed counts
   - [ ] Recent Activity tab updates
   - [ ] EmailLog entries created

**Via Test Script:**
```bash
cd backend
python test_email_system.py
# Enter your email when prompted
```

### 5. Test System Email Triggers

**Email Verification:**
```bash
# Register new user, check they receive verification email
```

**Password Reset:**
```bash
# Use "Forgot Password" flow, check email received
```

**Payment Emails:**
```bash
# Make test payment, check success/failure emails
```

**Subscription Emails:**
```bash
# Subscribe to plan, check activation email
# Wait for expiry date, check expiry reminder
```

### 6. Test Protection Mechanisms

**Try to Delete System Email (Should Fail):**
1. Call API directly:
```bash
curl -X DELETE http://127.0.0.1:8000/api/admin/email-templates/{system_email_id}/ \
  -H "Authorization: Bearer {your_token}"
```
Expected: 403 error with message about system emails

**Try to Deactivate System Email (Should Fail):**
1. Call API:
```bash
curl -X PUT http://127.0.0.1:8000/api/admin/email-templates/{system_email_id}/ \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```
Expected: 403 error

### 7. Gmail SMTP Configuration

**Required .env Variables:**
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
EMAIL_USE_TLS=True
```

**Get Gmail App Password:**
1. Go to Google Account Settings
2. Security → 2-Step Verification
3. App Passwords → Generate new
4. Use generated password in .env

### 8. Troubleshooting

**Emails not sending:**
- Check .env has correct Gmail credentials
- Verify EMAIL_USE_TLS=True
- Check Django logs: `tail -f backend/logs/django.log`
- Test SMTP directly:
```python
from django.core.mail import send_mail
send_mail('Test', 'Body', 'from@email.com', ['to@email.com'])
```

**EmailLog not created:**
- Check email_service.py creates log entries
- Verify EmailLog model imported correctly
- Check database: `python manage.py dbshell` → `SELECT * FROM users_emaillog;`

**Subscription filtering not working:**
- Ensure SubscriptionPlan model has billing_period field
- Check Subscription model links to SubscriptionPlan
- Verify users have active subscriptions

**Frontend errors:**
- Check browser console for API errors
- Verify backend server running: `python manage.py runserver`
- Check API endpoints return expected data format

## Success Criteria

### MVP Complete When:
- [x] 11 system emails auto-created
- [x] System emails cannot be deleted
- [x] System emails cannot be deactivated
- [x] 3-tab UI implemented
- [x] Custom template CRUD works
- [x] Email sending with filtering works
- [x] Subscription plan filtering works
- [x] Recent activity tab shows logs
- [ ] Gmail SMTP sends emails successfully
- [ ] EmailLog entries created on send
- [ ] All protection mechanisms tested

## Production Checklist

Before deploying to production:
- [ ] Run `python manage.py seed_system_emails` on production DB
- [ ] Configure production Gmail credentials
- [ ] Test all 11 system email types send correctly
- [ ] Verify EmailLog storage working
- [ ] Test subscription plan filtering with real data
- [ ] Backup email templates
- [ ] Set up email delivery monitoring
- [ ] Configure rate limits for bulk sends
- [ ] Test error handling for failed sends
