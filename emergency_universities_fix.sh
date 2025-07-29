#!/bin/bash

echo "🚨 Emergency Universities API Fix"
echo "================================"
echo "Fixing 500 Internal Server Error on universities endpoint"

# Check if we're in the right directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

echo "🔧 Step 1: Testing database field names..."

# Test database to see which field names exist
PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -t -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'universities' AND column_name IN ('type', 'university_type', 'language', 'languages', 'established', 'year_established');" > /tmp/uni_fields.txt

echo "📋 Available university fields:"
cat /tmp/uni_fields.txt

if grep -q "university_type" /tmp/uni_fields.txt; then
    echo "✅ Database uses OLD field names - fixing API..."
    
    # Create backup
    cp webapp/main.py webapp/main.py.backup
    
    # Fix the field references in universities API
    sed -i 's/u\.type/u.university_type/g' webapp/main.py
    sed -i 's/u\.language/u.languages/g' webapp/main.py  
    sed -i 's/u\.established/u.year_established/g' webapp/main.py
    
    echo "✅ Fixed field references to use old names"
    
elif grep -q "type" /tmp/uni_fields.txt; then
    echo "✅ Database uses NEW field names - API should work"
else
    echo "❌ Cannot determine field names - manual fix needed"
fi

echo -e "\n🔄 Step 2: Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

echo "⏳ Waiting for service startup..."
sleep 5

echo -e "\n🧪 Step 3: Testing universities API..."

# Test the API
response=$(curl -s -w "%{http_code}" -o /tmp/uni_test.json http://localhost:8008/api/v1/universities?per_page=3)

if [ "$response" = "200" ]; then
    echo "✅ Universities API working: HTTP $response"
    
    # Check response content
    if grep -q '"universities"' /tmp/uni_test.json; then
        echo "✅ Valid universities data returned"
        uni_count=$(grep -o '"id":[0-9]*' /tmp/uni_test.json | wc -l)
        echo "📊 Found $uni_count universities in response"
    else
        echo "⚠️  Response format unexpected"
    fi
else
    echo "❌ Universities API still failing: HTTP $response"
    echo "📋 Error response:"
    head -3 /tmp/uni_test.json 2>/dev/null
    
    echo -e "\n🔧 Checking service logs..."
    sudo journalctl -u facultyfinder.service --lines=5 --no-pager | tail -5
fi

# Test frontend
echo -e "\n🌐 Testing universities page..."
page_response=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8008/universities)

if [ "$page_response" = "200" ]; then
    echo "✅ Universities page loads: HTTP $page_response"
else
    echo "❌ Universities page failed: HTTP $page_response"
fi

# Clean up
rm -f /tmp/uni_fields.txt /tmp/uni_test.json

echo -e "\n🎯 Emergency Fix Summary:"
echo "========================"

if [ "$response" = "200" ]; then
    echo "✅ Universities API fixed and working"
    echo ""
    echo "🌐 Test your universities page:"
    echo "   https://facultyfinder.io/universities"
    echo ""
    echo "📊 API endpoint working:"
    echo "   https://facultyfinder.io/api/v1/universities"
else
    echo "❌ Universities API still needs attention"
    echo ""
    echo "🔧 Manual troubleshooting:"
    echo "   Check logs: sudo journalctl -u facultyfinder.service -f"
    echo "   Test API: curl http://localhost:8008/api/v1/universities?per_page=3"
    echo "   Database: psql -h localhost -U ff_user -d ff_production"
    echo ""
    echo "📋 Possible causes:"
    echo "   - Database field name mismatch"
    echo "   - Missing university/professor data"
    echo "   - Database connection issues"
fi

echo ""
echo "🛠️  Monitor service:"
echo "   sudo systemctl status facultyfinder.service" 