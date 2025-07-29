#!/bin/bash

echo "🚀 Deploying FastAPI Database Schema Fixes"
echo "==========================================="

# Check if we're in the right directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Please run this script from /var/www/ff directory"
    echo "   cd /var/www/ff && ./deploy_schema_fixes.sh"
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo "✅ Running from correct location"

# Pull latest changes from GitHub
echo -e "\n📥 Pulling latest changes from GitHub..."
git fetch origin
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pulled latest changes"
else
    echo "❌ Failed to pull changes from GitHub"
    exit 1
fi

# Show what changed
echo -e "\n📋 Recent changes:"
git log --oneline -3

# Restart the FastAPI service
echo -e "\n🔄 Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

# Wait a moment for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
echo -e "\n📊 Service status:"
sudo systemctl is-active facultyfinder.service

if sudo systemctl is-active --quiet facultyfinder.service; then
    echo "✅ Service is running"
else
    echo "❌ Service failed to start"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=10 --no-pager
    exit 1
fi

# Test the API endpoints
echo -e "\n🧪 Testing API endpoints..."

echo "Testing /health:"
health_response=$(curl -s http://localhost:8008/health)
echo "$health_response" | head -1
if echo "$health_response" | grep -q "healthy"; then
    echo "✅ Health endpoint OK"
else
    echo "❌ Health endpoint failed"
fi

echo -e "\nTesting /api/v1/stats:"
stats_response=$(curl -s http://localhost:8008/api/v1/stats)
echo "$stats_response" | head -1
if echo "$stats_response" | grep -q "total_professors"; then
    echo "✅ Stats endpoint OK"
else
    echo "❌ Stats endpoint failed"
fi

echo -e "\nTesting /api/v1/universities:"
universities_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/universities -o /dev/null)
if [ "$universities_response" = "200" ]; then
    echo "✅ Universities endpoint OK (HTTP $universities_response)"
else
    echo "❌ Universities endpoint failed (HTTP $universities_response)"
fi

echo -e "\nTesting /api/v1/faculties:"
faculties_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/faculties -o /dev/null)
if [ "$faculties_response" = "200" ]; then
    echo "✅ Faculties endpoint OK (HTTP $faculties_response)"
else
    echo "❌ Faculties endpoint failed (HTTP $faculties_response)"
fi

# Final status
echo -e "\n" + "=" * 60
echo "🎉 Deployment Complete!"
echo "=================================="

if [ "$universities_response" = "200" ] && [ "$faculties_response" = "200" ]; then
    echo "✅ All API endpoints are working correctly"
    echo "🌐 Your website should now be fully functional"
    echo ""
    echo "🔗 Test your website:"
    echo "   - Homepage: https://facultyfinder.io"
    echo "   - Universities: https://facultyfinder.io/universities"
    echo "   - Faculties: https://facultyfinder.io/faculties"
else
    echo "⚠️  Some API endpoints are still having issues"
    echo "📋 Check logs for more details:"
    echo "   sudo journalctl -u facultyfinder.service -f"
fi

echo ""
echo "📊 Monitor your service:"
echo "   sudo systemctl status facultyfinder.service"
echo "   sudo journalctl -u facultyfinder.service -f" 