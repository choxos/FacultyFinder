#!/bin/bash

echo "🔧 Fixing Database Credentials"
echo "=============================="
echo "Setting correct database credentials for ff_production"
echo ""

# Create or update .env file with correct credentials
echo "📝 Creating/updating .env file..."

cat > .env << EOF
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ff_production
DB_USER=ff_user
DB_PASSWORD=Choxos10203040

# Alternative format (for compatibility)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=ff_production
DATABASE_USER=ff_user
DATABASE_PASSWORD=Choxos10203040
EOF

echo "✅ .env file created with correct credentials"

# Make test script executable
chmod +x test_db_connection_fix.py

# Test database connection
echo -e "\n🧪 Testing database connection..."
python3 test_db_connection_fix.py

if [ $? -eq 0 ]; then
    echo -e "\n🎉 Database credentials verified!"
    echo "✅ Ready to generate professor IDs"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Run: python3 generate_professor_ids.py"
    echo "   2. Run: sudo systemctl restart facultyfinder.service"
    echo "   3. Test: curl http://localhost:8008/api/v1/professor/CA-ON-002-00001"
else
    echo -e "\n❌ Database connection still failing"
    echo "🔧 Troubleshooting:"
    echo "   1. Check if PostgreSQL is running: sudo systemctl status postgresql"
    echo "   2. Verify database exists: sudo -u postgres psql -l | grep ff_production"
    echo "   3. Test credentials manually: psql -h localhost -U ff_user -d ff_production"
fi 