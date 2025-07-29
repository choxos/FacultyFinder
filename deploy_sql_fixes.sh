#!/bin/bash

echo "🔧 Deploying Critical SQL Fixes"
echo "==============================="
echo "Fixing 500 errors on universities and faculties endpoints"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

# Pull SQL fixes
echo "📥 Pulling SQL fixes from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ SQL fixes pulled successfully"

# Show what changed
echo -e "\n📋 Latest fix:"
git log --oneline -1

# Restart FastAPI service
echo -e "\n🔄 Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

# Wait for startup
echo "⏳ Waiting for service startup..."
sleep 5

# Test the fixed endpoints
echo -e "\n🧪 Testing fixed API endpoints..."

echo "Testing /api/v1/universities:"
universities_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/universities -o /dev/null)
if [ "$universities_response" = "200" ]; then
    echo "✅ Universities endpoint FIXED! (HTTP $universities_response)"
else
    echo "❌ Universities endpoint still failing (HTTP $universities_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

echo -e "\nTesting /api/v1/faculties:"
faculties_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/faculties -o /dev/null)
if [ "$faculties_response" = "200" ]; then
    echo "✅ Faculties endpoint FIXED! (HTTP $faculties_response)"
else
    echo "❌ Faculties endpoint still failing (HTTP $faculties_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

# Final status
echo -e "\n" + "=" * 50
if [ "$universities_response" = "200" ] && [ "$faculties_response" = "200" ]; then
    echo "🎉 SUCCESS! Both API endpoints are now working!"
    echo "🌐 Your website should be fully functional:"
    echo "   - https://facultyfinder.io/universities"
    echo "   - https://facultyfinder.io/faculties"
    echo ""
    echo "✅ Fixed Issues:"
    echo "   - SQL syntax error in GROUP BY clause"
    echo "   - Column name error (p.primary_position → p.position)"
    echo "   - 500 Internal Server Errors resolved"
else
    echo "⚠️  Some endpoints still need attention"
    echo "🔧 Check logs: sudo journalctl -u facultyfinder.service -f"
fi

echo -e "\n🎯 Test your website now!" 