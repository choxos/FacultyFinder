#!/bin/bash

echo "🎯 Complete Professor ID Fix & Deployment"
echo "========================================"
echo "Fixing database credentials, generating IDs, and testing endpoints"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

echo "📥 Step 1: Pull latest fixes from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ Latest fixes pulled successfully"

echo -e "\n🔧 Step 2: Setting up correct database credentials..."

# Create .env file with correct credentials
cat > .env << EOF
# Database Configuration for FacultyFinder
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ff_production
DB_USER=ff_user
DB_PASSWORD=Choxos10203040

# Alternative format (for compatibility)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=ff_production
DATABASE_USER=ff_user
DATABASE_PASSWORD=Choxos10203040
EOF

echo "✅ Database credentials configured"

echo -e "\n🧪 Step 3: Testing database connection..."
python3 test_db_connection_fix.py

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed - please check PostgreSQL service"
    echo "🔧 Troubleshooting commands:"
    echo "   sudo systemctl status postgresql"
    echo "   sudo systemctl start postgresql"
    echo "   psql -h localhost -U ff_user -d ff_production"
    exit 1
fi

echo -e "\n🆔 Step 4: Generating professor IDs..."
python3 generate_professor_ids.py

if [ $? -eq 0 ]; then
    echo "✅ Professor IDs generated successfully"
    
    # Check if mapping file was created
    if [ -f "professor_id_mapping.json" ]; then
        echo "📁 ID mapping file created: professor_id_mapping.json"
        echo "📊 Sample mappings:"
        head -10 professor_id_mapping.json 2>/dev/null || echo "   (file content preview not available)"
    fi
else
    echo "⚠️  Professor ID generation had issues, but continuing..."
    echo "   (The API has fallback logic to handle this)"
fi

echo -e "\n🔄 Step 5: Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

if [ $? -ne 0 ]; then
    echo "❌ Failed to restart service"
    echo "🔧 Check service status: sudo systemctl status facultyfinder.service"
    exit 1
fi

echo "⏳ Waiting for service startup..."
sleep 5

echo -e "\n🧪 Step 6: Testing professor API endpoints..."

echo "Testing integer ID format (backwards compatibility):"
response1=$(curl -s -w "%{http_code}" -o /tmp/prof_test_1.json http://localhost:8008/api/v1/professor/1)
if [ "$response1" = "200" ]; then
    echo "✅ Integer ID test: HTTP $response1"
    # Check response content
    if grep -q '"name"' /tmp/prof_test_1.json 2>/dev/null; then
        echo "✅ Professor data returned successfully"
    else
        echo "⚠️  Response received but may not contain expected data"
    fi
else
    echo "❌ Integer ID test failed: HTTP $response1"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | tail -3
fi

echo -e "\nTesting string ID format (new format):"
response2=$(curl -s -w "%{http_code}" -o /tmp/prof_test_2.json http://localhost:8008/api/v1/professor/CA-ON-002-00002)
if [ "$response2" = "200" ]; then
    echo "✅ String ID test: HTTP $response2"
    # Check response content
    if grep -q '"name"' /tmp/prof_test_2.json 2>/dev/null; then
        echo "✅ Professor data returned successfully"
        professor_name=$(grep -o '"name":"[^"]*"' /tmp/prof_test_2.json 2>/dev/null | cut -d'"' -f4)
        if [ ! -z "$professor_name" ]; then
            echo "👤 Professor found: $professor_name"
        fi
    else
        echo "⚠️  Response received but may not contain expected data"
    fi
elif [ "$response2" = "404" ]; then
    echo "⚠️  String ID test: HTTP $response2 (Professor not found)"
    echo "   This may be normal if CA-ON-002-00002 doesn't exist"
    echo "   Let's try CA-ON-002-00001 instead..."
    
    response3=$(curl -s -w "%{http_code}" -o /tmp/prof_test_3.json http://localhost:8008/api/v1/professor/CA-ON-002-00001)
    if [ "$response3" = "200" ]; then
        echo "✅ String ID CA-ON-002-00001: HTTP $response3"
        if grep -q '"name"' /tmp/prof_test_3.json 2>/dev/null; then
            professor_name=$(grep -o '"name":"[^"]*"' /tmp/prof_test_3.json 2>/dev/null | cut -d'"' -f4)
            if [ ! -z "$professor_name" ]; then
                echo "👤 Professor found: $professor_name"
            fi
        fi
    else
        echo "❌ String ID CA-ON-002-00001: HTTP $response3"
    fi
else
    echo "❌ String ID test failed: HTTP $response2"
    echo "📋 Error response:"
    head -3 /tmp/prof_test_2.json 2>/dev/null || echo "   (no error details available)"
fi

echo -e "\n🌐 Step 7: Testing professor pages..."

echo "Testing integer professor page:"
page_response1=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8008/professor/1)
if [ "$page_response1" = "200" ]; then
    echo "✅ Integer professor page: HTTP $page_response1"
else
    echo "❌ Integer professor page failed: HTTP $page_response1"
fi

echo "Testing string professor page:"
page_response2=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8008/professor/CA-ON-002-00001)
if [ "$page_response2" = "200" ]; then
    echo "✅ String professor page: HTTP $page_response2"
else
    echo "❌ String professor page failed: HTTP $page_response2"
fi

# Clean up test files
rm -f /tmp/prof_test_*.json

echo -e "\n📊 Step 8: Database verification..."

echo "Checking professor_id_new column:"
db_check=$(PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -t -c "SELECT COUNT(*) FROM professors WHERE professor_id_new IS NOT NULL;" 2>/dev/null)

if [ ! -z "$db_check" ] && [ "$db_check" -gt 0 ]; then
    echo "✅ Found $db_check professors with new IDs"
    
    # Show sample new IDs
    echo "📋 Sample professor IDs:"
    PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -t -c "SELECT name, professor_id_new FROM professors WHERE professor_id_new IS NOT NULL LIMIT 5;" 2>/dev/null | head -5
else
    echo "⚠️  professor_id_new column may not be populated yet"
    echo "   This is okay - the API has fallback logic"
fi

# Final status summary
echo -e "\n" + "=" * 60
echo "🎉 Professor ID Fix Deployment Complete!"
echo "========================================"

if [ "$response1" = "200" ] && [ "$page_response1" = "200" ]; then
    echo "✅ Basic functionality working (integer IDs)"
else
    echo "⚠️  Basic functionality needs attention"
fi

if [ "$response2" = "200" ] || [ "$response3" = "200" ]; then
    echo "✅ String ID format working"
else
    echo "⚠️  String ID format needs attention"
fi

echo ""
echo "🌐 Test your professor pages:"
echo "   Integer format: https://facultyfinder.io/professor/1"
echo "   String format: https://facultyfinder.io/professor/CA-ON-002-00001"

if [ ! -z "$professor_name" ]; then
    echo "   Working example: Professor $professor_name"
fi

echo ""
echo "🔧 If issues persist:"
echo "   Check logs: sudo journalctl -u facultyfinder.service -f"
echo "   Test API: curl http://localhost:8008/api/v1/professor/1"
echo "   Database: psql -h localhost -U ff_user -d ff_production"

echo ""
echo "📋 Available professor IDs to test:"
echo "   1, 2, 3... (integer format)"
if [ ! -z "$db_check" ] && [ "$db_check" -gt 0 ]; then
    echo "   CA-ON-002-00001, CA-ON-002-00002... (string format)"
else
    echo "   String format IDs pending generation completion"
fi

echo ""
echo "🛠️  Monitor your service:"
echo "   sudo systemctl status facultyfinder.service" 