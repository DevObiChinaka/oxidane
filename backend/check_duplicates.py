#!/usr/bin/env python
"""
Check for duplicate templates
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate
from django.db.models import Count

print("\n" + "="*60)
print("🔍 Checking for Duplicate Templates")
print("="*60 + "\n")

# Find duplicates
duplicates = EmailTemplate.objects.values('template_type').annotate(
    count=Count('id')
).filter(count__gt=1, status='active')

if duplicates:
    print("⚠️  Found duplicate active templates:")
    for dup in duplicates:
        print(f"\n  Type: {dup['template_type']}")
        print(f"  Count: {dup['count']}")
        
        # Show which ones
        templates = EmailTemplate.objects.filter(
            template_type=dup['template_type'],
            status='active'
        )
        for t in templates:
            print(f"    - {t.name} (Default: {t.is_default})")
else:
    print("✅ No duplicate templates found!")

print("\n" + "="*60)
print("📊 Summary by Template Type:")
print("="*60 + "\n")

# Group by type
from collections import defaultdict
templates_by_type = defaultdict(list)

for template in EmailTemplate.objects.filter(status='active'):
    templates_by_type[template.template_type].append(template.name)

for t_type, names in sorted(templates_by_type.items()):
    count = len(names)
    icon = "⚠️" if count > 1 else "✅"
    print(f"{icon} {t_type}: {count} template(s)")
    if count > 1:
        for name in names:
            print(f"   - {name}")

print()
