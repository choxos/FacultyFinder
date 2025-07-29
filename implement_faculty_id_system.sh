#!/bin/bash

echo "🚀 Implementing Faculty ID System for FacultyFinder"
echo "=================================================="

# Step 1: Install required Python packages
echo "📦 Installing required packages..."
pip install psycopg2-binary pandas python-dotenv

# Step 2: Add faculty_id to CSV and create database schema
echo "🗄️ Setting up faculty_id system and database..."
python3 add_faculty_id_system.py

if [ $? -ne 0 ]; then
    echo "❌ Faculty ID system setup failed"
    exit 1
fi

# Step 3: Update FastAPI endpoints for faculty_id
echo "🔧 Updating FastAPI endpoints..."
python3 update_fastapi_faculty_id.py

if [ $? -ne 0 ]; then
    echo "❌ FastAPI update failed"
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

# Step 7: Test API endpoints with faculty_id
echo "🧪 Testing API endpoints with faculty_id..."

echo "Testing health endpoint..."
curl -s http://localhost:8008/health
echo ""

echo "Testing stats endpoint..."
curl -s http://localhost:8008/api/v1/stats
echo ""

echo "Testing universities endpoint..."
curl -s "http://localhost:8008/api/v1/universities?per_page=2"
echo ""

echo "Testing faculties endpoint (should include faculty_id)..."
curl -s "http://localhost:8008/api/v1/faculties?per_page=2"
echo ""

# Get a sample faculty_id for testing
echo "Getting sample faculty_id for testing professor endpoint..."
SAMPLE_FACULTY_ID=$(curl -s "http://localhost:8008/api/v1/faculties?per_page=1" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'data' in data and len(data['data']) > 0:
        print(data['data'][0]['faculty_id'])
    else:
        print('')
except:
    print('')
")

if [ ! -z "$SAMPLE_FACULTY_ID" ]; then
    echo "Testing professor detail endpoint with faculty_id: $SAMPLE_FACULTY_ID"
    curl -s "http://localhost:8008/api/v1/professor/$SAMPLE_FACULTY_ID"
    echo ""
    
    echo "Testing professor page route with faculty_id: $SAMPLE_FACULTY_ID"
    curl -I -s "http://localhost:8008/professor/$SAMPLE_FACULTY_ID" | head -1
else
    echo "⚠️ Could not get sample faculty_id for testing"
fi

# Step 8: Show sample faculty IDs
echo "📋 Sample faculty IDs in database:"
sudo -u postgres psql -d ff_production -c "SELECT faculty_id, name FROM professors LIMIT 5;" 2>/dev/null || echo "Could not query database directly"

# Step 9: Check service logs
echo "📋 Recent service logs:"
sudo journalctl -u facultyfinder.service --no-pager -n 10

echo ""
echo "🎉 Faculty ID system implementation completed!"
echo ""
echo "📊 Summary:"
echo "   - Faculty IDs added to CSV file"  
echo "   - PostgreSQL schema updated with faculty_id column"
echo "   - FastAPI endpoints updated to use faculty_id"
echo "   - Professor pages now accessible via faculty_id"
echo ""
echo "🌐 URLs now available:"
echo "   - API: /api/v1/professor/{faculty_id}"
echo "   - Page: /professor/{faculty_id}"
echo "   - Example: /professor/CA-ON-002-F-0001"
echo ""
echo "🌐 Check your website: https://facultyfinder.io" 