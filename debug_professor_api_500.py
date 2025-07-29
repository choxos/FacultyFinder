#!/usr/bin/env python3
"""
Debug Professor API 500 Errors
Test the professor API queries to identify why they're still failing
"""

import asyncio
import asyncpg

async def debug_professor_api():
    """Debug professor API 500 errors"""
    
    database_url = "postgresql://ff_user:Choxos10203040@localhost:5432/ff_production"
    
    print("🔍 Debugging Professor API 500 Errors")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connected")
        
        # Test 1: Check professor_id_new column and data
        print(f"\n📊 Testing professor_id_new column...")
        prof_count = await conn.fetchval("SELECT COUNT(*) FROM professors WHERE professor_id_new IS NOT NULL")
        print(f"✅ {prof_count} professors have professor_id_new values")
        
        # Test 2: Try the exact API query for integer ID
        print(f"\n🧪 Testing integer ID query (professor ID 1)...")
        try:
            integer_query = """
                SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                       p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                       p.university_code, p.faculty, p.department, p.other_departments,
                       p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                       COALESCE(p.position, '') as position, 
                       COALESCE(p.full_time, true) as full_time, 
                       COALESCE(p.adjunct, false) as adjunct, 
                       p.uni_email as email, p.other_email,
                       p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                       p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
                       p.academicedu, p.created_at, p.updated_at,
                       COALESCE(p.publication_count, 0) as publication_count,
                       COALESCE(p.citation_count, 0) as citation_count,
                       COALESCE(p.h_index, 0) as h_index,
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
            
            result = await conn.fetchrow(integer_query, 1)
            if result:
                print(f"✅ Integer ID query successful: {result['name']}")
            else:
                print("❌ Integer ID query returned no results")
                
        except Exception as e:
            print(f"❌ Integer ID query failed: {e}")
        
        # Test 3: Try the string ID query
        print(f"\n🧪 Testing string ID query (CA-ON-002-00001)...")
        try:
            string_query = """
                SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                       p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                       p.university_code, p.faculty, p.department, p.other_departments,
                       p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                       COALESCE(p.position, '') as position, 
                       COALESCE(p.full_time, true) as full_time, 
                       COALESCE(p.adjunct, false) as adjunct, 
                       p.uni_email as email, p.other_email,
                       p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                       p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
                       p.academicedu, p.created_at, p.updated_at,
                       COALESCE(p.publication_count, 0) as publication_count,
                       COALESCE(p.citation_count, 0) as citation_count,
                       COALESCE(p.h_index, 0) as h_index,
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
            
            result = await conn.fetchrow(string_query, "CA-ON-002-00001")
            if result:
                print(f"✅ String ID query successful: {result['name']}")
            else:
                print("❌ String ID query returned no results")
                # Check what professor_id_new values actually exist
                sample_ids = await conn.fetch("SELECT professor_id_new FROM professors WHERE professor_id_new IS NOT NULL LIMIT 5")
                print("📋 Sample professor_id_new values:")
                for row in sample_ids:
                    print(f"   {row['professor_id_new']}")
                
        except Exception as e:
            print(f"❌ String ID query failed: {e}")
        
        # Test 4: Check universities table columns
        print(f"\n🏛️  Testing universities table...")
        try:
            uni_columns = await conn.fetch("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'universities'
            """)
            column_names = [col['column_name'] for col in uni_columns]
            print(f"📋 Universities table columns: {', '.join(column_names)}")
            
            # Check specific problematic columns
            if 'province_state' not in column_names:
                print("❌ Missing province_state column in universities table")
            else:
                print("✅ province_state column exists")
                
        except Exception as e:
            print(f"❌ Universities table check failed: {e}")
        
        # Test 5: Test fallback query (university + offset)
        print(f"\n🧪 Testing fallback query (university + offset)...")
        try:
            fallback_query = """
                SELECT p.id, p.name, p.university_code
                FROM professors p
                WHERE p.university_code = $1
                ORDER BY p.name, p.id
                LIMIT 1 OFFSET $2
            """
            
            result = await conn.fetchrow(fallback_query, "CA-ON-002", 0)  # Get first professor
            if result:
                print(f"✅ Fallback query successful: {result['name']} (ID: {result['id']})")
            else:
                print("❌ Fallback query returned no results")
                
        except Exception as e:
            print(f"❌ Fallback query failed: {e}")
        
        await conn.close()
        
        print(f"\n🎯 Diagnosis Summary:")
        print(f"=" * 30)
        print(f"1. Check the actual API endpoint error in FastAPI logs")
        print(f"2. Ensure all database columns exist as expected")
        print(f"3. Verify the API query matches the database schema")
        
        print(f"\n📋 Next Steps:")
        print(f"   Check logs: sudo journalctl -u facultyfinder.service -f")
        print(f"   Test direct API: curl -v http://localhost:8008/api/v1/professor/1")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_professor_api()) 