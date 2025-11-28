#!/usr/bin/env python
"""Check admin user status in database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import User

try:
    user = User.objects.filter(email='oxiworldforexacademy@gmail.com').first()
    if user:
        print(f"✓ User found: {user.email}")
        print(f"  - Username: {user.username}")
        print(f"  - is_staff: {user.is_staff}")
        print(f"  - is_superuser: {user.is_superuser}")
        print(f"  - is_active: {user.is_active}")
        print(f"  - User ID: {user.id}")
        
        # Check all fields
        print("\n=== All User Fields ===")
        for field in user._meta.fields:
            value = getattr(user, field.name)
            print(f"  {field.name}: {value}")
    else:
        print("✗ User not found!")
        print("\nAll users in database:")
        for u in User.objects.all():
            print(f"  - {u.email} (staff={u.is_staff}, superuser={u.is_superuser})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
