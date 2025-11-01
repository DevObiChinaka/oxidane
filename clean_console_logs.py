"""
Clean all console.log statements from frontend for security
Keeps only error handling in production-safe way
"""
import re
from pathlib import Path

def clean_console_logs(filepath: Path):
    """Remove console.log statements from a file"""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Remove console.log, console.warn, console.debug statements
        # But keep console.error for critical errors
        patterns = [
            r'^\s*console\.log\([^)]*\);?\s*$',
            r'^\s*console\.warn\([^)]*\);?\s*$',
            r'^\s*console\.debug\([^)]*\);?\s*$',
            r'^\s*console\.info\([^)]*\);?\s*$',
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # Remove empty lines that were left
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    frontend_dir = Path('frontend/src')
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return
    
    # Find all TypeScript/JavaScript files
    files = list(frontend_dir.rglob('*.tsx')) + list(frontend_dir.rglob('*.ts')) + list(frontend_dir.rglob('*.jsx')) + list(frontend_dir.rglob('*.js'))
    
    cleaned_count = 0
    for file in files:
        if clean_console_logs(file):
            print(f"✅ Cleaned {file.relative_to(frontend_dir)}")
            cleaned_count += 1
    
    print(f"\n✨ Cleaned {cleaned_count} files")

if __name__ == '__main__':
    main()
