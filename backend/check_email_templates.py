import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

templates = EmailTemplate.objects.all()
print(f'Total templates: {templates.count()}')
print(f'Active templates: {templates.filter(status="active").count()}')
print(f'System templates: {templates.filter(is_system_email=True).count()}')
print(f'Draft templates: {templates.filter(status="draft").count()}')
print(f'Inactive templates: {templates.filter(status="inactive").count()}')

print('\nTemplate Details:')
for t in templates:
    print(f'  {t.name}')
    print(f'    Type: {t.template_type}')
    print(f'    Status: {t.status}')
    print(f'    System: {t.is_system_email}')
    print(f'    Default: {t.is_default}')
    print()
