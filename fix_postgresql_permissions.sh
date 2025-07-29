#!/bin/bash

echo "🔧 Fixing PostgreSQL Permissions for FacultyFinder"
echo "================================================="

echo "🔍 Diagnosing PostgreSQL permission issues..."

# Check current user permissions
echo "📋 Current ff_user permissions:"
sudo -u postgres psql -d ff_production -c "
SELECT 
    r.rolname AS role_name,
    r.rolsuper AS is_superuser,
    r.rolcreaterole AS can_create_roles,
    r.rolcreatedb AS can_create_databases,
    r.rolcanlogin AS can_login
FROM pg_roles r 
WHERE r.rolname = 'ff_user';
"

echo
echo "📋 Database permissions:"
sudo -u postgres psql -d ff_production -c "
SELECT 
    datname,
    datacl 
FROM pg_database 
WHERE datname = 'ff_production';
"

echo
echo "📋 Schema permissions:"
sudo -u postgres psql -d ff_production -c "
SELECT 
    nspname AS schema_name,
    nspacl AS permissions
FROM pg_namespace 
WHERE nspname = 'public';
"

echo
echo "🔧 Fixing permissions..."

# Grant necessary permissions to ff_user
echo "✅ Granting database permissions..."
sudo -u postgres psql -c "
-- Grant database connection and creation privileges
GRANT ALL PRIVILEGES ON DATABASE ff_production TO ff_user;

-- Grant usage and creation on public schema
GRANT USAGE ON SCHEMA public TO ff_user;
GRANT CREATE ON SCHEMA public TO ff_user;

-- Grant all privileges on public schema
GRANT ALL ON SCHEMA public TO ff_user;

-- Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ff_user;

-- Grant all privileges on all sequences in public schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ff_user;

-- Grant all privileges on all functions in public schema
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ff_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ff_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ff_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ff_user;
"

echo "✅ Database permissions granted"

# Alternative: Make ff_user a superuser (more permissive)
echo
echo "🔧 Alternative: Making ff_user a superuser for easier management..."
sudo -u postgres psql -c "ALTER USER ff_user WITH SUPERUSER;"

echo "✅ ff_user is now a superuser"

echo
echo "🧪 Testing permissions..."

# Test if ff_user can now create tables
sudo -u postgres psql -d ff_production -c "
-- Switch to ff_user
SET ROLE ff_user;

-- Try to create a test table
CREATE TABLE IF NOT EXISTS permission_test (
    id SERIAL PRIMARY KEY,
    test_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test data
INSERT INTO permission_test (test_message) VALUES ('Permission test successful');

-- Check the data
SELECT * FROM permission_test;

-- Clean up
DROP TABLE permission_test;

-- Reset role
RESET ROLE;
"

if [ $? -eq 0 ]; then
    echo "✅ Permission test successful!"
else
    echo "❌ Permission test failed"
fi

echo
echo "📋 Updated ff_user permissions:"
sudo -u postgres psql -d ff_production -c "
SELECT 
    r.rolname AS role_name,
    r.rolsuper AS is_superuser,
    r.rolcreaterole AS can_create_roles,
    r.rolcreatedb AS can_create_databases,
    r.rolcanlogin AS can_login
FROM pg_roles r 
WHERE r.rolname = 'ff_user';
"

echo
echo "🎯 Next steps:"
echo "1. Try running the data migration again:"
echo "   python3 data_migration_system.py --data-dir /var/www/ff/data_import"
echo
echo "2. If it still fails, try the simple import:"
echo "   python3 simple_data_import.py"
echo
echo "3. Check the migration logs for any remaining issues"

echo
echo "✅ PostgreSQL permissions fix completed!" 