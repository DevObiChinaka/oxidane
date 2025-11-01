"""
Notification Preferences Helper

This module provides helper functions to check user notification preferences
before sending emails.
"""

from users.models import User, UserPreferences


def should_send_notification(user, notification_type):
    """
    Check if a notification should be sent to a user based on their preferences.
    
    Args:
        user: User instance
        notification_type: String - one of:
            - 'email_login': Login notifications
            - 'course_updates': Course update notifications
            - 'subscription_renewal': Subscription renewal reminders
            - 'promotional_emails': Marketing/promotional emails
            - 'signal_alerts': Trading signal notifications
    
    Returns:
        bool: True if notification should be sent, False otherwise
    """
    try:
        # Get or create preferences with defaults
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        
        # Map notification type to preference field
        preference_mapping = {
            'email_login': preferences.email_login,
            'course_updates': preferences.course_updates,
            'subscription_renewal': preferences.subscription_renewal,
            'promotional_emails': preferences.promotional_emails,
            'signal_alerts': preferences.signal_alerts,
        }
        
        # Return preference value, default to True if type not found
        return preference_mapping.get(notification_type, True)
        
    except Exception as e:
        # If any error occurs, default to sending the notification
        print(f"Error checking notification preferences: {e}")
        return True


def get_user_preferences(user):
    """
    Get all notification preferences for a user.
    
    Args:
        user: User instance
    
    Returns:
        dict: Dictionary of all notification preferences
    """
    try:
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        
        return {
            'email_login': preferences.email_login,
            'course_updates': preferences.course_updates,
            'subscription_renewal': preferences.subscription_renewal,
            'promotional_emails': preferences.promotional_emails,
            'signal_alerts': preferences.signal_alerts,
        }
    except Exception as e:
        print(f"Error getting user preferences: {e}")
        # Return defaults
        return {
            'email_login': True,
            'course_updates': True,
            'subscription_renewal': True,
            'promotional_emails': False,
            'signal_alerts': True,
        }
