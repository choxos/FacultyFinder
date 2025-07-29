#!/usr/bin/env python3
"""
Fix Empty Professor Record
Remove the professor with empty name that got assigned CA-ON-002-00272
"""

import asyncio
import asyncpg

async def fix_empty_professor():
    """Remove empty professor record"""
    
    database_url = "postgresql://ff_user:Choxos10203040@localhost:5432/ff_production"
    
    print("🧹 Fixing Empty Professor Record")
    print("=" * 40)
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connected")
        
        # Find empty or null name professors
        empty_profs = await conn.fetch("""
            SELECT id, name, professor_id_new, university_code 
            FROM professors 
            WHERE name IS NULL OR name = '' OR TRIM(name) = ''
        """)
        
        print(f"\n🔍 Found {len(empty_profs)} empty professor records:")
        for prof in empty_profs:
            print(f"  ID {prof['id']}: '{prof['name']}' → {prof['professor_id_new']} ({prof['university_code']})")
        
        if empty_profs:
            # Delete empty professor records
            for prof in empty_profs:
                await conn.execute("DELETE FROM professors WHERE id = $1", prof['id'])
                print(f"🗑️  Deleted professor ID {prof['id']} (empty name)")
            
            print(f"\n✅ Removed {len(empty_profs)} empty professor records")
            
            # Recount remaining professors
            remaining_count = await conn.fetchval("SELECT COUNT(*) FROM professors")
            mcmaster_count = await conn.fetchval("""
                SELECT COUNT(*) FROM professors WHERE university_code = 'CA-ON-002'
            """)
            
            print(f"📊 Remaining professors:")
            print(f"   Total: {remaining_count}")
            print(f"   McMaster: {mcmaster_count}")
            
            # Show the highest professor ID for reference
            highest_prof = await conn.fetchrow("""
                SELECT name, professor_id_new 
                FROM professors 
                WHERE university_code = 'CA-ON-002' 
                ORDER BY id DESC 
                LIMIT 1
            """)
            
            if highest_prof:
                print(f"   Highest ID: {highest_prof['name']} → {highest_prof['professor_id_new']}")
        
        else:
            print("✅ No empty professor records found")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing empty professor: {e}")

if __name__ == "__main__":
    asyncio.run(fix_empty_professor()) 