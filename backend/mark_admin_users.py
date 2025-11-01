"""
Migration script to mark existing admin users with is_staff=True
Run this once to migrate from cache-based admin system to Django's is_staff
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Define admin user emails or usernames
# IMPORTANT: Update this list with your actual admin users
ADMIN_EMAILS = [
    # Add your admin emails here
    # Example: 'admin@oxiworld.com',
]

ADMIN_USERNAMES = [
    # Add your admin usernames here
    # Example: 'adminuser',
]

def mark_admins():
    """Mark specified users as admin (is_staff=True)"""
    print("🔧 Starting admin user migration...\n")
    
    updated_count = 0
    
    # Mark users by email
    for email in ADMIN_EMAILS:
        try:
            user = User.objects.get(email=email)
            if not user.is_staff:
                user.is_staff = True
                user.save()
                print(f"✅ Marked {user.email} ({user.username}) as admin")
                updated_count += 1
            else:
                print(f"ℹ️  {user.email} is already an admin")
        except User.DoesNotExist:
            print(f"❌ User with email {email} not found")
    
    # Mark users by username
    for username in ADMIN_USERNAMES:
        try:
            user = User.objects.get(username=username)
            if not user.is_staff:
                user.is_staff = True
                user.save()
                print(f"✅ Marked {user.username} ({user.email}) as admin")
                updated_count += 1
            else:
                print(f"ℹ️  {user.username} is already an admin")
        except User.DoesNotExist:
            print(f"❌ User with username {username} not found")
    
    print(f"\n✨ Migration complete! Updated {updated_count} user(s)")
    print("\n📋 Current admin users:")
    admin_users = User.objects.filter(is_staff=True)
    for user in admin_users:
        print(f"  - {user.email} ({user.username})")

if __name__ == '__main__':
    # Ask for confirmation
    print("⚠️  This script will mark users as admin (is_staff=True)")
    print("⚠️  Make sure to update ADMIN_EMAILS and ADMIN_USERNAMES in the script first!\n")
    
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        mark_admins()
    else:
        print("❌ Migration cancelled")
