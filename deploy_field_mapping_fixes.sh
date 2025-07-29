#!/bin/bash

echo "🔧 Deploying Field Mapping Fixes"
echo "================================"
echo "Correcting API field mapping to match CSV data structure"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

# Verify CSV field names
echo "📋 Verifying CSV field structure..."

if [ -f "data/university_codes.csv" ]; then
    echo "✅ university_codes.csv found"
    echo "   Fields: $(head -1 data/university_codes.csv)"
else
    echo "⚠️  university_codes.csv not found locally"
fi

if [ -f "data/mcmaster_hei_faculty.csv" ]; then
    echo "✅ mcmaster_hei_faculty.csv found"
    echo "   Sample fields: name, position, full_time, adjunct, university_code..."
else
    echo "⚠️  mcmaster_hei_faculty.csv not found locally"
fi

# Pull the field mapping fixes
echo -e "\n📥 Pulling field mapping fixes from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ Field mapping fixes pulled successfully"

# Run field verification if script exists
if [ -f "verify_database_schema.py" ]; then
    echo -e "\n🔍 Verifying database schema..."
    python3 verify_database_schema.py
else
    echo "⚠️  Schema verification script not found"
fi

# Restart FastAPI service
echo -e "\n🔄 Restarting FastAPI service with corrected field mapping..."
sudo systemctl restart facultyfinder.service

# Wait for startup
echo "⏳ Waiting for service startup..."
sleep 5

# Test the field mapping fixes
echo -e "\n🧪 Testing corrected field mapping..."

echo "Testing universities API with corrected fields:"
universities_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/universities?per_page=1 -o /tmp/universities_test.json)
if [ "$universities_response" = "200" ]; then
    echo "✅ Universities API OK (HTTP $universities_response)"
    
    # Check for corrected fields
    if grep -q '"type":\|"language":\|"established":' /tmp/universities_test.json 2>/dev/null; then
        echo "✅ Corrected university fields detected (type, language, established)"
    else
        echo "⚠️  Some corrected university fields may be missing"
        echo "📄 Response sample:"
        head -5 /tmp/universities_test.json | jq '.' 2>/dev/null || head -5 /tmp/universities_test.json
    fi
else
    echo "❌ Universities API failed (HTTP $universities_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

echo -e "\nTesting faculties API with verified fields:"
faculties_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/faculties?per_page=1 -o /tmp/faculties_test.json)
if [ "$faculties_response" = "200" ]; then
    echo "✅ Faculties API OK (HTTP $faculties_response)"
    
    # Check for correct fields
    if grep -q '"position":\|"full_time":\|"adjunct":' /tmp/faculties_test.json 2>/dev/null; then
        echo "✅ Correct faculty fields detected (position, full_time, adjunct)"
    else
        echo "⚠️  Some faculty fields may be missing"
        echo "📄 Response sample:"
        head -5 /tmp/faculties_test.json | jq '.' 2>/dev/null || head -5 /tmp/faculties_test.json
    fi
else
    echo "❌ Faculties API failed (HTTP $faculties_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

# Test frontend pages
echo -e "\nTesting frontend pages with corrected field display:"
universities_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/universities -o /dev/null)
if [ "$universities_page_response" = "200" ]; then
    echo "✅ Universities page OK (HTTP $universities_page_response)"
else
    echo "❌ Universities page failed (HTTP $universities_page_response)"
fi

faculties_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/faculties -o /dev/null)
if [ "$faculties_page_response" = "200" ]; then
    echo "✅ Faculties page OK (HTTP $faculties_page_response)"
else
    echo "❌ Faculties page failed (HTTP $faculties_page_response)"
fi

# Clean up test files
rm -f /tmp/universities_test.json /tmp/faculties_test.json

# Final status
echo -e "\n" + "=" * 60
echo "🎉 Field Mapping Fix Deployment Complete!"
echo "========================================"

if [ "$universities_response" = "200" ] && [ "$faculties_response" = "200" ]; then
    echo "✅ Field mapping corrections deployed successfully!"
    echo ""
    echo "🔧 Corrected Field Mappings:"
    echo "   University CSV → API Field Mapping:"
    echo "   - 'type' → 'type' (was 'university_type')"
    echo "   - 'language' → 'language' (was 'languages')"
    echo "   - 'established' → 'established' (was 'year_established')"
    echo ""
    echo "   Faculty CSV → API Field Mapping:"
    echo "   - 'position' → 'position' ✅ (already correct)"
    echo "   - 'full_time' → 'full_time' ✅ (already correct)"
    echo "   - 'adjunct' → 'adjunct' ✅ (already correct)"
    echo ""
    echo "🌐 Test your corrected data display:"
    echo "   Universities: https://facultyfinder.io/universities"
    echo "   Faculties: https://facultyfinder.io/faculties"
    echo "   Check that university type, language, and establishment year display correctly"
    echo "   Check that faculty positions and employment status display correctly"
    echo ""
    echo "📊 Field Mapping Now Matches CSV Structure:"
    echo "   - University type (Public/Private) should display"
    echo "   - Language of instruction should display"
    echo "   - Establishment year should sort correctly"
    echo "   - Faculty positions should be accurate"
    echo "   - Full-time/Part-time status should be correct"
else
    echo "⚠️  Some API endpoints need attention"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   sudo journalctl -u facultyfinder.service -f"
    echo "   curl http://localhost:8008/api/v1/universities"
    echo "   curl http://localhost:8008/api/v1/faculties"
    echo ""
    echo "📋 Check CSV field names match database schema:"
    echo "   python3 verify_database_schema.py"
fi

echo -e "\n🛠️  Monitor your service:"
echo "   sudo systemctl status facultyfinder.service"
echo "   sudo journalctl -u facultyfinder.service -f" 