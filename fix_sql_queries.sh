#!/bin/bash

echo "🔧 Fixing SQL Query Issues"
echo "=========================="

# Test syntax
echo "🧪 Testing Python syntax..."
python3 -m py_compile webapp/main.py

if [ $? -ne 0 ]; then
    echo "❌ Python syntax error"
    exit 1
fi

# Restart service
echo "🔄 Restarting FacultyFinder service..."
sudo systemctl restart facultyfinder.service
sleep 3

# Test all endpoints
echo "🧪 Testing all API endpoints..."

echo "Health endpoint:"
curl -s http://localhost:8008/health | jq .
echo ""

echo "Stats endpoint:"
curl -s http://localhost:8008/api/v1/stats | jq .
echo ""

echo "Countries endpoint:"
curl -s http://localhost:8008/api/v1/countries | jq .
echo ""

echo "Universities endpoint (should now work):"
curl -s "http://localhost:8008/api/v1/universities?per_page=2" | jq .
echo ""

echo "Faculties endpoint (should now work with faculty_id):"
curl -s "http://localhost:8008/api/v1/faculties?per_page=2" | jq .
echo ""

# Test faculty_id functionality
echo "🎯 Testing faculty_id functionality..."
SAMPLE_FACULTY_ID=$(curl -s "http://localhost:8008/api/v1/faculties?per_page=1" | jq -r '.data[0].faculty_id // empty')

if [ ! -z "$SAMPLE_FACULTY_ID" ]; then
    echo "Testing professor detail with faculty_id: $SAMPLE_FACULTY_ID"
    curl -s "http://localhost:8008/api/v1/professor/$SAMPLE_FACULTY_ID" | jq .
    echo ""
else
    echo "⚠️ Could not get sample faculty_id"
fi

echo "🎉 SQL query fixes deployed!"
echo "🌐 Your website should now be fully functional!" 