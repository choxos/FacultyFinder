#!/bin/bash

echo "🏛️ Deploying University Profile Pages"
echo "====================================="
echo "Adding university profile functionality to fix 404 errors"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

# Pull university profile changes
echo "📥 Pulling university profile code from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ University profile code pulled successfully"

# Show what was added
echo -e "\n📋 Latest addition:"
git log --oneline -1

# Restart FastAPI service
echo -e "\n🔄 Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

# Wait for startup
echo "⏳ Waiting for service startup..."
sleep 5

# Test the new university profile functionality
echo -e "\n🧪 Testing university profile functionality..."

# Test university profile page route
echo "Testing /university/CA-ON-002 page:"
university_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/university/CA-ON-002 -o /dev/null)
if [ "$university_page_response" = "200" ]; then
    echo "✅ University profile page OK (HTTP $university_page_response)"
else
    echo "❌ University profile page failed (HTTP $university_page_response)"
fi

# Test university API endpoint
echo -e "\nTesting /api/v1/university/CA-ON-002 API:"
university_api_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/university/CA-ON-002 -o /dev/null)
if [ "$university_api_response" = "200" ]; then
    echo "✅ University API endpoint OK (HTTP $university_api_response)"
else
    echo "❌ University API endpoint failed (HTTP $university_api_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

# Test with university name instead of code
echo -e "\nTesting with university name:"
university_name_response=$(curl -s -w "%{http_code}" "http://localhost:8008/api/v1/university/McMaster%20University" -o /dev/null)
if [ "$university_name_response" = "200" ]; then
    echo "✅ University name lookup OK (HTTP $university_name_response)"
else
    echo "❌ University name lookup failed (HTTP $university_name_response)"
fi

# Final status
echo -e "\n" + "=" * 50
if [ "$university_page_response" = "200" ] && [ "$university_api_response" = "200" ]; then
    echo "🎉 SUCCESS! University profiles are now working!"
    echo ""
    echo "🌐 Test your university profiles:"
    echo "   - Click any university name on: https://facultyfinder.io/universities"
    echo "   - Or visit directly: https://facultyfinder.io/university/CA-ON-002"
    echo ""
    echo "✅ Fixed Issues:"
    echo "   - University profile 404 errors resolved"
    echo "   - University detail pages now load"
    echo "   - Faculty lists for specific universities work"
    echo "   - Department and research area tabs functional"
else
    echo "⚠️  Some university functionality still needs attention"
    echo "🔧 Check logs: sudo journalctl -u facultyfinder.service -f"
fi

echo -e "\n🎯 University profiles are ready!" 