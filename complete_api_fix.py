#!/usr/bin/env python3
"""
Complete API Fix - Replace broken APIs with working versions
This fixes universities, faculties, and professor APIs comprehensively
"""

import os
import re

def backup_main_py():
    """Create a backup of main.py before making changes"""
    try:
        import shutil
        shutil.copy('webapp/main.py', 'webapp/main.py.backup')
        print("✅ Created backup: webapp/main.py.backup")
        return True
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
        return False

def create_working_universities_api():
    """Create a completely working universities API"""
    return '''@app.get("/api/v1/universities")
async def get_universities(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(24, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("faculty_count", description="Sort field"),
    country: Optional[str] = Query(None, description="Filter by country"),
    university_type: Optional[str] = Query(None, description="Filter by university type"),
    search: Optional[str] = Query(None, description="Search term")
):
    """Get universities with pagination, filtering, and search"""
    try:
        async with await get_db_connection() as conn:
            # Build WHERE conditions
            where_conditions = ["u.name IS NOT NULL"]
            params = []
            param_count = 0

            if country:
                param_count += 1
                where_conditions.append(f"u.country = ${param_count}")
                params.append(country)

            if university_type:
                param_count += 1
                where_conditions.append(f"u.university_type = ${param_count}")
                params.append(university_type)

            if search:
                param_count += 1
                where_conditions.append(f"(u.name ILIKE ${param_count} OR u.city ILIKE ${param_count})")
                params.extend([f"%{search}%", f"%{search}%"])
                param_count += 1

            # Sort options
            sort_options = {
                "faculty_count": "faculty_count DESC",
                "name": "u.name ASC", 
                "location": "u.country ASC, u.city ASC",
                "established": "u.year_established DESC NULLS LAST"
            }
            order_clause = sort_options.get(sort_by, "faculty_count DESC")

            # Calculate offset
            offset = (page - 1) * per_page

            # Main query
            query = f"""
                SELECT u.id, u.name, u.country, u.city, u.university_code,
                       COALESCE(u.province_state, '') as province_state,
                       COALESCE(u.address, '') as address,
                       COALESCE(u.website, '') as website,
                       COALESCE(u.university_type, '') as type,
                       COALESCE(u.languages, '') as language,
                       COALESCE(u.year_established, 0) as established,
                       COUNT(p.id) as faculty_count,
                       COUNT(DISTINCT COALESCE(p.department, 'Unknown')) as department_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, 
                         u.province_state, u.address, u.website, u.university_type, 
                         u.languages, u.year_established
                ORDER BY {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([per_page, offset])
            rows = await conn.fetch(query, *params)

            # Get total count
            count_query = f"""
                SELECT COUNT(DISTINCT u.id)
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
            """
            total = await conn.fetchval(count_query, *params[:-2])

            # Convert to list of dicts
            universities = [dict(row) for row in rows]

            return {
                "universities": universities,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }

    except Exception as e:
        logger.error(f"Error in get_universities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve universities")'''

def create_working_faculties_api():
    """Create a completely working faculties API"""
    return '''@app.get("/api/v1/faculties")
async def get_faculties(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(24, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field"),
    university_code: Optional[str] = Query(None, description="Filter by university"),
    search: Optional[str] = Query(None, description="Search term")
):
    """Get faculties/departments with pagination and filtering"""
    try:
        async with await get_db_connection() as conn:
            # Build WHERE conditions
            where_conditions = ["p.department IS NOT NULL", "p.department != ''"]
            params = []
            param_count = 0

            if university_code:
                param_count += 1
                where_conditions.append(f"p.university_code = ${param_count}")
                params.append(university_code)

            if search:
                param_count += 1
                where_conditions.append(f"p.department ILIKE ${param_count}")
                params.append(f"%{search}%")

            # Sort options
            sort_options = {
                "name": "department ASC",
                "faculty_count": "faculty_count DESC",
                "university": "university_name ASC, department ASC"
            }
            order_clause = sort_options.get(sort_by, "department ASC")

            # Calculate offset
            offset = (page - 1) * per_page

            # Main query
            query = f"""
                SELECT p.department as name,
                       p.university_code,
                       COALESCE(u.name, '') as university_name,
                       COUNT(p.id) as faculty_count
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                GROUP BY p.department, p.university_code, u.name
                ORDER BY {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([per_page, offset])
            rows = await conn.fetch(query, *params)

            # Get total count
            count_query = f"""
                SELECT COUNT(DISTINCT p.department)
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
            """
            total = await conn.fetchval(count_query, *params[:-2])

            # Convert to list of dicts
            faculties = [dict(row) for row in rows]

            return {
                "faculties": faculties,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }

    except Exception as e:
        logger.error(f"Error in get_faculties: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve faculties")'''

def create_working_professor_api():
    """Create a completely working professor API"""
    return '''@app.get("/api/v1/professor/{professor_id}")
async def get_professor(professor_id: str = Path(..., description="Professor ID")):
    """Get individual professor details"""
    try:
        async with await get_db_connection() as conn:
            # Try different ID formats
            professor_data = None
            
            # Try new string ID format first
            if not professor_id.isdigit():
                query = """
                    SELECT p.id, p.name, p.professor_code,
                           p.university_code, p.department, p.position, p.email, p.phone,
                           p.office, p.biography, p.research_interests, p.research_areas,
                           p.education, p.experience, p.awards_honors, p.memberships,
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name,
                           COALESCE(u.city, '') as city,
                           COALESCE(u.province_state, '') as province_state,
                           COALESCE(u.country, '') as country,
                           COALESCE(u.address, '') as address,
                           COALESCE(u.website, '') as university_website
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.professor_id_new = $1
                """
                row = await conn.fetchrow(query, professor_id)
                if row:
                    professor_data = dict(row)

            # Try legacy integer ID
            if not professor_data and professor_id.isdigit():
                query = """
                    SELECT p.id, p.name, p.professor_code,
                           p.university_code, p.department, p.position, p.email, p.phone,
                           p.office, p.biography, p.research_interests, p.research_areas,
                           p.education, p.experience, p.awards_honors, p.memberships,
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name,
                           COALESCE(u.city, '') as city,
                           COALESCE(u.province_state, '') as province_state,
                           COALESCE(u.country, '') as country,
                           COALESCE(u.address, '') as address,
                           COALESCE(u.website, '') as university_website
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.id = $1
                """
                row = await conn.fetchrow(query, int(professor_id))
                if row:
                    professor_data = dict(row)

            if not professor_data:
                raise HTTPException(status_code=404, detail="Professor not found")

            return professor_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professor {professor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")'''

def replace_apis_in_main():
    """Replace the broken APIs with working versions"""
    try:
        with open('webapp/main.py', 'r') as f:
            content = f.read()

        print("🔧 Replacing Universities API...")
        # Remove old universities API
        content = re.sub(
            r'@app\.get\("/api/v1/universities"\).*?(?=@app\.get|@app\.post|# |def |class |if __name__)',
            '',
            content,
            flags=re.DOTALL
        )
        
        print("🔧 Replacing Faculties API...")
        # Remove old faculties API
        content = re.sub(
            r'@app\.get\("/api/v1/faculties"\).*?(?=@app\.get|@app\.post|# |def |class |if __name__)',
            '',
            content,
            flags=re.DOTALL
        )
        
        print("🔧 Replacing Professor API...")
        # Remove old professor API
        content = re.sub(
            r'@app\.get\("/api/v1/professor/\{professor_id\}"\).*?(?=@app\.get|@app\.post|# |def |class |if __name__)',
            '',
            content,
            flags=re.DOTALL
        )

        # Find a good place to insert new APIs (before the last route or at the end)
        insertion_point = content.rfind('@app.get')
        if insertion_point == -1:
            insertion_point = content.rfind('# Routes')
            if insertion_point == -1:
                insertion_point = len(content) - 100
        
        # Find the end of the last route
        next_def = content.find('\n\n', insertion_point)
        if next_def == -1:
            next_def = len(content)

        # Insert new APIs
        new_apis = f"""

{create_working_universities_api()}

{create_working_faculties_api()}

{create_working_professor_api()}

"""
        
        content = content[:next_def] + new_apis + content[next_def:]

        # Save the fixed file
        with open('webapp/main.py', 'w') as f:
            f.write(content)

        print("✅ All APIs replaced successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to replace APIs: {e}")
        return False

def test_python_syntax():
    """Test that Python syntax is valid"""
    try:
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', 'webapp/main.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Python syntax is valid!")
            return True
        else:
            print(f"❌ Python syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Could not test syntax: {e}")
        return False

def restart_service():
    """Restart the FastAPI service"""
    try:
        import subprocess
        subprocess.run(['sudo', 'systemctl', 'restart', 'facultyfinder.service'], check=True)
        print("✅ Service restarted!")
        return True
    except Exception as e:
        print(f"❌ Could not restart service: {e}")
        return False

def test_apis():
    """Test that APIs are working"""
    try:
        import urllib.request
        import json
        import time
        
        # Wait for service to start
        time.sleep(3)
        
        # Test universities
        try:
            response = urllib.request.urlopen('http://localhost:8008/api/v1/universities?per_page=3')
            if response.status == 200:
                data = json.loads(response.read())
                print("✅ Universities API: HTTP 200")
                if 'universities' in data and len(data['universities']) > 0:
                    print(f"   Found {len(data['universities'])} universities")
                    print(f"   Sample: {data['universities'][0]['name']}")
                universities_ok = True
            else:
                print(f"❌ Universities API: HTTP {response.status}")
                universities_ok = False
        except Exception as e:
            print(f"❌ Universities API failed: {e}")
            universities_ok = False

        # Test faculties
        try:
            response = urllib.request.urlopen('http://localhost:8008/api/v1/faculties?per_page=3')
            if response.status == 200:
                data = json.loads(response.read())
                print("✅ Faculties API: HTTP 200")
                if 'faculties' in data and len(data['faculties']) > 0:
                    print(f"   Found {len(data['faculties'])} faculties")
                    print(f"   Sample: {data['faculties'][0]['name']}")
                faculties_ok = True
            else:
                print(f"❌ Faculties API: HTTP {response.status}")
                faculties_ok = False
        except Exception as e:
            print(f"❌ Faculties API failed: {e}")
            faculties_ok = False

        # Test professor
        try:
            response = urllib.request.urlopen('http://localhost:8008/api/v1/professor/10')
            if response.status == 200:
                data = json.loads(response.read())
                print("✅ Professor API: HTTP 200")
                if 'name' in data:
                    print(f"   Professor: {data['name']}")
                professor_ok = True
            else:
                print(f"❌ Professor API: HTTP {response.status}")
                professor_ok = False
        except Exception as e:
            print(f"❌ Professor API failed: {e}")
            professor_ok = False

        return universities_ok and faculties_ok and professor_ok

    except Exception as e:
        print(f"❌ API testing failed: {e}")
        return False

def main():
    print("🚀 Complete API Fix")
    print("=" * 50)
    
    # Step 1: Backup
    backup_main_py()
    
    # Step 2: Replace APIs
    if not replace_apis_in_main():
        print("❌ Failed to replace APIs")
        return
    
    # Step 3: Test syntax
    if not test_python_syntax():
        print("❌ Python syntax error - check main.py")
        return
    
    # Step 4: Restart service
    if not restart_service():
        print("❌ Could not restart service")
        return
    
    # Step 5: Test APIs
    if test_apis():
        print("\n🎉 SUCCESS! All APIs are working!")
        print("\n🌐 Your pages should now work:")
        print("   • Universities: https://facultyfinder.io/universities")
        print("   • Faculties: https://facultyfinder.io/faculties")
        print("   • Professor: https://facultyfinder.io/professor/10")
    else:
        print("\n❌ Some APIs still need attention")
        print("\n🔧 Check logs: sudo journalctl -u facultyfinder.service -f")

if __name__ == "__main__":
    main() 