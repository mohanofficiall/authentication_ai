"""
Script to fix SQLAlchemy relationship strings
"""
import os
import re

def fix_relationships_in_file(filepath):
    """Fix relationship strings in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 'backend.models.user.User' with just 'User'
        # Replace 'backend.models.attendance.Attendance' with just 'Attendance'
        # Replace 'backend.models.attendance.AttendanceSession' with just 'AttendanceSession'
        original_content = content
        content = re.sub(r"'backend\.models\.user\.User'", "'User'", content)
        content = re.sub(r"'backend\.models\.attendance\.Attendance'", "'Attendance'", content)
        content = re.sub(r"'backend\.models\.attendance\.AttendanceSession'", "'AttendanceSession'", content)
        
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
    """Main function to fix all Python model files"""
    models_dir = r'c:\Users\Suneel Reddy\Downloads\authentication\backend\models'
    fixed_count = 0
    
    for file in os.listdir(models_dir):
        if file.endswith('.py'):
            filepath = os.path.join(models_dir, file)
            if fix_relationships_in_file(filepath):
                fixed_count += 1
    
    print(f"\n[OK] Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
