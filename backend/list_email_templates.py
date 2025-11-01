#!/usr/bin/env python
"""Check email templates in database"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

print('\n📧 All Email Templates in Database:')
print('='*70)

templates = EmailTemplate.objects.all().order_by('template_type', '-created_at')

for i, t in enumerate(templates, 1):
    print(f'\n{i}. {t.name}')
    print(f'   Type: {t.template_type}')
    print(f'   Status: {t.status}')
    print(f'   Default: {"✓" if t.is_default else "✗"}')
    print(f'   Created: {t.created_at.strftime("%Y-%m-%d %H:%M")}')

print('='*70)
print(f'\nTotal: {templates.count()} templates')
print('\n✅ All templates are accessible in Django Admin at:')
print('   http://localhost:8000/admin/users/emailtemplate/')
