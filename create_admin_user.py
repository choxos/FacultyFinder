#!/usr/bin/env python3
"""
Create Admin User Script
Creates an admin user for the FacultyFinder application
"""

import asyncio
import asyncpg
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

async def create_admin_user():
    """Create an admin user in the database"""
    
    # Database connection configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'test_user'),
        'password': os.getenv('DB_PASSWORD', 'test_password'),
        'database': os.getenv('DB_NAME', 'test_db')
    }
    
    # Admin user details
    admin_data = {
        'username': 'admin',
        'email': 'admin@facultyfinder.io',
        'password': 'admin123',  # Change this to a secure password
        'first_name': 'System',
        'last_name': 'Administrator'
    }
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to database")
        
        # Check if admin user already exists
        existing_user = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1 OR email = $2",
            admin_data['username'], admin_data['email']
        )
        
        if existing_user:
            print(f"⚠️  Admin user already exists: {existing_user['username']} ({existing_user['email']})")
            
            # Update to admin role if not already admin
            if not existing_user.get('is_admin') and existing_user.get('role') != 'admin':
                await conn.execute("""
                    UPDATE users 
                    SET role = 'admin', is_admin = TRUE 
                    WHERE id = $1
                """, existing_user['id'])
                print("✅ Updated existing user to admin role")
            else:
                print("✅ User already has admin privileges")
        else:
            # Create password hash (using simple SHA256 for now - should use bcrypt in production)
            password_hash = hashlib.sha256(admin_data['password'].encode()).hexdigest()
            
            # Insert new admin user
            user = await conn.fetchrow("""
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name,
                    role, is_admin, is_active, email_verified
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
            """, 
            admin_data['username'],
            admin_data['email'],
            password_hash,
            admin_data['first_name'],
            admin_data['last_name'],
            'admin',
            True,
            True,
            True
            )
            
            print(f"✅ Created admin user: {user['username']} ({user['email']})")
            print(f"   User ID: {user['id']}")
            print(f"   Role: {user['role']}")
            print(f"   Is Admin: {user.get('is_admin', False)}")
        
        await conn.close()
        print("\n🎉 Admin user setup complete!")
        print("\n📝 Login credentials:")
        print(f"   Username: {admin_data['username']}")
        print(f"   Email: {admin_data['email']}")
        print(f"   Password: {admin_data['password']}")
        print("\n⚠️  Please change the password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 FacultyFinder Admin User Creation Script")
    print("=" * 50)
    
    asyncio.run(create_admin_user()) 