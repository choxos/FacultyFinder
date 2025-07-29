#!/usr/bin/env python3
"""
Fix Async Context Manager Issue
Remove 'async' from get_db_connection function
"""

def fix_async_context_manager():
    """Fix the async context manager issue"""
    
    with open('webapp/main.py', 'r') as f:
        content = f.read()
    
    print("🔧 Fixing async context manager issue...")
    
    # Fix get_db_connection function - remove async
    content = content.replace(
        'async def get_db_connection():',
        'def get_db_connection():'
    )
    
    with open('webapp/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed async context manager")
    return True

def main():
    """Main function"""
    print("🚀 Fixing Async Context Manager Issue")
    print("====================================")
    
    if fix_async_context_manager():
        print("🎉 Async context manager issue fixed!")
        return True
    else:
        print("❌ Failed to fix async context manager issue")
        return False

if __name__ == "__main__":
    main() 