#!/bin/bash

echo "🔐 Deploying Authentication Pages to VPS"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Please run this script from /var/www/ff directory"
    echo "   cd /var/www/ff && ./update_deploy_auth_pages.sh"
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo "✅ Running from correct location"

# Pull latest changes from GitHub
echo -e "\n📥 Pulling authentication pages from GitHub..."
git fetch origin
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pulled latest changes"
else
    echo "❌ Failed to pull changes from GitHub"
    exit 1
fi

# Restart the FastAPI service to pick up new routes
echo -e "\n🔄 Restarting FastAPI service to load new routes..."
sudo systemctl restart facultyfinder.service

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 3

# Check service status
echo -e "\n📊 Service status:"
if sudo systemctl is-active --quiet facultyfinder.service; then
    echo "✅ Service is running"
else
    echo "❌ Service failed to start"
    exit 1
fi

# Test the new authentication routes
echo -e "\n🧪 Testing new authentication routes..."

echo "Testing /login page:"
login_response=$(curl -s -w "%{http_code}" http://localhost:8008/login -o /dev/null)
if [ "$login_response" = "200" ]; then
    echo "✅ Login page OK (HTTP $login_response)"
else
    echo "❌ Login page failed (HTTP $login_response)"
fi

echo -e "\nTesting /register page:"
register_response=$(curl -s -w "%{http_code}" http://localhost:8008/register -o /dev/null)
if [ "$register_response" = "200" ]; then
    echo "✅ Register page OK (HTTP $register_response)"
else
    echo "❌ Register page failed (HTTP $register_response)"
fi

# Final status
echo -e "\n" + "=" * 50
echo "🎉 Authentication Pages Deployment Complete!"
echo "==============================================="

if [ "$login_response" = "200" ] && [ "$register_response" = "200" ]; then
    echo "✅ All authentication pages are working correctly"
    echo "🔗 Test your authentication pages:"
    echo "   - Login: https://facultyfinder.io/login"
    echo "   - Register: https://facultyfinder.io/register"
    echo ""
    echo "🎯 Users can now:"
    echo "   - Click 'Log In' button without getting 404 errors"
    echo "   - Click 'Sign Up' button without getting 404 errors"
    echo "   - Access professional login and registration forms"
else
    echo "⚠️  Some authentication pages are having issues"
    echo "📋 Check logs for more details:"
    echo "   sudo journalctl -u facultyfinder.service -f"
fi

echo ""
echo "📊 Monitor your service:"
echo "   sudo systemctl status facultyfinder.service" 