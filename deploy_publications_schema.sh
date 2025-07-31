#!/bin/bash
# deploy_publications_schema.sh
# Deploy Publications Database Schema to PostgreSQL

echo "🗄️  Deploying Publications Database Schema..."

# Check if .env file exists
if [ -f .env ]; then
    source .env
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found. Please create it with database credentials:"
    echo "   DB_HOST=your_vps_ip"
    echo "   DB_PORT=5432"
    echo "   DB_NAME=facultyfinder"
    echo "   DB_USER=your_db_user"
    echo "   DB_PASSWORD=your_db_password"
    exit 1
fi

# Verify required environment variables
if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo "❌ Missing required environment variables. Please check your .env file."
    exit 1
fi

# Test database connection
echo "🔍 Testing database connection..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please check your credentials and ensure PostgreSQL is running."
    exit 1
fi

echo "✅ Database connection successful"

# Apply publications schema
echo "📊 Creating publications tables and indexes..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -f database/publications_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Publications schema deployed successfully!"
else
    echo "❌ Schema deployment failed"
    exit 1
fi

# Verify tables were created
echo "🔍 Verifying table creation..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -c "
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('publications', 'faculty_publications', 'author_profiles', 'research_collaborations', 'publication_metrics_cache')
ORDER BY tablename;
"

echo ""
echo "📈 Verifying indexes..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -c "
SELECT 
    indexname,
    tablename
FROM pg_indexes 
WHERE tablename LIKE '%publication%' OR tablename LIKE '%author%'
ORDER BY tablename, indexname;
"

echo ""
echo "🔧 Verifying functions..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -c "
SELECT 
    proname as function_name,
    pg_get_function_result(oid) as returns
FROM pg_proc 
WHERE proname IN ('update_modified_column', 'refresh_faculty_metrics');
"

echo ""
echo "👁️  Verifying views..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -c "
SELECT 
    viewname,
    viewowner
FROM pg_views 
WHERE viewname IN ('faculty_publication_summary', 'top_cited_publications', 'collaboration_network')
ORDER BY viewname;
"

# Test the metrics function
echo ""
echo "🧪 Testing metrics calculation function..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -c "
-- Test with a dummy faculty ID (this should not fail even if faculty doesn't exist)
SELECT refresh_faculty_metrics('TEST-FACULTY-001');
SELECT 'Function test completed' as result;
"

echo ""
echo "📊 Database schema summary:"
echo "=================================="
echo "Tables created:"
echo "  ✓ publications - Core publication storage"
echo "  ✓ faculty_publications - Faculty-publication relationships"  
echo "  ✓ author_profiles - OpenAlex author information"
echo "  ✓ research_collaborations - Collaboration tracking"
echo "  ✓ publication_metrics_cache - Performance optimization"
echo ""
echo "Views created:"
echo "  ✓ faculty_publication_summary - Combined faculty metrics"
echo "  ✓ top_cited_publications - Most cited papers with authors"
echo "  ✓ collaboration_network - Research collaboration network"
echo ""
echo "Functions created:"
echo "  ✓ update_modified_column() - Auto-update timestamps"
echo "  ✓ refresh_faculty_metrics() - Calculate faculty metrics"
echo ""
echo "Indexes created:"
echo "  ✓ Performance indexes on all key columns"
echo "  ✓ Full-text search indexes for title/abstract"
echo "  ✓ JSONB indexes for complex queries"
echo "=================================="

echo ""
echo "🎯 Next steps:"
echo "1. Run the publications importer: python3 publications_importer.py"
echo "2. Update your FastAPI application with new endpoints"
echo "3. Test the API endpoints"
echo "4. Deploy to production"

echo ""
echo "✅ Publications database ready for data import!" 