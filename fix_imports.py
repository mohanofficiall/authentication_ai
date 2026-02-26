"""
Script to fix all 'from backend.' imports to relative imports
"""
import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 'from backend.' with 'from '
        original_content = content
        content = re.sub(r'from backend\.', 'from ', content)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Error fixing {filepath}: {e}")
        return False

def main():
    """Main function to fix all Python files in backend directory"""
    backend_dir = r'c:\Users\Suneel Reddy\Downloads\authentication\backend'
    fixed_count = 0
    
    for root, dirs, files in os.walk(backend_dir):
        # Skip venv directory
        if 'venv' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\n[OK] Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
