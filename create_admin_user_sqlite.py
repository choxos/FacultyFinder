#!/usr/bin/env python3
"""
Create Admin User Script (SQLite version)
Creates an admin user for the FacultyFinder application using SQLite
"""

import sqlite3
import hashlib
import os

def create_admin_user():
    """Create an admin user in the SQLite database"""
    
    # Database path
    db_path = "database/facultyfinder_dev.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
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
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()
        print("✅ Connected to SQLite database")
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            print("❌ Users table not found in database")
            return False
        
        # Check if admin user already exists
        cursor.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (admin_data['username'], admin_data['email'])
        )
        
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"⚠️  Admin user already exists: {existing_user['username']} ({existing_user['email']})")
            
            # Update to admin role if not already admin
            if existing_user['role'] != 'admin':
                cursor.execute("""
                    UPDATE users 
                    SET role = 'admin'
                    WHERE id = ?
                """, (existing_user['id'],))
                conn.commit()
                print("✅ Updated existing user to admin role")
            else:
                print("✅ User already has admin privileges")
        else:
            # Create password hash (using simple SHA256 for now - should use bcrypt in production)
            password_hash = hashlib.sha256(admin_data['password'].encode()).hexdigest()
            
            # Insert new admin user
            cursor.execute("""
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name,
                    role, is_active, email_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                admin_data['username'],
                admin_data['email'],
                password_hash,
                admin_data['first_name'],
                admin_data['last_name'],
                'admin',
                True,
                True
            ))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            print(f"✅ Created admin user: {admin_data['username']} ({admin_data['email']})")
            print(f"   User ID: {user_id}")
            print(f"   Role: admin")
        
        conn.close()
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
    print("🔧 FacultyFinder Admin User Creation Script (SQLite)")
    print("=" * 55)
    
    create_admin_user() 