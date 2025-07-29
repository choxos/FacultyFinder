#!/bin/bash

echo "🚀 Comprehensive FacultyFinder Database Fix"
echo "==========================================="

# Step 1: Install required Python packages
echo "📦 Installing required packages..."
pip install psycopg2-binary pandas python-dotenv

# Step 2: Fix database schema and import data
echo "🗄️ Fixing database schema and importing data..."
python3 fix_database_schema_postgresql.py

if [ $? -ne 0 ]; then
    echo "❌ Database schema fix failed"
    exit 1
fi

# Step 3: Fix FastAPI schema compatibility
echo "🔧 Fixing FastAPI schema compatibility..."
python3 fix_fastapi_schema_compatibility.py

if [ $? -ne 0 ]; then
    echo "❌ FastAPI schema compatibility fix failed"
    exit 1
fi

# Step 4: Test Python syntax
echo "🧪 Testing Python syntax..."
python3 -m py_compile webapp/main.py

if [ $? -ne 0 ]; then
    echo "❌ Python syntax error"
    exit 1
fi

# Step 5: Restart the service
echo "🔄 Restarting FacultyFinder service..."
sudo systemctl restart facultyfinder.service
sleep 5

# Step 6: Check service status
echo "📊 Checking service status..."
sudo systemctl status facultyfinder.service --no-pager -l | head -15

# Step 7: Test all API endpoints
echo "🧪 Testing API endpoints..."

echo "Testing health endpoint..."
curl -s http://localhost:8008/health
echo ""

echo "Testing stats endpoint..."
curl -s http://localhost:8008/api/v1/stats
echo ""

echo "Testing universities endpoint..."
curl -s "http://localhost:8008/api/v1/universities?per_page=2"
echo ""

echo "Testing countries endpoint..."
curl -s "http://localhost:8008/api/v1/countries"
echo ""

echo "Testing faculties endpoint..."
curl -s "http://localhost:8008/api/v1/faculties?per_page=2"
echo ""

# Step 8: Check service logs
echo "📋 Recent service logs:"
sudo journalctl -u facultyfinder.service --no-pager -n 10

echo "🎉 Database fix completed!"
echo "🌐 Check your website: https://facultyfinder.io" 