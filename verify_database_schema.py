#!/usr/bin/env python3
"""
Verify Database Schema Field Mapping
Check if database columns match CSV field names
"""

import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
env_files = ['/var/www/ff/.env', '.env', '.env.test']
for env_file in env_files:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        break

def get_database_url():
    """Construct database URL from environment variables"""
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = os.getenv('DATABASE_PORT', '5432')
    name = os.getenv('DATABASE_NAME', 'facultyfinder')
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', '')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

async def verify_schema():
    """Verify database schema matches CSV field names"""
    database_url = get_database_url()
    print(f"🔗 Connecting to database...")
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connected successfully")
        
        # Check professors table columns
        print(f"\n📋 Professors Table Columns:")
        professors_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'professors' 
            ORDER BY ordinal_position
        """)
        
        expected_professor_fields = [
            'name', 'first_name', 'last_name', 'middle_names', 'other_name',
            'degree', 'all_degrees_and_inst', 'all_degrees_only', 'research_areas',
            'university_code', 'university', 'faculty', 'department', 'other_depts',
            'primary_aff', 'membership', 'canada_research_chair', 'director',
            'position', 'full_time', 'adjunct', 'uni_email', 'other_email',
            'uni_page', 'website', 'misc', 'twitter', 'phone', 'fax',
            'gscholar', 'scopus', 'wos', 'orcid', 'researchgate', 'academicedu', 'linkedin'
        ]
        
        actual_professor_columns = [col['column_name'] for col in professors_columns]
        
        for field in expected_professor_fields:
            if field in actual_professor_columns:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} - MISSING")
        
        print(f"\n🏛️  Universities Table Columns:")
        universities_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'universities' 
            ORDER BY ordinal_position
        """)
        
        expected_university_fields = [
            'university_code', 'university_name', 'country', 'province_state',
            'city', 'address', 'website', 'type', 'language', 'established'
        ]
        
        actual_university_columns = [col['column_name'] for col in universities_columns]
        
        for field in expected_university_fields:
            if field in actual_university_columns:
                print(f"  ✅ {field}")
            elif field == 'type' and 'university_type' in actual_university_columns:
                print(f"  ⚠️  {field} → found 'university_type' instead")
            elif field == 'language' and 'languages' in actual_university_columns:
                print(f"  ⚠️  {field} → found 'languages' instead")
            elif field == 'established' and 'year_established' in actual_university_columns:
                print(f"  ⚠️  {field} → found 'year_established' instead")
            else:
                print(f"  ❌ {field} - MISSING")
        
        # Check specific problematic fields
        print(f"\n🔍 Field Mapping Analysis:")
        
        # Check if CSV field 'type' maps to database 'university_type'
        if 'type' in actual_university_columns:
            print(f"  ✅ University type field: 'type' (matches CSV)")
        elif 'university_type' in actual_university_columns:
            print(f"  ⚠️  University type field: 'university_type' (should be 'type' to match CSV)")
        
        # Check if CSV field 'language' maps to database 'languages'
        if 'language' in actual_university_columns:
            print(f"  ✅ Language field: 'language' (matches CSV)")
        elif 'languages' in actual_university_columns:
            print(f"  ⚠️  Language field: 'languages' (should be 'language' to match CSV)")
        
        # Check if CSV field 'established' maps to database 'year_established'
        if 'established' in actual_university_columns:
            print(f"  ✅ Established field: 'established' (matches CSV)")
        elif 'year_established' in actual_university_columns:
            print(f"  ⚠️  Established field: 'year_established' (should be 'established' to match CSV)")
        
        # Check professor specific fields
        if 'position' in actual_professor_columns:
            print(f"  ✅ Professor position field: 'position' (matches CSV)")
        else:
            print(f"  ❌ Professor position field: MISSING")
        
        if 'full_time' in actual_professor_columns:
            print(f"  ✅ Full-time field: 'full_time' (matches CSV)")
        else:
            print(f"  ❌ Full-time field: MISSING")
        
        if 'adjunct' in actual_professor_columns:
            print(f"  ✅ Adjunct field: 'adjunct' (matches CSV)")
        else:
            print(f"  ❌ Adjunct field: MISSING")
        
        # Sample data check
        print(f"\n📊 Sample Data Check:")
        
        # Check a few professor records
        sample_professors = await conn.fetch("""
            SELECT name, position, full_time, adjunct, university_code
            FROM professors 
            LIMIT 3
        """)
        
        print(f"  Sample Professors:")
        for prof in sample_professors:
            print(f"    - {prof['name']}: {prof['position']}, Full-time: {prof['full_time']}, Adjunct: {prof['adjunct']}")
        
        # Check a few university records
        sample_universities = await conn.fetch("""
            SELECT university_code, name, country, city
            FROM universities 
            LIMIT 3
        """)
        
        print(f"  Sample Universities:")
        for uni in sample_universities:
            print(f"    - {uni['university_code']}: {uni['name']}, {uni['city']}, {uni['country']}")
        
        await conn.close()
        
        print(f"\n🎯 Field Mapping Recommendations:")
        print(f"1. Ensure database column names match CSV headers exactly")
        print(f"2. Update API queries to use correct field names")
        print(f"3. Verify data import process uses correct field mapping")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    print("🔍 Database Schema Verification")
    print("=" * 50)
    print("Checking if database fields match CSV structure")
    print("=" * 50)
    
    await verify_schema()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 