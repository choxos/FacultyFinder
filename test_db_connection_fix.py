#!/usr/bin/env python3
"""
Test Database Connection with Correct Credentials
"""

import asyncio
import asyncpg

async def test_connection():
    """Test database connection with user's credentials"""
    
    # Use the exact credentials provided by the user
    host = 'localhost'
    port = '5432'
    database = 'ff_production'
    user = 'ff_user'
    password = 'Choxos10203040'
    
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    print("🔗 Testing database connection...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Database: {database}")
    print(f"   User: {user}")
    print(f"   Password: {'*' * len(password)}")
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connection successful!")
        
        # Test a simple query
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM professors")
        print(f"📊 Found {result['count']} professors in database")
        
        # Test universities table
        result = await conn.fetchrow("SELECT COUNT(*) as count FROM universities")
        print(f"🏛️  Found {result['count']} universities in database")
        
        await conn.close()
        print("✅ Connection test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print("\n🎉 Database credentials are correct!")
        print("📋 You can now run: ./generate_professor_ids.py")
    else:
        print("\n❌ Database credentials need to be fixed")
        print("📋 Please check your database settings") 