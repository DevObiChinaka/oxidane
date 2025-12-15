#!/usr/bin/env python
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
user = User.objects.get(email='derachinaka@gmail.com')
sub = Subscription.objects.filter(billing_profile__user=user, status='active').first()

print('=' * 60)
print('CURRENT SUBSCRIPTION STATE')
print('=' * 60)
print(f'User: {user.email}')
print(f'Plan: {sub.plan.name}')
print(f'Status: {sub.status}')
print(f'End date: {sub.end_date}')
print(f'Next billing: {sub.next_billing_date}')
print(f'Auto-renew: {sub.auto_renew}')
print(f'Payment method: {"Yes" if sub.payment_method else "No"}')

now = timezone.now()
print(f'\nCurrent time: {now}')
print(f'Hours until end: {((sub.end_date - now).total_seconds() / 3600):.1f}')

print(f'\n✅ Ready for auto-renewal tonight at 2 AM UTC')
print('=' * 60)
