#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

print("\n=== Email Templates Status ===\n")

payment_types = [
    'payment_success',
    'payment_failed', 
    'payment_refunded',
    'subscription_success',
    'subscription_expiry',
    'renewal_reminder'
]

for template_type in payment_types:
    templates = EmailTemplate.objects.filter(template_type=template_type)
    if templates.exists():
        t = templates.first()
        print(f"✓ {template_type}: {t.name} ({t.status})")
    else:
        print(f"✗ {template_type}: NOT FOUND")

print(f"\nTotal templates: {EmailTemplate.objects.count()}")
print(f"Active templates: {EmailTemplate.objects.filter(status='active').count()}")
