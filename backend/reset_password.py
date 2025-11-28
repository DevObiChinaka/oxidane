from users.models import User
u = User.objects.get(email='oxiworldforexacademy@gmail.com')
u.set_password('OxiWorld25')
u.save()
print('Password updated successfully')
print(f'Email: {u.email}')
print(f'is_staff: {u.is_staff}')
print(f'is_superuser: {u.is_superuser}')
