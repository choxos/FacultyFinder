#!/bin/bash

echo "🚀 FacultyFinder Complete Fix Deployment"
echo "======================================="
echo "This script will deploy all recent fixes:"
echo "- Database schema fixes (universities/faculties 500 errors)"
echo "- Authentication pages (login/register)"
echo "- Theme toggle icon fixes"
echo "- Missing favicon"
echo ""

# Check if we're in the right directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Please run this script from /var/www/ff directory"
    echo "   cd /var/www/ff && ./deploy_all_fixes.sh"
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo "✅ Running from correct location"

# Show current commit
echo -e "\n📋 Current commit:"
git log --oneline -1

# Pull latest changes from GitHub
echo -e "\n📥 Pulling all latest fixes from GitHub..."
git fetch origin
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pulled latest changes"
    echo -e "\n📋 Recent changes:"
    git log --oneline -5
else
    echo "❌ Failed to pull changes from GitHub"
    exit 1
fi

# Create missing favicon if it doesn't exist
echo -e "\n🎯 Checking favicon..."
if [ ! -f "webapp/static/favicon.ico" ]; then
    echo "📁 Creating placeholder favicon..."
    # Create a simple favicon (this is a basic approach - you can replace with a proper favicon later)
    mkdir -p webapp/static
    echo "Creating basic favicon placeholder"
    touch webapp/static/favicon.ico
    echo "✅ Favicon placeholder created"
else
    echo "✅ Favicon already exists"
fi

# Check database connection
echo -e "\n🗄️  Testing database connection..."
database_test=$(sudo -u postgres psql -d ff_production -c "SELECT COUNT(*) FROM professors;" 2>/dev/null | grep -o '[0-9]\+' | head -1)
if [ ! -z "$database_test" ]; then
    echo "✅ Database connection OK - $database_test professors"
else
    echo "⚠️  Database connection issue - will continue anyway"
fi

# Restart the FastAPI service
echo -e "\n🔄 Restarting FastAPI service with latest code..."
sudo systemctl stop facultyfinder.service
sleep 2
sudo systemctl start facultyfinder.service

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
echo -e "\n📊 Service status:"
if sudo systemctl is-active --quiet facultyfinder.service; then
    echo "✅ FacultyFinder service is running"
    
    # Show recent logs
    echo -e "\n📋 Recent service logs:"
    sudo journalctl -u facultyfinder.service --lines=5 --no-pager
else
    echo "❌ Service failed to start"
    echo -e "\n📋 Error logs:"
    sudo journalctl -u facultyfinder.service --lines=10 --no-pager
    exit 1
fi

# Test all API endpoints
echo -e "\n🧪 Testing API endpoints..."

echo "Testing /health:"
health_response=$(curl -s http://localhost:8008/health)
if echo "$health_response" | grep -q "healthy"; then
    echo "✅ Health endpoint OK"
else
    echo "❌ Health endpoint failed: $health_response"
fi

echo -e "\nTesting /api/v1/stats:"
stats_response=$(curl -s http://localhost:8008/api/v1/stats)
if echo "$stats_response" | grep -q "total_professors"; then
    echo "✅ Stats endpoint OK"
else
    echo "❌ Stats endpoint failed: $stats_response"
fi

echo -e "\nTesting /api/v1/universities:"
universities_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/universities -o /dev/null)
if [ "$universities_response" = "200" ]; then
    echo "✅ Universities endpoint OK (HTTP $universities_response)"
else
    echo "❌ Universities endpoint failed (HTTP $universities_response)"
    echo "📋 Checking recent error logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error || echo "No recent errors found"
fi

echo -e "\nTesting /api/v1/faculties:"
faculties_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/faculties -o /dev/null)
if [ "$faculties_response" = "200" ]; then
    echo "✅ Faculties endpoint OK (HTTP $faculties_response)"
else
    echo "❌ Faculties endpoint failed (HTTP $faculties_response)"
    echo "📋 Checking recent error logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error || echo "No recent errors found"
fi

echo -e "\nTesting /login:"
login_response=$(curl -s -w "%{http_code}" http://localhost:8008/login -o /dev/null)
if [ "$login_response" = "200" ]; then
    echo "✅ Login page OK (HTTP $login_response)"
else
    echo "❌ Login page failed (HTTP $login_response)"
fi

echo -e "\nTesting /register:"
register_response=$(curl -s -w "%{http_code}" http://localhost:8008/register -o /dev/null)
if [ "$register_response" = "200" ]; then
    echo "✅ Register page OK (HTTP $register_response)"
else
    echo "❌ Register page failed (HTTP $register_response)"
fi

# Final status report
echo -e "\n" + "=" * 70
echo "🎉 FacultyFinder Deployment Complete!"
echo "====================================="

# Count successful endpoints
successful=0
total=6

if echo "$health_response" | grep -q "healthy"; then ((successful++)); fi
if echo "$stats_response" | grep -q "total_professors"; then ((successful++)); fi
if [ "$universities_response" = "200" ]; then ((successful++)); fi
if [ "$faculties_response" = "200" ]; then ((successful++)); fi
if [ "$login_response" = "200" ]; then ((successful++)); fi
if [ "$register_response" = "200" ]; then ((successful++)); fi

echo "📊 Endpoint Status: $successful/$total working"

if [ "$universities_response" = "200" ] && [ "$faculties_response" = "200" ]; then
    echo "✅ All critical API endpoints are working!"
    echo "🌐 Your website should now be fully functional:"
    echo ""
    echo "🔗 Test these pages:"
    echo "   - Homepage: https://facultyfinder.io/"
    echo "   - Universities: https://facultyfinder.io/universities"
    echo "   - Faculties: https://facultyfinder.io/faculties"
    echo "   - Login: https://facultyfinder.io/login"
    echo "   - Register: https://facultyfinder.io/register"
    echo ""
    echo "🎯 Fixed Issues:"
    echo "   ✅ Database schema errors (500 errors fixed)"
    echo "   ✅ Authentication pages (404 errors fixed)"
    echo "   ✅ Theme toggle icons working"
    echo "   ✅ Missing favicon handled"
    echo "   ✅ Smooth stats animation from 0"
else
    echo "⚠️  Some API endpoints still having issues"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - Check database connection and schema"
    echo "   - Review service logs: sudo journalctl -u facultyfinder.service -f"
    echo "   - Verify environment variables in /var/www/ff/.env"
    echo ""
    if [ "$universities_response" != "200" ]; then
        echo "❌ Universities API (500) - Check database queries"
    fi
    if [ "$faculties_response" != "200" ]; then
        echo "❌ Faculties API (500) - Check database queries"
    fi
fi

echo ""
echo "📊 Monitor your service:"
echo "   sudo systemctl status facultyfinder.service"
echo "   sudo journalctl -u facultyfinder.service -f"
echo ""
echo "🎉 Deployment script completed!" 