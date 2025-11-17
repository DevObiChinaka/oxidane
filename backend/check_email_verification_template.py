import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

template = EmailTemplate.objects.filter(name='Email Verification').first()

if template:
    print(f"✅ Template found: {template.name}")
    print(f"Subject: {template.subject_template}")
    print(f"Type: {template.template_type}")
    print(f"Available Variables: {template.available_variables}")
    print(f"\nHTML Content (first 800 chars):")
    print(template.html_content[:800] if template.html_content else "No HTML content")
    print("\n" + "="*50)
    print("\nSearching for {{otp_code}} in HTML:")
    if template.html_content and '{{otp_code}}' in template.html_content:
        print("✅ Found {{otp_code}} in HTML content")
    else:
        print("❌ {{otp_code}} NOT FOUND in HTML content")
else:
    print("❌ Template not found")
