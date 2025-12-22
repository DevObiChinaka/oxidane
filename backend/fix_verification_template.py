#!/usr/bin/env python
"""
Fix email verification template type
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

print("Fixing email verification template type...")

# Find the template
template = EmailTemplate.objects.filter(name__icontains="verification").first()

if template:
    print(f"Found: {template.name}")
    print(f"Current type: {template.template_type}")
    
    # Update to correct type
    template.template_type = 'email_verification'
    template.save()
    
    print(f"Updated to: {template.template_type}")
    print("✅ Fixed!")
else:
    print("❌ Template not found")
