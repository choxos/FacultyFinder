#!/usr/bin/env python3
"""
Quick Universities API Fix
Test database schema and fix field mapping issues
"""

import asyncio
import asyncpg

async def test_and_fix():
    database_url = "postgresql://ff_user:Choxos10203040@localhost:5432/ff_production"
    
    print("🔍 Testing Universities Database Schema")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check if old or new field names exist
        columns_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'universities'"
        columns = await conn.fetch(columns_query)
        column_names = [col['column_name'] for col in columns]
        
        print(f"📋 Available columns: {', '.join(column_names)}")
        
        # Test which field names work
        if 'university_type' in column_names:
            print("✅ Database uses OLD field names: university_type, languages, year_established")
            print("🔧 Need to revert API to use old field names")
        elif 'type' in column_names:
            print("✅ Database uses NEW field names: type, language, established")
            print("✅ API should work with current field mapping")
        
        # Test the actual problematic query
        try:
            test_query = """
                SELECT u.id, u.name, u.university_type as type, u.languages as language, u.year_established as established
                FROM universities u LIMIT 1
            """
            await conn.fetchrow(test_query)
            print("✅ OLD field names work - need to fix API")
        except:
            try:
                test_query = """
                    SELECT u.id, u.name, u.type, u.language, u.established
                    FROM universities u LIMIT 1
                """
                await conn.fetchrow(test_query)
                print("✅ NEW field names work - API should be fine")
            except Exception as e:
                print(f"❌ Both field name formats fail: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_and_fix()) 