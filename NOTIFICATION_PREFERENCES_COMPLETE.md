# Notification Preferences System - Complete Implementation

## Overview
The notification preferences system allows users to control which email notifications they receive from the platform. This document describes the complete implementation including database models, API endpoints, frontend interface, and usage examples.

## Database Schema

### UserPreferences Model
Location: `backend/users/models.py`

```python
class UserPreferences(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences (all default to True except promotional_emails)
    email_login = models.BooleanField(default=True)
    course_updates = models.BooleanField(default=True)
    subscription_renewal = models.BooleanField(default=True)
    promotional_emails = models.BooleanField(default=False)
    signal_alerts = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Relationship**: Each user has exactly one UserPreferences instance (OneToOne).

## API Endpoints

### 1. Get Notification Preferences
**Endpoint**: `GET /api/auth/get-notifications/`  
**Authentication**: Required (JWT Bearer token)  
**Response**:
```json
{
  "preferences": {
    "emailLogin": true,
    "courseUpdates": true,
    "subscriptionRenewal": true,
    "promotionalEmails": false,
    "signalAlerts": true
  }
}
```

### 2. Update Notification Preferences
**Endpoint**: `POST /api/auth/update-notifications/`  
**Authentication**: Required (JWT Bearer token)  
**Request Body**:
```json
{
  "emailLogin": false,
  "courseUpdates": true,
  "subscriptionRenewal": true,
  "promotionalEmails": true,
  "signalAlerts": true
}
```
**Response**:
```json
{
  "message": "Notification preferences updated successfully",
  "success": true,
  "preferences": {
    "emailLogin": false,
    "courseUpdates": true,
    "subscriptionRenewal": true,
    "promotionalEmails": true,
    "signalAlerts": true
  }
}
```

## Frontend Implementation

### Settings Page
Location: `frontend/src/app/settings/page.tsx`

The Notifications tab provides toggle switches for each notification type:

1. **Login Notifications** - Get notified when someone logs into your account
2. **Course Updates** - Receive updates about new lessons and course materials
3. **Subscription Renewal** - Get reminders before your subscription renews
4. **Signal Alerts** - Receive trading signal notifications
5. **Promotional Emails** - Receive promotional offers and marketing emails

**Features**:
- Loads existing preferences on page load
- Real-time toggle switches with animations
- Automatic save with success feedback
- Professional UI with dark theme

## Usage in Email Sending

### Helper Functions
Location: `backend/users/notification_helpers.py`

#### Check if notification should be sent:
```python
from users.notification_helpers import should_send_notification

# Before sending login notification
if should_send_notification(user, 'email_login'):
    send_login_notification_email(user)

# Before sending course update
if should_send_notification(user, 'course_updates'):
    send_course_update_email(user, course)
```

#### Get all user preferences:
```python
from users.notification_helpers import get_user_preferences

preferences = get_user_preferences(user)
# Returns: {'email_login': True, 'course_updates': True, ...}
```

## Admin Interface

### Django Admin
Access: `http://localhost:8000/admin/users/userpreferences/`

**Features**:
- View all user preferences in a list
- Filter by any notification type
- Search by user email or name
- Bulk edit preferences using list_editable
- Individual preference management

**List Display**:
- User email
- All notification toggle states
- Last updated timestamp

## Default Values

When a new user registers or UserPreferences is first created:
- ✅ **email_login**: True (security notifications should be enabled by default)
- ✅ **course_updates**: True (educational content is core to the platform)
- ✅ **subscription_renewal**: True (important billing information)
- ❌ **promotional_emails**: False (opt-in for marketing)
- ✅ **signal_alerts**: True (trading signals are a key feature)

## Testing

### Test Script
Location: `backend/test_notifications.py`

Run tests:
```bash
cd backend
python test_notifications.py
```

Tests verify:
1. Preferences creation with defaults
2. Preferences updates persist to database
3. Preferences can be retrieved correctly
4. Admin display strings work properly

## Migration

### Database Migration
```bash
cd backend
python manage.py makemigrations users
python manage.py migrate
```

This creates the `users_userpreferences` table with all necessary fields.

## Integration Examples

### Example 1: Login Notification
```python
from users.notification_helpers import should_send_notification
from users.email_automation import send_login_notification

def on_user_login(user, ip_address):
    if should_send_notification(user, 'email_login'):
        send_login_notification(
            user=user,
            ip_address=ip_address,
            device_info=get_device_info()
        )
```

### Example 2: Course Update
```python
def notify_users_of_course_update(course):
    enrolled_users = course.enrolled_users.all()
    
    for user in enrolled_users:
        if should_send_notification(user, 'course_updates'):
            send_course_update_email(user, course)
```

### Example 3: Subscription Renewal Reminder
```python
def send_renewal_reminders():
    expiring_subscriptions = get_expiring_subscriptions(days=7)
    
    for subscription in expiring_subscriptions:
        user = subscription.user
        if should_send_notification(user, 'subscription_renewal'):
            send_renewal_reminder_email(user, subscription)
```

## Future Enhancements

Potential additions to the notification system:

1. **SMS Notifications**: Add phone number and SMS preferences
2. **Push Notifications**: Browser push notification toggles
3. **Notification Frequency**: Daily digest vs real-time options
4. **Category Preferences**: More granular control (e.g., specific course types)
5. **Quiet Hours**: Schedule when notifications should not be sent
6. **Notification History**: Log of all notifications sent to user

## Security Considerations

1. **Authentication Required**: All preference endpoints require valid JWT tokens
2. **User Isolation**: Users can only view/edit their own preferences
3. **Default Safe**: Defaults favor security notifications (login alerts)
4. **Audit Trail**: created_at and updated_at timestamps for tracking changes

## Status

✅ **Fully Functional** - The notification preferences system is complete and ready for production use.

### Completed Components:
- ✅ Database model (UserPreferences)
- ✅ Database migration applied
- ✅ Backend API endpoints (get/update)
- ✅ Frontend UI (Settings page with toggles)
- ✅ Helper functions for email integration
- ✅ Django admin interface
- ✅ Test scripts and validation
- ✅ Documentation

### Next Steps:
1. Integrate `should_send_notification()` into existing email sending functions
2. Add notification preferences to user onboarding flow
3. Create email notification history tracking
4. Add analytics for notification engagement
