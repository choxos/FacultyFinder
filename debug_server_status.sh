#!/bin/bash

echo "🔍 FacultyFinder Server Diagnosis"
echo "================================="

# Check current service status
echo -e "\n📊 SERVICE STATUS:"
echo "FastAPI Service: $(systemctl is-active facultyfinder.service 2>/dev/null || echo 'not found')"
echo "Nginx: $(systemctl is-active nginx)"
echo "PostgreSQL: $(systemctl is-active postgresql)"

# Check what's running on port 8008
echo -e "\n🔌 PORT 8008 STATUS:"
if sudo netstat -tlnp | grep :8008; then
    echo "✅ Something is running on port 8008"
    PROCESS=$(sudo netstat -tlnp | grep :8008 | awk '{print $7}')
    echo "Process: $PROCESS"
else
    echo "❌ Nothing running on port 8008"
fi

# Check recent service logs
echo -e "\n📋 RECENT SERVICE LOGS:"
if systemctl list-units | grep -q facultyfinder.service; then
    echo "Last 10 lines from facultyfinder.service:"
    sudo journalctl -u facultyfinder.service -n 10 --no-pager
else
    echo "❌ facultyfinder.service not found"
fi

# Test API endpoints directly
echo -e "\n🧪 API ENDPOINT TESTS:"
echo "Testing /health endpoint:"
if curl -s http://localhost:8008/health 2>/dev/null; then
    echo "✅ Health endpoint responding"
else
    echo "❌ Health endpoint not responding"
fi

echo -e "\nTesting /api/v1/stats endpoint:"
if curl -s http://localhost:8008/api/v1/stats 2>/dev/null; then
    echo "✅ Stats endpoint responding"
else
    echo "❌ Stats endpoint not responding"
fi

echo -e "\nTesting /api/v1/universities endpoint:"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/api/v1/universities 2>/dev/null)
echo "Response code: $RESPONSE"

# Check if Flask might still be running
echo -e "\n🔍 CHECKING FOR FLASK:"
if ps aux | grep -i gunicorn | grep -v grep; then
    echo "⚠️  Gunicorn (Flask) processes found:"
    ps aux | grep -i gunicorn | grep -v grep
else
    echo "✅ No Gunicorn processes found"
fi

if ps aux | grep -i flask | grep -v grep; then
    echo "⚠️  Flask processes found:"
    ps aux | grep -i flask | grep -v grep
else
    echo "✅ No Flask processes found"
fi

# Check if uvicorn is running
echo -e "\n🔍 CHECKING FOR FASTAPI:"
if ps aux | grep -i uvicorn | grep -v grep; then
    echo "✅ Uvicorn (FastAPI) processes found:"
    ps aux | grep -i uvicorn | grep -v grep
else
    echo "❌ No Uvicorn processes found"
fi

# Check database connection
echo -e "\n🗄️  DATABASE CONNECTION:"
if sudo -u postgres psql -d ff_production -c "SELECT COUNT(*) FROM professors;" 2>/dev/null; then
    echo "✅ Database connection working"
else
    echo "❌ Database connection failed"
fi

# Check current working directory and files
echo -e "\n📁 APPLICATION FILES:"
echo "Current directory: $(pwd)"
echo "App.py exists: $(test -f /var/www/ff/webapp/app.py && echo 'Yes' || echo 'No')"
echo "Main.py exists: $(test -f /var/www/ff/webapp/main.py && echo 'Yes' || echo 'No')"
echo "FastAPI requirements: $(test -f /var/www/ff/requirements_fastapi.txt && echo 'Yes' || echo 'No')"

# Check .env file
echo -e "\n⚙️  ENVIRONMENT:"
if [ -f /var/www/ff/.env ]; then
    echo "✅ .env file exists"
    echo "Database URL present: $(grep -q DATABASE_URL /var/www/ff/.env && echo 'Yes' || echo 'No')"
else
    echo "❌ .env file missing"
fi

# Check nginx configuration
echo -e "\n🌐 NGINX STATUS:"
if nginx -t 2>/dev/null; then
    echo "✅ Nginx configuration valid"
else
    echo "❌ Nginx configuration invalid"
fi

echo -e "\n📍 QUICK FIXES TO TRY:"
echo "1. sudo systemctl restart facultyfinder.service"
echo "2. sudo systemctl status facultyfinder.service"
echo "3. sudo journalctl -u facultyfinder.service -f"
echo "4. curl http://localhost:8008/health"

echo -e "\n✅ Diagnosis complete!" 