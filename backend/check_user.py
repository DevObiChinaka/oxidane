from users.models import User

user = User.objects.filter(email='oxiworldforexacademy@gmail.com').first()
if user:
    print(f"User found: {user.email}")
    print(f"Username: {user.username}")
    print(f"is_staff: {user.is_staff}")
    print(f"is_superuser: {user.is_superuser}")
    print(f"is_active: {user.is_active}")
    print(f"User ID: {user.id}")
else:
    print("User not found!")
    print("All users:")
    for u in User.objects.all()[:5]:
        print(f"  {u.email} - staff={u.is_staff}, super={u.is_superuser}")
