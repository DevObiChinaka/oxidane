#!/usr/bin/env python
"""Test admin OTP login endpoint"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

User = get_user_model()

# Check admin user
admin = User.objects.filter(email='oxiworldforexacademy@gmail.com').first()
if admin:
    print(f"✓ User found: {admin.email}")
    print(f"  is_staff: {admin.is_staff}")
    print(f"  is_superuser: {admin.is_superuser}")
    print(f"  is_active: {admin.is_active}")
    
    # Test password
    test_password = 'L@undr0m@t987!'
    if check_password(test_password, admin.password):
        print(f"✓ Password matches!")
    else:
        print(f"✗ Password does NOT match")
        print(f"  Trying to set new password...")
        admin.set_password(test_password)
        admin.save()
        print(f"✓ Password updated!")
else:
    print("✗ Admin user not found!")
