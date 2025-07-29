#!/bin/bash

echo "🧪 Testing FacultyFinder APIs (No JQ Required)"
echo "=============================================="

echo "Health endpoint:"
curl -s http://localhost:8008/health
echo -e "\n"

echo "Stats endpoint:"
curl -s http://localhost:8008/api/v1/stats
echo -e "\n"

echo "Countries endpoint:"
curl -s http://localhost:8008/api/v1/countries
echo -e "\n"

echo "Universities endpoint (should now work):"
curl -s "http://localhost:8008/api/v1/universities?per_page=2"
echo -e "\n"

echo "Faculties endpoint (should now work with faculty_id):"
curl -s "http://localhost:8008/api/v1/faculties?per_page=2"
echo -e "\n"

# Simple test to get a faculty_id (using python instead of jq)
echo "🎯 Testing faculty_id functionality..."
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
    echo "Testing professor detail with faculty_id: $SAMPLE_FACULTY_ID"
    curl -s "http://localhost:8008/api/v1/professor/$SAMPLE_FACULTY_ID"
    echo -e "\n"
    
    echo "Testing professor page route:"
    curl -I -s "http://localhost:8008/professor/$SAMPLE_FACULTY_ID" | head -1
else
    echo "⚠️ Could not get sample faculty_id for testing"
fi

echo -e "\n🎉 API testing complete!"
echo "🌐 Check https://facultyfinder.io to see your website!" 