from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(is_staff=True).first()
if admin:
    print(f'Email: {admin.email}')
    print(f'Username: {admin.username}')
