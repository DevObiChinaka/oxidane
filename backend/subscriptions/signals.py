"""
Signals for automatic BillingProfile creation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import BillingProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_billing_profile(sender, instance, created, **kwargs):
    """
    Automatically create a BillingProfile when a new user is created.
    This ensures every user has a billing profile ready for subscriptions.
    """
    if created:
        BillingProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_billing_profile(sender, instance, **kwargs):
    """
    Save the billing profile whenever the user is saved.
    Creates one if it doesn't exist (edge case handling).
    """
    if not hasattr(instance, 'billing_profile'):
        BillingProfile.objects.create(user=instance)
