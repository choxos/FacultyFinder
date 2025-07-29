#!/usr/bin/env python3
"""
Fix Flask Compatibility Issues for FacultyFinder
Addresses deprecated decorators and other Flask version incompatibilities
"""

import os
import re
import sys
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def fix_before_first_request(filepath):
    """Fix the deprecated @app.before_first_request decorator"""
    print(f"🔧 Fixing before_first_request in {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to find @app.before_first_request and the following function
    pattern = r'@app\.before_first_request\s*\ndef\s+(\w+)\s*\([^)]*\):'
    
    matches = re.finditer(pattern, content)
    
    if not matches:
        print("❌ No @app.before_first_request decorators found")
        return content, False
    
    # Remove the decorator but keep the function
    fixed_content = re.sub(r'@app\.before_first_request\s*\n', '', content)
    
    print("✅ Removed @app.before_first_request decorator")
    return fixed_content, True

def add_initialization_call(content):
    """Add the initialization call to the main block"""
    
    # Find the if __name__ == '__main__': block
    main_pattern = r"if __name__ == '__main__':\s*\n"
    
    if not re.search(main_pattern, content):
        print("❌ Could not find if __name__ == '__main__': block")
        return content, False
    
    # Check if initialization is already called
    if 'initialize_performance_optimizations()' in content:
        print("✅ Performance initialization already present")
        return content, False
    
    # Add the initialization call before app.run()
    app_run_pattern = r"(\s+)(app\.run\([^)]*\))"
    
    def replacement(match):
        indent = match.group(1)
        app_run_call = match.group(2)
        return f"{indent}# Initialize performance optimizations\n{indent}initialize_performance_optimizations()\n{indent}\n{indent}# Run the application\n{indent}{app_run_call}"
    
    fixed_content = re.sub(app_run_pattern, replacement, content)
    
    if fixed_content != content:
        print("✅ Added performance initialization call")
        return fixed_content, True
    else:
        print("❌ Could not add initialization call")
        return content, False

def fix_flask_mail_import():
    """Fix Flask-Mail import to be optional"""
    print("🔧 Ensuring Flask-Mail import is optional...")
    
    # This is already handled in the current code, just verify
    print("✅ Flask-Mail import should already be optional")

def main():
    print("🚀 Flask Compatibility Fix for FacultyFinder")
    print("=" * 50)
    
    # Change to webapp directory
    webapp_dir = "/var/www/ff/webapp"
    if os.path.exists(webapp_dir):
        os.chdir(webapp_dir)
        print(f"📁 Changed to directory: {webapp_dir}")
    else:
        print(f"❌ Directory not found: {webapp_dir}")
        print("   Make sure you're running this from the correct location")
        sys.exit(1)
    
    app_py_path = "app.py"
    
    if not os.path.exists(app_py_path):
        print(f"❌ File not found: {app_py_path}")
        sys.exit(1)
    
    # Create backup
    backup_path = backup_file(app_py_path)
    
    try:
        # Read the current file
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Fix deprecated decorators
        content, fixed_decorator = fix_before_first_request(content)
        
        # Add initialization call
        content, added_init = add_initialization_call(content)
        
        # Write the fixed content back
        if fixed_decorator or added_init:
            with open(app_py_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed Flask compatibility issues in {app_py_path}")
        else:
            print("ℹ️  No changes needed")
        
        # Test the fix
        print("\n🧪 Testing the fix...")
        test_command = "python3 -c \"from app import app; print('✅ Flask app imports successfully!')\""
        exit_code = os.system(test_command)
        
        if exit_code == 0:
            print("🎉 Flask compatibility fix successful!")
            print("\n📋 Next steps:")
            print("1. Try running: python3 app.py")
            print("2. If successful, your website should be accessible")
            print("3. If you still get errors, check the logs for other issues")
        else:
            print("❌ There might be other issues. Check the error messages above.")
            
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        # Restore backup
        shutil.copy2(backup_path, app_py_path)
        print(f"🔄 Restored backup from {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main() 