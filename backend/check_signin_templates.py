#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

# Check for signin-related templates
templates = EmailTemplate.objects.filter(
    template_type__in=['user_login_otp', 'user_signin_notification', 'signin_notification']
)

print("\n" + "="*60)
print("SIGNIN EMAIL TEMPLATES CHECK")
print("="*60)

if templates.exists():
    print(f"\nFound {templates.count()} signin templates:\n")
    for t in templates:
        print(f"✓ {t.template_type}")
        print(f"  Name: {t.name}")
        print(f"  Status: {t.status}")
        print(f"  Default: {t.is_default}")
        print()
else:
    print("\n❌ NO SIGNIN TEMPLATES FOUND!\n")
    print("Templates need to be created using:")
    print("  - create_user_signin_templates.py")
    print("  - create_signin_templates.py")

print("="*60)
