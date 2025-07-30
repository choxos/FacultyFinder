#!/bin/bash

echo "🔧 Fixing University Schema for Google Maps Integration"
echo "====================================================="

# Load database credentials
if [ -f "/var/www/ff/.env" ]; then
    export $(cat /var/www/ff/.env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

echo "📊 Adding missing address columns to universities table..."

# Run the SQL fix
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -f fix_university_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ University schema updated successfully!"
else
    echo "❌ Schema update failed"
    exit 1
fi

echo ""
echo "🔄 Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

echo ""
echo "⏳ Waiting for service to start..."
sleep 3

echo ""
echo "🧪 Testing universities API..."
RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:8008/api/v1/universities?per_page=1")
HTTP_CODE="${RESPONSE: -3}"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Universities API is now working!"
    BODY="${RESPONSE%???}"
    echo "📊 Sample response: ${BODY:0:200}..."
else
    echo "❌ Universities API still returning HTTP $HTTP_CODE"
    echo "📋 Response: $RESPONSE"
    
    echo ""
    echo "🔍 Recent service logs:"
    sudo journalctl -u facultyfinder.service -n 5 --no-pager
fi

echo ""
echo "🎉 University Schema Fix Complete!"
echo "=================================="

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Your universities page should now be working!"
    echo "🌐 Test at: https://facultyfinder.io/universities"
else
    echo "⚠️ If issues persist, check the service logs:"
    echo "   sudo journalctl -u facultyfinder.service -n 20"
fi 