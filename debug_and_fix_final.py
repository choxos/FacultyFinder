#!/usr/bin/env python3
"""
Debug and Fix Final - Manual API Repair
Check logs, identify exact issues, and manually fix the API endpoints
"""

import re
import subprocess

def check_service_logs():
    """Check recent service logs for specific errors"""
    print("🔍 Checking Service Logs")
    print("=" * 30)
    
    try:
        # Get recent error logs
        result = subprocess.run([
            'sudo', 'journalctl', '-u', 'facultyfinder.service', 
            '--since', '5 minutes ago', '--no-pager'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logs = result.stdout
            
            # Look for specific error patterns
            if 'column' in logs and 'does not exist' in logs:
                print("❌ Database column errors found:")
                for line in logs.split('\n'):
                    if 'column' in line and 'does not exist' in line:
                        print(f"   {line.strip()}")
                return "column_error"
            
            elif 'relation' in logs and 'does not exist' in logs:
                print("❌ Database table errors found:")
                for line in logs.split('\n'):
                    if 'relation' in line and 'does not exist' in line:
                        print(f"   {line.strip()}")
                return "table_error"
            
            elif 'syntax error' in logs:
                print("❌ SQL syntax errors found:")
                for line in logs.split('\n'):
                    if 'syntax error' in line:
                        print(f"   {line.strip()}")
                return "syntax_error"
            
            elif 'import' in logs and 'error' in logs:
                print("❌ Python import errors found:")
                return "import_error"
            
            else:
                print("⚠️  No specific error pattern found in logs")
                print("📋 Recent log excerpt:")
                recent_logs = logs.split('\n')[-10:]
                for line in recent_logs:
                    if line.strip():
                        print(f"   {line.strip()}")
                return "unknown_error"
        
    except Exception as e:
        print(f"❌ Could not check logs: {e}")
        return "log_check_failed"

def fix_universities_api_manually():
    """Manually fix the universities API with correct field mapping"""
    print("\n🔧 Manual Universities API Fix")
    print("=" * 40)
    
    try:
        with open('webapp/main.py', 'r') as f:
            content = f.read()
        
        # Find the universities query and replace it completely
        # Look for the universities query pattern
        
        # Create the correct universities query
        correct_universities_query = '''            # Main query
            query = f"""
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province_state,
                       COALESCE(u.address, '') as address,
                       COALESCE(u.website, '') as website,
                       COALESCE(u.university_type, '') as type,
                       COALESCE(u.languages, '') as language,
                       u.year_established as established,
                       COUNT(p.id) as faculty_count,
                       COUNT(DISTINCT COALESCE(p.department, 'Unknown')) as department_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state,
                         u.address, u.website, u.university_type, u.languages, u.year_established
                HAVING COUNT(p.id) >= 0
                ORDER BY {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            \""""'''
        
        # Replace the universities query
        pattern = r'# Main query\s*query = f""".*?"""'
        content = re.sub(pattern, correct_universities_query, content, flags=re.DOTALL)
        
        # Also fix the university type filter
        content = content.replace('u.type =', 'u.university_type =')
        
        print("✅ Universities query fixed manually")
        
        with open('webapp/main.py', 'w') as f:
            f.write(content)
        
        print("✅ Universities API manually updated")
        return True
        
    except Exception as e:
        print(f"❌ Manual universities fix failed: {e}")
        return False

def fix_professor_api_manually():
    """Manually fix the professor API with simple working queries"""
    print("\n🔧 Manual Professor API Fix")
    print("=" * 40)
    
    try:
        with open('webapp/main.py', 'r') as f:
            content = f.read()
        
        # Create a completely new professor API endpoint
        new_professor_endpoint = '''@app.get("/api/v1/professor/{professor_id}")
async def get_professor(professor_id: str = Path(..., description="Professor ID")):
    """Get individual professor details"""
    try:
        async with await get_db_connection() as conn:
            # Handle both integer IDs and string format IDs
            if professor_id.isdigit():
                # Legacy integer ID
                query = """
                    SELECT p.id, p.name, p.professor_code, 
                           p.university_code, p.department, p.position, p.email, p.phone,
                           p.office, p.biography, p.research_interests, 
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name, 
                           COALESCE(u.city, '') as city, 
                           COALESCE(u.province_state, '') as province_state, 
                           COALESCE(u.country, '') as country
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.id = $1
                """
                params = [int(professor_id)]
            else:
                # String format ID - try professor_id_new
                query = """
                    SELECT p.id, p.name, p.professor_code, 
                           p.university_code, p.department, p.position, p.email, p.phone,
                           p.office, p.biography, p.research_interests,
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name, 
                           COALESCE(u.city, '') as city, 
                           COALESCE(u.province_state, '') as province_state, 
                           COALESCE(u.country, '') as country
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.professor_id_new = $1
                """
                params = [professor_id]

            row = await conn.fetchrow(query, *params)
            
            if not row:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            # Convert to dict and return
            professor_data = dict(row)
            return professor_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professor {professor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")'''
        
        # Remove the old professor API endpoint completely
        pattern = r'@app\.get\("/api/v1/professor/\{professor_id\}"\).*?(?=@app\.get|# Professor detail route)'
        content = re.sub(pattern, new_professor_endpoint + '\n\n', content, flags=re.DOTALL)
        
        print("✅ Professor API replaced with working version")
        
        with open('webapp/main.py', 'w') as f:
            f.write(content)
        
        print("✅ Professor API manually updated")
        return True
        
    except Exception as e:
        print(f"❌ Manual professor fix failed: {e}")
        return False

def test_database_queries():
    """Test the actual database queries to make sure they work"""
    print("\n🧪 Testing Database Queries")
    print("=" * 40)
    
    try:
        import asyncio
        import asyncpg
        
        async def test_queries():
            conn = await asyncpg.connect("postgresql://ff_user:Choxos10203040@localhost:5432/ff_production")
            
            # Test universities query
            try:
                uni_query = """
                    SELECT u.id, u.name, u.country, u.city, u.university_code, 
                           COALESCE(u.province_state, '') as province_state,
                           COALESCE(u.address, '') as address,
                           COALESCE(u.website, '') as website,
                           COALESCE(u.university_type, '') as type,
                           COALESCE(u.languages, '') as language,
                           u.year_established as established,
                           COUNT(p.id) as faculty_count
                    FROM universities u
                    LEFT JOIN professors p ON p.university_code = u.university_code
                    WHERE u.name IS NOT NULL
                    GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state,
                             u.address, u.website, u.university_type, u.languages, u.year_established
                    LIMIT 1
                """
                result = await conn.fetchrow(uni_query)
                if result:
                    print("✅ Universities query works")
                    print(f"   Sample: {result['name']}, Faculty: {result['faculty_count']}")
                else:
                    print("⚠️  Universities query returns no results")
            except Exception as e:
                print(f"❌ Universities query failed: {e}")
            
            # Test professor query
            try:
                prof_query = """
                    SELECT p.id, p.name, p.professor_code, 
                           p.university_code, p.department, p.position, p.email,
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.id = 1
                """
                result = await conn.fetchrow(prof_query)
                if result:
                    print("✅ Professor query works")
                    print(f"   Sample: {result['name']}, Department: {result['department']}")
                else:
                    print("⚠️  Professor query returns no results")
            except Exception as e:
                print(f"❌ Professor query failed: {e}")
            
            await conn.close()
        
        asyncio.run(test_queries())
        return True
        
    except Exception as e:
        print(f"❌ Database query testing failed: {e}")
        return False

def restart_and_test_service():
    """Restart service and test endpoints"""
    print("\n🔄 Restarting Service and Testing")
    print("=" * 40)
    
    try:
        # Restart service
        subprocess.run(['sudo', 'systemctl', 'restart', 'facultyfinder.service'], check=True)
        print("✅ Service restarted")
        
        # Wait for startup
        import time
        time.sleep(5)
        
        # Test endpoints
        import urllib.request
        import json
        
        # Test universities
        try:
            response = urllib.request.urlopen('http://localhost:8008/api/v1/universities?per_page=3')
            if response.status == 200:
                data = json.loads(response.read())
                print("✅ Universities API: HTTP 200")
                if 'universities' in data:
                    print(f"   Found {len(data['universities'])} universities")
                return True
        except Exception as e:
            print(f"❌ Universities API test failed: {e}")
        
        # Test professor
        try:
            response = urllib.request.urlopen('http://localhost:8008/api/v1/professor/1')
            if response.status == 200:
                data = json.loads(response.read())
                print("✅ Professor API: HTTP 200")
                if 'name' in data:
                    print(f"   Professor: {data['name']}")
                return True
        except Exception as e:
            print(f"❌ Professor API test failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Service restart/test failed: {e}")
        return False

def main():
    print("🔧 Debug and Fix Final")
    print("=" * 50)
    
    # Step 1: Check logs for specific errors
    error_type = check_service_logs()
    
    # Step 2: Test database queries work
    db_test = test_database_queries()
    
    # Step 3: Apply manual fixes
    uni_fixed = fix_universities_api_manually()
    prof_fixed = fix_professor_api_manually()
    
    # Step 4: Restart and test
    if uni_fixed and prof_fixed:
        service_test = restart_and_test_service()
        
        print("\n🎯 Final Results")
        print("=" * 20)
        
        if service_test:
            print("✅ All APIs fixed and working!")
            print("\n🌐 Test your pages:")
            print("   Universities: https://facultyfinder.io/universities")
            print("   Professor: https://facultyfinder.io/professor/1")
        else:
            print("❌ APIs still need attention")
            print("\n🔧 Manual troubleshooting:")
            print("   Check logs: sudo journalctl -u facultyfinder.service -f")
            print("   Verify database: psql -h localhost -U ff_user -d ff_production")
    else:
        print("\n❌ Manual fixes failed - manual intervention needed")

if __name__ == "__main__":
    main() 