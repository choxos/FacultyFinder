#!/usr/bin/env python3
"""
Diagnose Universities API 500 Error
Check database schema and test queries to identify the issue
"""

import asyncio
import asyncpg

async def diagnose_universities_error():
    """Diagnose the universities API error"""
    
    # Use the exact credentials
    host = 'localhost'
    port = '5432'
    database = 'ff_production'
    user = 'ff_user'
    password = 'Choxos10203040'
    
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    print("🔍 Diagnosing Universities API 500 Error")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connection successful")
        
        # Check universities table schema
        print(f"\n📋 Universities Table Schema:")
        schema_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'universities' 
            ORDER BY ordinal_position
        """
        
        columns = await conn.fetch(schema_query)
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Check what field names actually exist
        column_names = [col['column_name'] for col in columns]
        
        print(f"\n🔍 Field Mapping Check:")
        # Check our expected fields vs actual fields
        expected_new = ['type', 'language', 'established']
        expected_old = ['university_type', 'languages', 'year_established']
        
        for new_field, old_field in zip(expected_new, expected_old):
            if new_field in column_names:
                print(f"  ✅ {new_field} (new format)")
            elif old_field in column_names:
                print(f"  ⚠️  {old_field} (old format - needs mapping fix)")
            else:
                print(f"  ❌ Neither {new_field} nor {old_field} found")
        
        # Test a simple universities query
        print(f"\n🧪 Testing Basic Universities Query:")
        try:
            basic_query = """
                SELECT u.id, u.name, u.country, u.city, u.university_code
                FROM universities u
                LIMIT 3
            """
            basic_results = await conn.fetch(basic_query)
            print(f"✅ Basic query successful - {len(basic_results)} results")
            for row in basic_results:
                print(f"  - {row['name']}, {row['city']}, {row['country']}")
        except Exception as e:
            print(f"❌ Basic query failed: {e}")
        
        # Test the problematic field references
        print(f"\n🧪 Testing Field References:")
        
        # Test with new field names
        try:
            new_fields_query = """
                SELECT u.id, u.name, 
                       COALESCE(u.type, '') as type,
                       COALESCE(u.language, '') as language,
                       u.established
                FROM universities u
                LIMIT 1
            """
            await conn.fetchrow(new_fields_query)
            print(f"✅ New field names (type, language, established) work")
        except Exception as e:
            print(f"❌ New field names failed: {e}")
            
            # Try old field names
            try:
                old_fields_query = """
                    SELECT u.id, u.name, 
                           COALESCE(u.university_type, '') as university_type,
                           COALESCE(u.languages, '') as languages,
                           u.year_established
                    FROM universities u
                    LIMIT 1
                """
                await conn.fetchrow(old_fields_query)
                print(f"✅ Old field names (university_type, languages, year_established) work")
                print(f"🔧 SOLUTION: Database still uses old field names - API needs to be reverted")
            except Exception as e2:
                print(f"❌ Old field names also failed: {e2}")
        
        # Test the actual API query
        print(f"\n🧪 Testing Actual API Query:")
        try:
            api_query = """
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province_state,
                       COALESCE(u.address, '') as address,
                       COALESCE(u.website, '') as website,
                       COALESCE(u.type, '') as type,
                       COALESCE(u.language, '') as language,
                       u.established,
                       COUNT(p.id) as faculty_count,
                       COUNT(DISTINCT COALESCE(p.department, 'Unknown')) as department_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE u.name IS NOT NULL
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state,
                         u.address, u.website, u.type, u.language, u.established
                HAVING COUNT(p.id) >= 0
                ORDER BY faculty_count DESC
                LIMIT 3
            """
            api_results = await conn.fetch(api_query)
            print(f"✅ API query successful - {len(api_results)} results")
            for row in api_results:
                print(f"  - {row['name']}: {row['faculty_count']} faculty")
        except Exception as e:
            print(f"❌ API query failed: {e}")
            print(f"🔧 This is likely the cause of the 500 error")
            
            # Try with old field names
            try:
                api_query_old = """
                    SELECT u.id, u.name, u.country, u.city, u.university_code, 
                           COALESCE(u.province_state, '') as province_state,
                           COALESCE(u.address, '') as address,
                           COALESCE(u.website, '') as website,
                           COALESCE(u.university_type, '') as university_type,
                           COALESCE(u.languages, '') as languages,
                           u.year_established,
                           COUNT(p.id) as faculty_count,
                           COUNT(DISTINCT COALESCE(p.department, 'Unknown')) as department_count
                    FROM universities u
                    LEFT JOIN professors p ON p.university_code = u.university_code
                    WHERE u.name IS NOT NULL
                    GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state,
                             u.address, u.website, u.university_type, u.languages, u.year_established
                    HAVING COUNT(p.id) >= 0
                    ORDER BY faculty_count DESC
                    LIMIT 3
                """
                api_results_old = await conn.fetch(api_query_old)
                print(f"✅ API query with old field names successful - {len(api_results_old)} results")
                print(f"🔧 SOLUTION: Revert API to use old field names")
            except Exception as e2:
                print(f"❌ API query with old field names also failed: {e2}")
        
        await conn.close()
        
        print(f"\n🎯 Diagnosis Summary:")
        print(f"=" * 30)
        
        if 'type' in column_names and 'language' in column_names and 'established' in column_names:
            print(f"✅ Database has new field names - API should work")
        elif 'university_type' in column_names and 'languages' in column_names and 'year_established' in column_names:
            print(f"❌ Database still has old field names")
            print(f"🔧 SOLUTION: Revert webapp/main.py to use old field names")
            print(f"   OR: Update database schema to use new field names")
        else:
            print(f"❌ Database schema is inconsistent")
            print(f"🔧 SOLUTION: Check database migration and field consistency")
        
        print(f"\n📋 Quick Fix Commands:")
        print(f"   Test API: curl http://localhost:8008/api/v1/universities?per_page=3")
        print(f"   Check logs: sudo journalctl -u facultyfinder.service -f")
        print(f"   Database: psql -h localhost -U ff_user -d ff_production")
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_universities_error()) 