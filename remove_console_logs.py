import re
import os
from pathlib import Path

# Pattern to match console.log/error/warn/info/debug statements
console_pattern = re.compile(r'^\s*console\.(log|error|warn|info|debug)\([^;]*\);?\s*$', re.MULTILINE)

def remove_console_logs(file_path):
    """Remove all console.* statements from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count console logs before removal
        matches = console_pattern.findall(content)
        if not matches:
            return 0
        
        # Remove console logs
        new_content = console_pattern.sub('', content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return len(matches)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def main():
    frontend_src = Path(r'C:\Users\user\OneDrive\Desktop\Oxidane\frontend\src')
    
    # Find all TypeScript/JavaScript files
    extensions = ['*.ts', '*.tsx', '*.js', '*.jsx']
    files = []
    for ext in extensions:
        files.extend(frontend_src.rglob(ext))
    
    # Exclude node_modules and test setup files
    files = [f for f in files if 'node_modules' not in str(f) and 'setup.js' not in f.name]
    
    print(f"Found {len(files)} files to process")
    
    total_removed = 0
    files_modified = 0
    
    for file_path in files:
        removed = remove_console_logs(file_path)
        if removed > 0:
            files_modified += 1
            total_removed += removed
            print(f"✓ {file_path.relative_to(frontend_src)}: removed {removed} console statements")
    
    print(f"\n✅ Complete! Modified {files_modified} files, removed {total_removed} console statements")

if __name__ == "__main__":
    main()
