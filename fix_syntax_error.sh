#!/bin/bash

echo "🚨 Syntax Error Fix"
echo "====================="

echo "✅ Fixed: Replaced \${} with {} in query LIMIT/OFFSET"
echo "✅ Fixed: Column reference u.year_established"

echo ""
echo "🔧 Step 1: Checking Python syntax..."
python3 -m py_compile webapp/main.py
if [ $? -eq 0 ]; then
    echo "✅ Python syntax is now valid!"
else
    echo "❌ Python syntax still has errors"
    exit 1
fi

echo ""
echo "🔄 Step 2: Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service
sleep 3

echo ""
echo "📊 Step 3: Checking service status..."
if sudo systemctl is-active --quiet facultyfinder.service; then
    echo "✅ Service is running!"
else
    echo "❌ Service failed to start"
    echo "📋 Service status:"
    sudo systemctl status facultyfinder.service --no-pager -l
    exit 1
fi

echo ""
echo "🧪 Step 4: Testing APIs..."

# Test universities API
echo "Testing universities API..."
UNIVERSITIES_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/api/v1/universities?per_page=3)
if [ "$UNIVERSITIES_RESPONSE" = "200" ]; then
    echo "✅ Universities API: HTTP 200"
    # Get actual data
    curl -s http://localhost:8008/api/v1/universities?per_page=2 | jq '.universities[0].name' 2>/dev/null || echo "   (Data received but jq not available)"
else
    echo "❌ Universities API: HTTP $UNIVERSITIES_RESPONSE"
fi

# Test professor API
echo "Testing professor API..."
PROFESSOR_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/api/v1/professor/10)
if [ "$PROFESSOR_RESPONSE" = "200" ]; then
    echo "✅ Professor API: HTTP 200"
    # Get actual data
    curl -s http://localhost:8008/api/v1/professor/10 | jq '.name' 2>/dev/null || echo "   (Data received but jq not available)"
else
    echo "❌ Professor API: HTTP $PROFESSOR_RESPONSE"
fi

echo ""
echo "🎯 Fix Summary"
echo "================"

if [ "$UNIVERSITIES_RESPONSE" = "200" ] && [ "$PROFESSOR_RESPONSE" = "200" ]; then
    echo "🎉 SUCCESS! Both APIs are working!"
    echo ""
    echo "🌐 Your pages should now work:"
    echo "   • Universities: https://facultyfinder.io/universities"
    echo "   • Professor: https://facultyfinder.io/professor/10"
    echo "   • Professor (new ID): https://facultyfinder.io/professor/CA-ON-002-00001"
else
    echo "⚠️  Some APIs still need attention"
    echo ""
    echo "🔧 Debug:"
    echo "   • Check logs: sudo journalctl -u facultyfinder.service -f"
    echo "   • Service status: sudo systemctl status facultyfinder.service"
fi 