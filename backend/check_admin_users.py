"""
Check and fix admin user permissions
Run this to ensure your admin account has proper staff/superuser permissions
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("🔍 ADMIN USER PERMISSIONS CHECK")
print("=" * 60)

# Get all staff/superuser accounts
staff_users = User.objects.filter(is_staff=True)
superusers = User.objects.filter(is_superuser=True)

print(f"\n📊 Staff Users: {staff_users.count()}")
for user in staff_users:
    print(f"   ✅ {user.email} (Staff: {user.is_staff}, Superuser: {user.is_superuser})")

print(f"\n📊 Superusers: {superusers.count()}")
for user in superusers:
    print(f"   ✅ {user.email}")

# Check if there are any admin users
if not staff_users.exists():
    print("\n⚠️  WARNING: No staff users found!")
    print("   Creating admin user for testing...")
    
    # Try to find a user to promote
    regular_users = User.objects.all()[:5]
    if regular_users.exists():
        print("\n📋 Available users:")
        for i, user in enumerate(regular_users, 1):
            print(f"   {i}. {user.email}")
        
        choice = input("\nEnter number of user to make admin (or press Enter to skip): ").strip()
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(regular_users):
                user = regular_users[idx]
                user.is_staff = True
                user.is_superuser = True
                user.save()
                print(f"\n✅ {user.email} is now an admin!")
    else:
        print("\n⚠️  No users found in database!")
        print("   Please create a user first, then run this script again.")
else:
    print("\n✅ Admin users configured correctly!")
    print("\nTo log in to admin panel:")
    print("   1. Go to http://localhost:3000/admin/login")
    print("   2. Use one of the email addresses listed above")
    print("   3. Enter your password")
    print("   4. JWT token will be generated automatically")

print("\n" + "=" * 60)
print("🔐 AUTHENTICATION FLOW:")
print("=" * 60)
print("""
1. Admin Login Page:
   - Uses regular JWT authentication
   - Checks is_staff=True permission
   
2. Backend Email Templates:
   - Now uses @permission_classes([IsAuthenticated, IsAdmin])
   - Validates JWT token
   - Checks if user.is_staff=True
   
3. Token Storage:
   - Frontend stores token in localStorage as 'admin_token'
   - API sends it as Authorization: Bearer <token>
   
4. No Redis Required:
   - Regular JWT auth doesn't need Redis
   - Works with Django's built-in auth
""")

print("\n" + "=" * 60)
