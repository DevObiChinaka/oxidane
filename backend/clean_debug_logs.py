"""
Clean up excessive debug logging from backend
Keep only essential error logging
"""
import re
from pathlib import Path

def clean_debug_logging(filepath: Path):
    """Remove excessive debug logging"""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Remove debug logging patterns
        patterns = [
            r"^\s*print\(.*?\)\s*$",  # print statements
            r"^\s*logger\.debug\(.*?\)\s*$",  # debug logs
            r"^\s*logger\.info\('🔐.*?\)\s*$",  # emoji debug logs
            r"^\s*logger\.info\('🔍.*?\)\s*$",
            r"^\s*logger\.info\('✅.*?\)\s*$",
            r"^\s*logger\.info\('❌.*?\)\s*$",
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # Remove empty lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    backend_dir = Path('.')
    
    # Find all Python files in key directories
    files = []
    for pattern in ['users/*.py', 'courses/*.py', 'subscriptions/*.py']:
        files.extend(backend_dir.glob(pattern))
    
    cleaned_count = 0
    for file in files:
        if clean_debug_logging(file):
            print(f"✅ Cleaned {file}")
            cleaned_count += 1
    
    print(f"\n✨ Cleaned {cleaned_count} files")

if __name__ == '__main__':
    main()
