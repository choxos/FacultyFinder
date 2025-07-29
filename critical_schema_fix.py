#!/usr/bin/env python3
"""
Critical Schema Fix
Fix both universities and professors API to match actual database schema
"""

def main():
    print("🚨 Critical Schema Fix")
    print("=" * 50)
    
    main_py = 'webapp/main.py'
    
    try:
        with open(main_py, 'r') as f:
            content = f.read()
        
        # Fix 1: Universities API field mapping and typos
        print("🔧 Fixing Universities API...")
        
        # Fix any languagess typo
        content = content.replace('u.languagess', 'u.languages')
        
        # Ensure we're using the correct old field names for universities
        content = content.replace('COALESCE(u.type,', 'COALESCE(u.university_type,')
        content = content.replace('COALESCE(u.language,', 'COALESCE(u.languages,')
        content = content.replace('u.established', 'u.year_established')
        
        # Fix GROUP BY clause to match
        content = content.replace('u.type, u.language, u.established', 'u.university_type, u.languages, u.year_established')
        
        print("✅ Universities API field mapping fixed")
        
        # Fix 2: Professor Model
        print("🔧 Fixing Professor Model...")
        
        # Replace the Professor class with one that matches actual database schema
        old_professor_model = '''class Professor(BaseModel):
    id: int
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    university_code: Optional[str] = None
    university_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    primary_position: Optional[str] = None
    research_areas: Optional[str] = None
    total_publications: Optional[int] = 0
    publication_count: Optional[int] = 0
    publications_last_5_years: Optional[int] = 0
    citation_count: Optional[int] = 0
    h_index: Optional[int] = 0
    adjunct: Optional[bool] = False
    full_time: Optional[bool] = True'''
        
        new_professor_model = '''class Professor(BaseModel):
    id: int
    name: str
    professor_code: Optional[str] = None
    university_code: Optional[str] = None
    university_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    office: Optional[str] = None
    biography: Optional[str] = None
    research_interests: Optional[str] = None
    research_areas: Optional[dict] = None
    education: Optional[dict] = None
    experience: Optional[dict] = None
    awards_honors: Optional[dict] = None
    memberships: Optional[dict] = None
    professor_id_new: Optional[str] = None
    city: Optional[str] = None
    province_state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    university_website: Optional[str] = None'''
        
        content = content.replace(old_professor_model, new_professor_model)
        print("✅ Professor model updated to match database schema")
        
        # Fix 3: Professor API Queries
        print("🔧 Fixing Professor API Queries...")
        
        # Create the correct professor query based on actual database schema
        correct_query = '''SELECT p.id, p.name, p.professor_code, 
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
                LEFT JOIN universities u ON p.university_code = u.university_code'''
        
        # Replace all the complex professor queries that reference non-existent columns
        # Find and replace the SELECT statements that cause errors
        import re
        
        # Pattern to match the problematic SELECT statements
        pattern = r'SELECT p\.id, p\.name, p\.first_name.*?LEFT JOIN universities u ON p\.university_code = u\.university_code'
        
        # Replace all occurrences
        content = re.sub(pattern, correct_query, content, flags=re.DOTALL)
        
        print("✅ Professor API queries updated to match database schema")
        
        # Write the fixed content back
        with open(main_py, 'w') as f:
            f.write(content)
        
        print("\n🎉 Critical Fix Applied Successfully!")
        print("=" * 40)
        print("✅ Universities API: Fixed field mapping and typos")
        print("✅ Professor Model: Updated to match actual database")
        print("✅ Professor Queries: Fixed to use correct column names")
        print()
        print("🔄 Next Steps:")
        print("   1. Restart service: sudo systemctl restart facultyfinder.service")
        print("   2. Test APIs:")
        print("      curl http://localhost:8008/api/v1/universities?per_page=3")
        print("      curl http://localhost:8008/api/v1/professor/1")
        
    except Exception as e:
        print(f"❌ Critical fix failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 