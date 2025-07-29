#!/usr/bin/env python3
"""
Quick fix for Flask @app.before_first_request compatibility issue
"""

import re
import sys

def fix_flask_app():
    """Fix the Flask app.py file"""
    
    try:
        # Read the app.py file
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Create backup
        with open('app.py.backup', 'w') as f:
            f.write(content)
        print("✅ Created backup: app.py.backup")
        
        # Remove @app.before_first_request decorator
        original_content = content
        content = re.sub(r'@app\.before_first_request\s*\n', '', content)
        
        if content != original_content:
            print("✅ Removed @app.before_first_request decorator")
        
        # Add initialization call if missing
        if 'initialize_performance_optimizations()' not in content:
            # Find the if __name__ == '__main__': section
            pattern = r"(if __name__ == '__main__':\s*\n)(.*?)(app\.run\([^)]*\))"
            
            def add_init(match):
                start = match.group(1)
                middle = match.group(2)
                app_run = match.group(3)
                return f"{start}{middle}    # Initialize performance optimizations\n    initialize_performance_optimizations()\n    \n    # Run the application\n    {app_run}"
            
            content = re.sub(pattern, add_init, content, flags=re.DOTALL)
            print("✅ Added performance initialization")
        
        # Write the fixed content
        with open('app.py', 'w') as f:
            f.write(content)
        
        print("🎉 Flask compatibility fix applied!")
        print("\nNow try running: python3 app.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing Flask compatibility issue...")
    
    if fix_flask_app():
        print("✅ Fix completed successfully!")
    else:
        print("❌ Fix failed. Check the error messages above.")
        sys.exit(1) 