#!/usr/bin/env python3
"""
Create Admin User with Granular Permissions Script (PostgreSQL)
Creates admin users with specific permission levels for FacultyFinder
"""

import asyncio
import asyncpg
import hashlib
import os
import sys
from dotenv import load_dotenv

load_dotenv()

ADMIN_ROLES = {
    "superuser": {
        "description": "Full access to all admin features",
        "permissions": {
            "can_manage_ai_requests": True,
            "can_manage_database": True,
            "can_manage_users": True,
            "is_superuser": True
        }
    },
    "ai_admin": {
        "description": "Can manage AI requests and payments only",
        "permissions": {
            "can_manage_ai_requests": True,
            "can_manage_database": False,
            "can_manage_users": False,
            "is_superuser": False
        }
    },
    "database_admin": {
        "description": "Can manage universities, professors, and database only",
        "permissions": {
            "can_manage_ai_requests": False,
            "can_manage_database": True,
            "can_manage_users": False,
            "is_superuser": False
        }
    },
    "user_manager": {
        "description": "Can manage users only",
        "permissions": {
            "can_manage_ai_requests": False,
            "can_manage_database": False,
            "can_manage_users": True,
            "is_superuser": False
        }
    },
    "ai_database_admin": {
        "description": "Can manage both AI requests and database",
        "permissions": {
            "can_manage_ai_requests": True,
            "can_manage_database": True,
            "can_manage_users": False,
            "is_superuser": False
        }
    }
}

async def create_admin_user_with_permissions():
    """Create an admin user with specific permissions"""
    
    # Database connection configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'test_user'),
        'password': os.getenv('DB_PASSWORD', 'test_password'),
        'database': os.getenv('DB_NAME', 'test_db')
    }
    
    print("🔧 FacultyFinder Admin User Creation with Permissions")
    print("=" * 60)
    
    # Show available roles
    print("\n📋 Available Admin Roles:")
    for role_key, role_info in ADMIN_ROLES.items():
        print(f"   {role_key.upper()}: {role_info['description']}")
    
    # Get user input
    print(f"\n👤 Enter admin user details:")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    first_name = input("First Name: ").strip()
    last_name = input("Last Name: ").strip()
    
    print(f"\n🔐 Select admin role:")
    for i, (role_key, role_info) in enumerate(ADMIN_ROLES.items(), 1):
        print(f"   {i}. {role_key.upper()}: {role_info['description']}")
    
    while True:
        try:
            choice = int(input(f"Enter choice (1-{len(ADMIN_ROLES)}): "))
            if 1 <= choice <= len(ADMIN_ROLES):
                selected_role = list(ADMIN_ROLES.keys())[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    role_info = ADMIN_ROLES[selected_role]
    permissions = role_info['permissions']
    
    print(f"\n✅ Selected role: {selected_role.upper()}")
    print(f"   Description: {role_info['description']}")
    print(f"   Permissions: {', '.join([k.replace('can_manage_', '').replace('_', ' ').title() for k, v in permissions.items() if v])}")
    
    confirm = input(f"\n❓ Create admin user '{username}' with these permissions? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Admin user creation cancelled.")
        return False
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        print("\n✅ Connected to PostgreSQL database")
        
        # Check if users table exists and has permission columns
        table_info = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
        """)
        
        existing_columns = [row['column_name'] for row in table_info]
        
        if not existing_columns:
            print("❌ Users table not found. Creating table...")
            await conn.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    role VARCHAR(20) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    email_verified BOOLEAN DEFAULT FALSE,
                    
                    -- Granular Admin Permissions
                    can_manage_ai_requests BOOLEAN DEFAULT FALSE,
                    can_manage_database BOOLEAN DEFAULT FALSE,
                    can_manage_users BOOLEAN DEFAULT FALSE,
                    is_superuser BOOLEAN DEFAULT FALSE,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    verification_token VARCHAR(255),
                    reset_token VARCHAR(255),
                    reset_token_expires TIMESTAMP
                )
            """)
            print("✅ Users table created with permission columns")
        else:
            # Check if permission columns exist, if not add them
            permission_columns = ['can_manage_ai_requests', 'can_manage_database', 'can_manage_users', 'is_superuser']
            for col in permission_columns:
                if col not in existing_columns:
                    print(f"📝 Adding permission column: {col}")
                    await conn.execute(f"""
                        ALTER TABLE users 
                        ADD COLUMN {col} BOOLEAN DEFAULT FALSE
                    """)
        
        # Check if admin user already exists
        existing_user = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1 OR email = $2",
            username, email
        )
        
        if existing_user:
            print(f"⚠️  User already exists: {existing_user['username']} ({existing_user['email']})")
            
            update_confirm = input("❓ Update existing user with new permissions? (y/N): ").strip().lower()
            if update_confirm in ['y', 'yes']:
                # Update existing user with new permissions
                await conn.execute("""
                    UPDATE users 
                    SET role = 'admin', 
                        is_admin = TRUE,
                        can_manage_ai_requests = $2,
                        can_manage_database = $3,
                        can_manage_users = $4,
                        is_superuser = $5
                    WHERE id = $1
                """, existing_user['id'], 
                permissions['can_manage_ai_requests'],
                permissions['can_manage_database'], 
                permissions['can_manage_users'],
                permissions['is_superuser'])
                print("✅ Updated existing user with new permissions")
            else:
                print("❌ User update cancelled.")
                return False
        else:
            # Create password hash
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert new admin user with permissions
            user = await conn.fetchrow("""
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name,
                    role, is_admin, is_active, email_verified, is_verified,
                    can_manage_ai_requests, can_manage_database, 
                    can_manage_users, is_superuser
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING *
            """, 
            username, email, password_hash, first_name, last_name,
            'admin', True, True, True, True,
            permissions['can_manage_ai_requests'],
            permissions['can_manage_database'], 
            permissions['can_manage_users'],
            permissions['is_superuser']
            )
            
            print(f"\n✅ Created admin user: {user['username']} ({user['email']})")
            print(f"   User ID: {user['id']}")
            print(f"   Role: {selected_role.upper()}")
        
        await conn.close()
        print("\n🎉 Admin user setup complete!")
        print("\n📝 Login credentials:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Role: {selected_role.upper()}")
        print(f"   Permissions: {', '.join([k.replace('can_manage_', '').replace('_', ' ').title() for k, v in permissions.items() if v])}")
        print("\n🔗 Access admin panel at: https://facultyfinder.io/login")
        
        # Show accessible URLs
        print("\n🔍 Accessible Admin URLs:")
        print(f"   • Dashboard: https://facultyfinder.io/admin/dashboard")
        if permissions['can_manage_ai_requests']:
            print(f"   • AI Requests: https://facultyfinder.io/admin/ai-requests")
        if permissions['can_manage_database']:
            print(f"   • Database: https://facultyfinder.io/admin/database")
        if permissions['can_manage_users']:
            print(f"   • User Management: https://facultyfinder.io/admin/users")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(create_admin_user_with_permissions()) 