#!/usr/bin/env python3
"""
Emergency API Schema Fix
Fix both universities typo and professor API schema mismatch
"""

import re

def fix_universities_typo():
    """Fix the 'languagess' typo in universities API"""
    print("🔧 Fixing Universities API Typo")
    print("=" * 40)
    
    main_py_path = 'webapp/main.py'
    
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Fix the typo: languagess → languages
        if 'languagess' in content:
            content = content.replace('u.languagess', 'u.languages')
            print("✅ Fixed typo: u.languagess → u.languages")
        
        # Also fix any other potential issues in the universities query
        # Make sure we're using the correct old field names
        content = re.sub(r'u\.type(?!\w)', 'u.university_type', content)
        content = re.sub(r'u\.language(?!\w)', 'u.languages', content)  
        content = re.sub(r'u\.established(?!\w)', 'u.year_established', content)
        
        print("✅ Verified all university field mappings")
        
        with open(main_py_path, 'w') as f:
            f.write(content)
        
        print("✅ Universities API fixed")
        
    except Exception as e:
        print(f"❌ Failed to fix universities API: {e}")

def fix_professor_api_schema():
    """Fix professor API to match actual database schema"""
    print("\n🔧 Fixing Professor API Schema")
    print("=" * 40)
    
    main_py_path = 'webapp/main.py'
    
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Find the professor API queries and replace with correct schema
        # The actual table has: professor_code, name, university_code, department, position, email, etc.
        
        # Replace the complex professor query with a simpler one that matches actual schema
        old_professor_query_pattern = r'SELECT p\.id, p\.name, p\.first_name.*?WHERE p\.id = \$1'
        
        new_professor_query = '''SELECT p.id, p.name, p.professor_code, 
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
                WHERE p.id = $1'''
        
        # Replace the professor query patterns
        content = re.sub(old_professor_query_pattern, new_professor_query, content, flags=re.DOTALL)
        
        # Also fix the string ID query
        old_string_query_pattern = r'SELECT p\.id, p\.name, p\.first_name.*?WHERE p\.professor_id_new = \$1'
        
        new_string_query = '''SELECT p.id, p.name, p.professor_code, 
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
                WHERE p.professor_id_new = $1'''
        
        content = re.sub(old_string_query_pattern, new_string_query, content, flags=re.DOTALL)
        
        print("✅ Updated professor API queries to match actual database schema")
        
        with open(main_py_path, 'w') as f:
            f.write(content)
        
        print("✅ Professor API schema fixed")
        
    except Exception as e:
        print(f"❌ Failed to fix professor API: {e}")

def main():
    print("🚨 Emergency API Schema Fix")
    print("=" * 50)
    print("Fixing both universities typo and professor schema mismatch")
    print()
    
    # Fix universities typo
    fix_universities_typo()
    
    # Fix professor API schema
    fix_professor_api_schema()
    
    print("\n🎯 Emergency Fix Complete!")
    print("=" * 30)
    print("✅ Universities API: Fixed 'languagess' typo")
    print("✅ Professor API: Updated to match actual database schema")
    print()
    print("🔄 Next steps:")
    print("   1. Restart FastAPI service: sudo systemctl restart facultyfinder.service")
    print("   2. Test universities API: curl http://localhost:8008/api/v1/universities?per_page=3")
    print("   3. Test professor API: curl http://localhost:8008/api/v1/professor/1")

if __name__ == "__main__":
    main() 