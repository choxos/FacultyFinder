#!/bin/bash

echo "🐘 Deploying PostgreSQL Schema for FacultyFinder"
echo "=============================================="

# Load database credentials
if [ -f "/var/www/ff/.env" ]; then
    export $(cat /var/www/ff/.env | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

echo "📊 Running PostgreSQL schema deployment..."

# Run the PostgreSQL schema
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -f database/schema_postgresql.sql

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL schema deployed successfully!"
else
    echo "❌ Schema deployment failed"
    exit 1
fi

echo ""
echo "📊 Checking database tables..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "\dt"

echo ""
echo "🧪 Testing database connection and basic queries..."

# Test universities table
echo "Testing universities table..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "SELECT COUNT(*) as university_count FROM universities;"

# Test professors table
echo "Testing professors table..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "SELECT COUNT(*) as professor_count FROM professors;"

echo ""
echo "🎉 PostgreSQL Schema Deployment Complete!"
echo "========================================"

echo "✅ Your database is now ready for:"
echo "   • Faculty and university data"
echo "   • Publication management with PubMed integration"
echo "   • Citation analysis and metrics"
echo "   • User authentication system"
echo "   • Cryptocurrency payment processing"

echo ""
echo "🚀 Next steps:"
echo "   1. Import your existing data with data migration scripts"
echo "   2. Run the FastAPI application"
echo "   3. Test the API endpoints" 