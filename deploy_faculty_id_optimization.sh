#!/bin/bash

# Faculty ID System Optimization Deployment Script
# This script optimizes the faculty_id system for better performance and efficiency

set -e  # Exit on any error

echo "🚀 Faculty ID System Optimization Deployment"
echo "=============================================="

# Step 1: Pull latest changes from GitHub
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Step 2: Install required dependencies if needed
echo "📦 Checking dependencies..."
pip install --quiet asyncpg

# Step 3: Test Python syntax for all updated files
echo "🧪 Testing Python syntax..."
python3 -m py_compile optimize_faculty_id_system.py
python3 -m py_compile webapp/main.py
echo "✅ Python syntax is valid"

# Step 4: Run the faculty ID optimization
echo "🔧 Running faculty ID system optimization..."
python3 optimize_faculty_id_system.py

# Step 5: Restart the FastAPI service
echo "🔄 Restarting FacultyFinder service..."
sudo systemctl restart facultyfinder.service

# Step 6: Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Step 7: Check service status
echo "📊 Checking service status..."
sudo systemctl status facultyfinder.service --no-pager -n 5

# Step 8: Test the optimized APIs
echo "🧪 Testing optimized Faculty ID APIs..."

echo ""
echo "Testing health endpoint..."
health_response=$(curl -s "http://localhost:8008/health" || echo "Failed")
echo "Health: $health_response"

echo ""
echo "Testing faculties endpoint (should include professor_id and computed faculty_id)..."
faculties_response=$(curl -s "http://localhost:8008/api/v1/faculties?per_page=2" || echo "Failed")
echo "Faculties: $faculties_response"

echo ""
echo "Testing individual professor by faculty_id..."
# Extract a faculty_id from the faculties response using Python
faculty_id=$(echo "$faculties_response" | python3 -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    if 'faculties' in data and len(data['faculties']) > 0:
        print(data['faculties'][0]['faculty_id'])
    else:
        print('CA-ON-002-00001')  # fallback
except:
    print('CA-ON-002-00001')  # fallback
")

echo "Testing professor endpoint with faculty_id: $faculty_id"
professor_response=$(curl -s "http://localhost:8008/api/v1/professor/$faculty_id" || echo "Failed")
echo "Professor: $professor_response"

echo ""
echo "Testing professor endpoint with direct professor_id: 1"
professor_id_response=$(curl -s "http://localhost:8008/api/v1/professor/1" || echo "Failed")
echo "Professor by ID: $professor_id_response"

# Step 9: Performance comparison (optional)
echo ""
echo "🚀 Performance Test (5 requests each)..."

echo "Testing faculties endpoint performance..."
time_start=$(date +%s%N)
for i in {1..5}; do
    curl -s "http://localhost:8008/api/v1/faculties?per_page=10" > /dev/null
done
time_end=$(date +%s%N)
faculties_time=$(( (time_end - time_start) / 1000000 ))
echo "Faculties API: 5 requests took ${faculties_time}ms (avg: $((faculties_time/5))ms per request)"

echo "Testing professor endpoint performance..."
time_start=$(date +%s%N)
for i in {1..5}; do
    curl -s "http://localhost:8008/api/v1/professor/$faculty_id" > /dev/null
done
time_end=$(date +%s%N)
professor_time=$(( (time_end - time_start) / 1000000 ))
echo "Professor API: 5 requests took ${professor_time}ms (avg: $((professor_time/5))ms per request)"

# Step 10: Summary
echo ""
echo "🎉 Faculty ID Optimization Deployment Complete!"
echo "================================================="
echo "✅ Database schema optimized (faculty_id column removed)"
echo "✅ Added efficient professor_id integer column"
echo "✅ Added unique constraint per university"
echo "✅ Created performance index"
echo "✅ Updated FastAPI endpoints"
echo "✅ Faculty ID now computed programmatically"
echo ""
echo "📊 API Performance:"
echo "   - Faculties API average: $((faculties_time/5))ms per request"
echo "   - Professor API average: $((professor_time/5))ms per request"
echo ""
echo "🔗 Test URLs:"
echo "   - Faculties: https://facultyfinder.io/api/v1/faculties"
echo "   - Professor: https://facultyfinder.io/api/v1/professor/$faculty_id"
echo "   - Professor by ID: https://facultyfinder.io/api/v1/professor/1"
echo ""
echo "🌐 Your website is now running with optimized Faculty ID system!" 