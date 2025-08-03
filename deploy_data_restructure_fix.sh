#!/bin/bash

echo "🚀 Deploying Data Restructure Fixes"
echo "====================================="

# Check if we're on the VPS or local machine
if [ -f "/var/www/ff/.env" ]; then
    echo "🖥️  Detected VPS environment"
    ENV_LOCATION="/var/www/ff/.env"
else
    echo "💻 Detected local environment" 
    ENV_LOCATION=".env"
fi

echo ""
echo "📋 This script will:"
echo "   1. 🔄 Pull latest changes from GitHub (with updated file paths)"
echo "   2. 🔍 Run comprehensive database diagnostics"
echo "   3. 🗄️ Update database if needed"
echo "   4. 🚀 Restart FastAPI service"
echo "   5. 🧪 Test universities API"
echo ""

# Confirm deployment
read -p "🚀 Ready to deploy data restructure fixes? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "📥 Step 1: Pulling latest changes from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed"
    exit 1
fi

echo ""
echo "🔍 Step 2: Running database diagnostics..."
python3 diagnose_database_issue.py

echo ""
echo "📊 Step 3: Checking if database needs rebuilding..."

# Check if the database is empty or has issues
if python3 update_database_from_csv.py --mode status | grep -q "0 universities\|0 professors\|Database connection failed"; then
    echo "⚠️ Database appears to be empty or has connection issues"
    echo ""
    read -p "🔄 Rebuild database from CSV files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ Performing full database rebuild..."
        python3 update_database_from_csv.py --mode full --restart
        
        if [ $? -ne 0 ]; then
            echo "❌ Database rebuild failed"
            exit 1
        fi
    else
        echo "⏭️ Skipping database rebuild"
    fi
else
    echo "✅ Database appears to have data, performing incremental update..."
    python3 update_database_from_csv.py --mode incremental --restart
fi

echo ""
echo "🚀 Step 4: Ensuring FastAPI service is running..."

# Check if systemctl is available (VPS)
if command -v systemctl &> /dev/null; then
    sudo systemctl restart facultyfinder.service
    sleep 3
    sudo systemctl status facultyfinder.service --no-pager
else
    echo "⚠️ systemctl not available - manual service restart may be needed"
fi

echo ""
echo "🧪 Step 5: Testing universities API..."

# Wait for service to be ready
sleep 5

# Test the API
echo "📡 Testing API endpoint..."
RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:8008/api/v1/universities?per_page=1")
HTTP_CODE="${RESPONSE: -3}"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Universities API is working!"
    # Extract just the response body (remove HTTP code)
    BODY="${RESPONSE%???}"
    echo "📊 Sample response: ${BODY:0:200}..."
else
    echo "❌ Universities API returned HTTP $HTTP_CODE"
    echo "📋 Response: $RESPONSE"
    
    echo ""
    echo "🔍 Checking service logs..."
    if command -v journalctl &> /dev/null; then
        sudo journalctl -u facultyfinder.service -n 10 --no-pager
    fi
fi

echo ""
echo "🎉 Data Restructure Fix Deployment Complete!"
echo "=========================================="

echo ""
echo "✅ What was fixed:"
echo "   📁 Updated all scripts to use new data file paths:"
echo "      OLD: data/mcmaster_hei_faculty.csv"
echo "      NEW: data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv"
echo "   🔧 Updated database update scripts"
echo "   🔧 Updated publication system scripts"
echo "   🆕 Added comprehensive diagnostic tool"

echo ""
echo "🔗 Quick Commands:"
echo "   📊 Check database status: python3 diagnose_database_issue.py"
echo "   🔄 Update database: ./update_db.sh"
echo "   🧪 Test API: curl http://localhost:8008/api/v1/universities?per_page=1"
echo "   📋 Check service: sudo systemctl status facultyfinder.service"

echo ""
echo "🌐 Test your website: https://facultyfinder.io/universities"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "🎉 Universities page should now be working! 🚀"
else
    echo "⚠️ If issues persist, run: python3 diagnose_database_issue.py"
fi 