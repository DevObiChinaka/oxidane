"""Replace IsAdminUser with IsAdmin in all files"""
from pathlib import Path

files = [
    'subscriptions/admin_views.py',
    'courses/admin_views.py',
    'users/admin_views.py',
]

for filepath in files:
    path = Path(filepath)
    if not path.exists():
        continue
    
    content = path.read_text(encoding='utf-8')
    updated = content.replace('IsAdminUser', 'IsAdmin')
    
    if updated != content:
        path.write_text(updated, encoding='utf-8')
        print(f"✅ Updated {filepath}")
    else:
        print(f"ℹ️  No changes needed in {filepath}")

print("✨ Complete!")
