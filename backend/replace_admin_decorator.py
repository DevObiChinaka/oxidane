"""Script to replace all @admin_required decorators with standard DRF permissions"""
import re
from pathlib import Path

# Files to update
files_to_update = [
    'courses/admin_views.py',
    'subscriptions/admin_views.py',
    'users/admin_views.py',
]

for file_path in files_to_update:
    full_path = Path(file_path)
    
    if not full_path.exists():
        print(f"⚠️  Skipping {file_path} - file not found")
        continue
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace @admin_required with standard permission classes
        updated_content = content.replace(
            '@admin_required',
            '@permission_classes([IsAuthenticated, IsAdmin])'
        )
        
        # Count replacements
        count = content.count('@admin_required')
        
        if count > 0:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ {file_path}: Replaced {count} instances")
        else:
            print(f"ℹ️  {file_path}: No @admin_required found")
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

print("\n✨ Migration complete!")
