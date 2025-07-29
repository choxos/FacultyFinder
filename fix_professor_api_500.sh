#!/bin/bash

echo "🔧 Fixing Professor API Issues"
echo "=============================="
echo "1. Remove empty professor record"
echo "2. Fix API 500 errors"
echo "3. Test both integer and string ID formats"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

echo "🧹 Step 1: Removing empty professor record..."
python3 fix_empty_professor.py

echo -e "\n🔍 Step 2: Debugging API 500 errors..."
python3 debug_professor_api_500.py

echo -e "\n🔄 Step 3: Checking service logs for API errors..."
echo "📋 Recent API errors:"
sudo journalctl -u facultyfinder.service --since "5 minutes ago" | grep -i error | tail -5

echo -e "\n🧪 Step 4: Testing API endpoints directly..."

echo "Testing /api/v1/professor/1 (integer ID):"
response1=$(curl -s -w "%{http_code}" -o /tmp/prof_api_1.json http://localhost:8008/api/v1/professor/1 2>/dev/null)

if [ "$response1" = "200" ]; then
    echo "✅ Integer ID API: HTTP $response1"
    if grep -q '"name"' /tmp/prof_api_1.json 2>/dev/null; then
        professor_name=$(grep -o '"name":"[^"]*"' /tmp/prof_api_1.json | cut -d'"' -f4)
        echo "👤 Professor: $professor_name"
    fi
elif [ "$response1" = "500" ]; then
    echo "❌ Integer ID API: HTTP $response1 (Internal Server Error)"
    echo "📋 Error details:"
    head -3 /tmp/prof_api_1.json 2>/dev/null || echo "   No error details available"
    
    echo -e "\n🔧 Checking for specific issues..."
    
    # Check if it's a field mapping issue
    if sudo journalctl -u facultyfinder.service --since "2 minutes ago" | grep -q "column.*does not exist"; then
        echo "⚠️  Database column error detected - field mapping issue"
        echo "🔧 This suggests the API is referencing database columns that don't exist"
        
        # Check database schema
        echo "📋 Checking actual database schema..."
        PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -c "\d professors" | head -20
        
    elif sudo journalctl -u facultyfinder.service --since "2 minutes ago" | grep -q "relation.*does not exist"; then
        echo "⚠️  Database table error detected"
        echo "🔧 Check if universities table exists and is accessible"
    else
        echo "⚠️  Unknown API error - check detailed logs"
    fi
else
    echo "❌ Integer ID API: HTTP $response1 (Unexpected response)"
fi

echo -e "\nTesting /api/v1/professor/CA-ON-002-00001 (string ID):"
response2=$(curl -s -w "%{http_code}" -o /tmp/prof_api_2.json http://localhost:8008/api/v1/professor/CA-ON-002-00001 2>/dev/null)

if [ "$response2" = "200" ]; then
    echo "✅ String ID API: HTTP $response2"
    if grep -q '"name"' /tmp/prof_api_2.json 2>/dev/null; then
        professor_name=$(grep -o '"name":"[^"]*"' /tmp/prof_api_2.json | cut -d'"' -f4)
        echo "👤 Professor: $professor_name"
    fi
elif [ "$response2" = "500" ]; then
    echo "❌ String ID API: HTTP $response2 (Internal Server Error)"
elif [ "$response2" = "404" ]; then
    echo "⚠️  String ID API: HTTP $response2 (Not Found)"
    echo "   This might be expected if CA-ON-002-00001 doesn't exist"
    
    # Try to find a valid string ID
    echo "🔍 Finding a valid string ID to test..."
    valid_id=$(PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -t -c "SELECT professor_id_new FROM professors WHERE professor_id_new IS NOT NULL LIMIT 1;" 2>/dev/null | xargs)
    
    if [ ! -z "$valid_id" ]; then
        echo "Testing with valid ID: $valid_id"
        response3=$(curl -s -w "%{http_code}" -o /tmp/prof_api_3.json "http://localhost:8008/api/v1/professor/$valid_id" 2>/dev/null)
        
        if [ "$response3" = "200" ]; then
            echo "✅ Valid string ID API: HTTP $response3"
            if grep -q '"name"' /tmp/prof_api_3.json 2>/dev/null; then
                professor_name=$(grep -o '"name":"[^"]*"' /tmp/prof_api_3.json | cut -d'"' -f4)
                echo "👤 Professor: $professor_name"
            fi
        else
            echo "❌ Valid string ID API: HTTP $response3"
        fi
    fi
else
    echo "❌ String ID API: HTTP $response2 (Unexpected response)"
fi

# Clean up test files
rm -f /tmp/prof_api_*.json

echo -e "\n🔧 Step 5: Checking for quick fixes..."

if [ "$response1" = "500" ] || [ "$response2" = "500" ]; then
    echo "⚠️  API still returning 500 errors - investigating..."
    
    # Check if it's a simple service restart issue
    echo "🔄 Trying service restart..."
    sudo systemctl restart facultyfinder.service
    sleep 5
    
    # Test again after restart
    echo "🧪 Re-testing after restart..."
    response_retry=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8008/api/v1/professor/1 2>/dev/null)
    
    if [ "$response_retry" = "200" ]; then
        echo "✅ Service restart fixed the issue!"
    else
        echo "❌ Service restart didn't fix the issue (HTTP $response_retry)"
        echo ""
        echo "🔧 Advanced troubleshooting needed:"
        echo "   1. Check detailed logs: sudo journalctl -u facultyfinder.service -f"
        echo "   2. Check database connectivity from API"
        echo "   3. Verify all required database columns exist"
        echo "   4. Check for Python/dependency issues"
    fi
fi

echo -e "\n📊 Step 6: Final verification..."

# Count professors
total_profs=$(PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -t -c "SELECT COUNT(*) FROM professors;" 2>/dev/null | xargs)
new_id_profs=$(PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -t -c "SELECT COUNT(*) FROM professors WHERE professor_id_new IS NOT NULL;" 2>/dev/null | xargs)

echo "📋 Database status:"
echo "   Total professors: $total_profs"
echo "   With new IDs: $new_id_profs"

if [ "$total_profs" = "$new_id_profs" ]; then
    echo "✅ All professors have new IDs"
else
    echo "⚠️  Some professors missing new IDs"
fi

echo -e "\n🎯 Fix Summary:"
echo "==============="

if [ "$response1" = "200" ] || [ "$response_retry" = "200" ]; then
    echo "✅ Professor API working"
    echo ""
    echo "🌐 Test your professor pages:"
    echo "   https://facultyfinder.io/professor/1"
    if [ ! -z "$valid_id" ]; then
        echo "   https://facultyfinder.io/professor/$valid_id"
    fi
else
    echo "❌ Professor API still needs attention"
    echo ""
    echo "🔧 Next troubleshooting steps:"
    echo "   1. Check service logs: sudo journalctl -u facultyfinder.service -f"
    echo "   2. Verify database schema: python3 debug_professor_api_500.py"
    echo "   3. Test database queries manually"
    echo "   4. Check for missing dependencies or config issues"
fi

echo ""
echo "🛠️  Monitor your service:"
echo "   sudo systemctl status facultyfinder.service" 