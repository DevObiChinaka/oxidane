#!/usr/bin/env python
"""Test OTP authentication flows"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("OTP AUTHENTICATION SYSTEM STATUS")
print("=" * 60)

# Admin users
print("\n📊 ADMIN USERS:")
admins = User.objects.filter(is_staff=True, is_active=True)
for admin in admins:
    print(f"  ✓ {admin.email}")
    print(f"    - is_superuser: {admin.is_superuser}")
    print(f"    - email_verified: {admin.is_email_verified}")

# Regular users
print("\n👥 REGULAR USERS:")
users = User.objects.filter(is_staff=False, is_active=True)[:5]
if users:
    for user in users:
        print(f"  ✓ {user.email}")
        print(f"    - email_verified: {user.is_email_verified}")
        print(f"    - name: {user.first_name} {user.last_name}")
else:
    print("  ⚠️  No regular users found")

print("\n" + "=" * 60)
print("ENDPOINTS AVAILABLE:")
print("=" * 60)
print("Admin Login (OTP):")
print("  POST /api/admin-auth/login/")
print("  POST /api/admin-auth/verify-otp/")
print("\nUser Login (OTP):")
print("  POST /api/auth/login-with-otp/")
print("  POST /api/auth/verify-login-otp/")
print("\nPassword Reset (OTP):")
print("  POST /api/auth/password-reset-otp/request/")
print("  POST /api/auth/password-reset-otp/verify/")
print("\n" + "=" * 60)
