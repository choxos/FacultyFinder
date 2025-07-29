#!/usr/bin/env python3
"""
Fix FastAPI Schema Compatibility for PostgreSQL
Updates main.py to work with university_code instead of university_id
"""

import re

def fix_fastapi_queries():
    """Fix all database queries in main.py to use PostgreSQL schema"""
    
    with open('webapp/main.py', 'r') as f:
        content = f.read()
    
    print("🔧 Fixing FastAPI queries for PostgreSQL schema...")
    
    # Fix get_summary_statistics function
    content = re.sub(
        r'prof_count = await conn\.fetchval\("SELECT COUNT\(DISTINCT name\) FROM professors"\)',
        r'prof_count = await conn.fetchval("SELECT COUNT(*) FROM professors")',
        content
    )
    
    content = re.sub(
        r'uni_count = await conn\.fetchval\("SELECT COUNT\(DISTINCT name\) FROM universities"\)',
        r'uni_count = await conn.fetchval("SELECT COUNT(*) FROM universities")',
        content
    )
    
    # Fix get_top_universities function
    old_university_query = r'''query = """
            SELECT u\.id, u\.name, u\.country, u\.city, u\.university_code, COALESCE\(u\.province_state, ''\) as province, u\.year_established,
                   COUNT\(p\.id\) as faculty_count
            FROM universities u
            LEFT JOIN professors p ON u\.id = p\.university_id
            GROUP BY u\.id, u\.name, u\.country, u\.city, u\.university_code, u\.province_state, u\.year_established
            ORDER BY faculty_count DESC
            LIMIT \$1
        """'''
    
    new_university_query = r'''query = """
            SELECT u.id, u.name, u.country, u.city, u.university_code, COALESCE(u.province_state, '') as province, u.year_established,
                   COUNT(p.id) as faculty_count
            FROM universities u
            LEFT JOIN professors p ON u.university_code = p.university_code
            GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state, u.year_established
            ORDER BY faculty_count DESC
            LIMIT $1
        """'''
    
    content = re.sub(old_university_query, new_university_query, content, flags=re.DOTALL)
    
    # Fix universities API query
    universities_query_pattern = r'''# Build final query with joins
            query = f"""
                SELECT u\.id, u\.name, u\.country, u\.city, u\.university_code, 
                       COALESCE\(u\.province_state, ''\) as province, u\.year_established,
                       COALESCE\(u\.website, ''\) as website, COALESCE\(u\.university_type, 'Public'\) as university_type,
                       COUNT\(p\.id\) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON u\.id = p\.university_id
                {where_clause}
                GROUP BY u\.id, u\.name, u\.country, u\.city, u\.university_code, u\.province_state, 
                         u\.year_established, u\.website, u\.university_type
                {order_clause}
                LIMIT \$\{param_count \+ 1\} OFFSET \$\{param_count \+ 2\}
            """'''
    
    new_universities_query = r'''# Build final query with joins
            query = f"""
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province, u.year_established,
                       COALESCE(u.website, '') as website, COALESCE(u.university_type, 'Public') as university_type,
                       COUNT(p.id) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON u.university_code = p.university_code
                {where_clause}
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state, 
                         u.year_established, u.website, u.university_type
                {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """'''
    
    content = re.sub(universities_query_pattern, new_universities_query, content, flags=re.DOTALL)
    
    # Fix faculties/professors API query
    professors_query_pattern = r'''query = f"""
                SELECT p\.id, p\.name, p\.first_name, p\.last_name, p\.position, p\.department,
                       p\.research_areas, u\.name as university_name, u\.city, u\.province_state, u\.country,
                       COALESCE\(p\.uni_email, p\.other_email, ''\) as email,
                       COALESCE\(p\.website, p\.uni_page, ''\) as profile_url,
                       0 as publication_count, 0 as citation_count, 0 as h_index
                FROM professors p
                LEFT JOIN universities u ON p\.university_id = u\.id
                {where_clause}
                {order_clause}
                LIMIT \$\{param_count \+ 1\} OFFSET \$\{param_count \+ 2\}
            """'''
    
    new_professors_query = r'''query = f"""
                SELECT p.id, p.name, p.first_name, p.last_name, p.position, p.department,
                       p.research_areas, u.name as university_name, u.city, u.province_state, u.country,
                       COALESCE(p.uni_email, p.other_email, '') as email,
                       COALESCE(p.website, p.uni_page, '') as profile_url,
                       0 as publication_count, 0 as citation_count, 0 as h_index
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                {where_clause}
                {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """'''
    
    content = re.sub(professors_query_pattern, new_professors_query, content, flags=re.DOTALL)
    
    # Fix professor detail query
    professor_detail_pattern = r'''query = """
                    SELECT p\.id, p\.name, p\.first_name, p\.last_name, p\.middle_names, p\.other_name,
                           p\.degrees, p\.all_degrees_and_inst, p\.all_degrees_only, p\.research_areas,
                           p\.university_code, p\.faculty, p\.department, p\.other_departments,
                           p\.primary_affiliation, p\.memberships, p\.canada_research_chair, p\.director,
                           COALESCE\(p\.position, ''\) as position, 
                           COALESCE\(p\.full_time, true\) as full_time, 
                           COALESCE\(p\.adjunct, false\) as adjunct, 
                           p\.uni_email as email, p\.other_email,
                           p\.uni_page, p\.website, p\.misc, p\.twitter, p\.linkedin, p\.phone, p\.fax,
                           p\.google_scholar, p\.scopus, p\.web_of_science, p\.orcid, p\.researchgate, p\.academicedu,
                           u\.name as university_name, u\.city, u\.province_state, u\.country
                    FROM professors p
                    LEFT JOIN universities u ON p\.university_id = u\.id
                    WHERE p\.id = \$1
                """'''
    
    new_professor_detail = r'''query = """
                    SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                           p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                           p.university_code, p.faculty, p.department, p.other_departments,
                           p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                           COALESCE(p.position, '') as position, 
                           COALESCE(p.full_time, true) as full_time, 
                           COALESCE(p.adjunct, false) as adjunct, 
                           p.uni_email as email, p.other_email,
                           p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                           p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate, p.academicedu,
                           u.name as university_name, u.city, u.province_state, u.country
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.id = $1
                """'''
    
    content = re.sub(professor_detail_pattern, new_professor_detail, content, flags=re.DOTALL)
    
    # Fix countries query
    countries_query_pattern = r'''query = """
                SELECT u\.country, 
                       COUNT\(DISTINCT u\.id\) as university_count,
                       COUNT\(DISTINCT p\.id\) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON u\.id = p\.university_id
                WHERE u\.country IS NOT NULL AND u\.country != ''
                GROUP BY u\.country
                ORDER BY faculty_count DESC, university_count DESC
            """'''
    
    new_countries_query = r'''query = """
                SELECT u.country, 
                       COUNT(DISTINCT u.id) as university_count,
                       COUNT(DISTINCT p.id) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON u.university_code = p.university_code
                WHERE u.country IS NOT NULL AND u.country != ''
                GROUP BY u.country
                ORDER BY faculty_count DESC, university_count DESC
            """'''
    
    content = re.sub(countries_query_pattern, new_countries_query, content, flags=re.DOTALL)
    
    # Fix university detail query
    university_detail_pattern = r'''query = """
                SELECT u\.id, u\.name, u\.country, u\.city, u\.university_code, 
                       COALESCE\(u\.province_state, ''\) as province, u\.year_established,
                       COALESCE\(u\.website, ''\) as website, COALESCE\(u\.university_type, 'Public'\) as university_type,
                       COUNT\(p\.id\) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON u\.id = p\.university_id
                WHERE u\.university_code = \$1
                GROUP BY u\.id, u\.name, u\.country, u\.city, u\.university_code, u\.province_state, 
                         u\.year_established, u\.website, u\.university_type
            """'''
    
    new_university_detail = r'''query = """
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province, u.year_established,
                       COALESCE(u.website, '') as website, COALESCE(u.university_type, 'Public') as university_type,
                       COUNT(p.id) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON u.university_code = p.university_code
                WHERE u.university_code = $1
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state, 
                         u.year_established, u.website, u.university_type
            """'''
    
    content = re.sub(university_detail_pattern, new_university_detail, content, flags=re.DOTALL)
    
    # Write the fixed content back
    with open('webapp/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed FastAPI queries for PostgreSQL schema")
    return True

def main():
    """Main function"""
    print("🔧 Fixing FastAPI Schema Compatibility")
    print("=====================================")
    
    if fix_fastapi_queries():
        print("🎉 FastAPI schema compatibility fixed!")
        return True
    else:
        print("❌ Failed to fix FastAPI schema compatibility")
        return False

if __name__ == "__main__":
    main() 