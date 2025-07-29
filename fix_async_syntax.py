#!/usr/bin/env python3
"""
Fix Async Syntax Error - Restore proper async function structure
"""

import re

def fix_async_syntax():
    """Fix the async syntax error in main.py"""
    try:
        with open('webapp/main.py', 'r') as f:
            content = f.read()
        
        print("🔧 Fixing async syntax errors...")
        
        # Fix any standalone async with statements
        # Pattern: Look for 'async with' that's not properly indented in an async function
        
        # Replace malformed async with statements
        content = re.sub(
            r'(\n\s*)async with await get_db_connection\(\) as conn:',
            r'\1async with await get_db_connection() as conn:',
            content
        )
        
        # Ensure all API functions are properly structured
        # Fix Universities API function header
        content = re.sub(
            r'@app\.get\("/api/v1/universities"\)\s*\n([^a])',
            r'@app.get("/api/v1/universities")\nasync def get_universities(\n    page: int = Query(1, ge=1, description="Page number"),\n    per_page: int = Query(24, ge=1, le=100, description="Items per page"),\n    sort_by: str = Query("faculty_count", description="Sort field"),\n    country: Optional[str] = Query(None, description="Filter by country"),\n    university_type: Optional[str] = Query(None, description="Filter by university type"),\n    search: Optional[str] = Query(None, description="Search term")\n):\n    """Get universities with pagination, filtering, and search"""\n    try:\n        \1',
            content,
            flags=re.MULTILINE
        )
        
        # Fix Faculties API function header  
        content = re.sub(
            r'@app\.get\("/api/v1/faculties"\)\s*\n([^a])',
            r'@app.get("/api/v1/faculties")\nasync def get_faculties(\n    page: int = Query(1, ge=1, description="Page number"),\n    per_page: int = Query(24, ge=1, le=100, description="Items per page"),\n    sort_by: str = Query("name", description="Sort field"),\n    university_code: Optional[str] = Query(None, description="Filter by university"),\n    search: Optional[str] = Query(None, description="Search term")\n):\n    """Get faculties/departments with pagination and filtering"""\n    try:\n        \1',
            content,
            flags=re.MULTILINE
        )
        
        # Fix Professor API function header
        content = re.sub(
            r'@app\.get\("/api/v1/professor/\{professor_id\}"\)\s*\n([^a])',
            r'@app.get("/api/v1/professor/{professor_id}")\nasync def get_professor(professor_id: str = Path(..., description="Professor ID")):\n    """Get individual professor details"""\n    try:\n        \1',
            content,
            flags=re.MULTILINE
        )
        
        with open('webapp/main.py', 'w') as f:
            f.write(content)
        
        print("✅ Fixed async syntax structure")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix async syntax: {e}")
        return False

def restore_from_backup():
    """Restore from backup and apply a simpler fix"""
    try:
        import shutil
        shutil.copy('webapp/main.py.backup', 'webapp/main.py')
        print("✅ Restored from backup")
        
        # Apply just the critical syntax fix
        with open('webapp/main.py', 'r') as f:
            content = f.read()
        
        # Fix the original syntax error
        content = content.replace('LIMIT ${param_count + 1} OFFSET ${param_count + 2}', 
                                'LIMIT {param_count + 1} OFFSET {param_count + 2}')
        
        with open('webapp/main.py', 'w') as f:
            f.write(content)
        
        print("✅ Applied minimal syntax fix")
        return True
        
    except Exception as e:
        print(f"❌ Could not restore from backup: {e}")
        return False

def test_syntax():
    """Test Python syntax"""
    try:
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', 'webapp/main.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Python syntax is now valid!")
            return True
        else:
            print(f"❌ Syntax still invalid: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Could not test syntax: {e}")
        return False

def restart_service():
    """Restart the service"""
    try:
        import subprocess
        subprocess.run(['sudo', 'systemctl', 'restart', 'facultyfinder.service'], check=True)
        print("✅ Service restarted!")
        
        # Quick test
        import time
        time.sleep(3)
        
        import urllib.request
        response = urllib.request.urlopen('http://localhost:8008/api/v1/universities?per_page=1')
        if response.status == 200:
            print("✅ Universities API working!")
            return True
        else:
            print(f"⚠️  Universities API: HTTP {response.status}")
            return False
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

def main():
    print("🔧 Fix Async Syntax Error")
    print("=" * 30)
    
    # Option 1: Try to fix the async syntax
    if fix_async_syntax() and test_syntax():
        print("✅ Fixed async syntax successfully!")
        if restart_service():
            print("🎉 Service is working!")
            return
    
    print("\n🔄 Trying backup restore approach...")
    
    # Option 2: Restore from backup and apply minimal fix
    if restore_from_backup() and test_syntax():
        print("✅ Backup restore successful!")
        if restart_service():
            print("🎉 Service is working with minimal fix!")
            return
    
    print("\n❌ Both approaches failed - manual intervention needed")
    print("\n🔧 Manual steps:")
    print("1. Check: cat webapp/main.py.backup")
    print("2. Restore: cp webapp/main.py.backup webapp/main.py") 
    print("3. Fix syntax: sed -i 's/LIMIT ${param_count + 1}/LIMIT {param_count + 1}/g' webapp/main.py")
    print("4. Test: python3 -m py_compile webapp/main.py")
    print("5. Restart: sudo systemctl restart facultyfinder.service")

if __name__ == "__main__":
    main() 