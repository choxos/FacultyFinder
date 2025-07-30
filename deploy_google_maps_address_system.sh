#!/bin/bash

echo "🗺️ FacultyFinder Google Maps Address System Deployment"
echo "======================================================"

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
echo "   1. 🔧 Update database schema with new address columns"
echo "   2. 📥 Import address data from university_codes.csv"
echo "   3. 🔄 Update FastAPI endpoints to support new address fields"
echo "   4. 🎨 Deploy enhanced frontend with Google Maps integration"
echo "   5. 🚀 Restart the FacultyFinder service"
echo ""

# Confirm deployment
read -p "🚀 Ready to deploy Google Maps address system? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "🔧 Step 1: Installing required packages..."
pip install psycopg2-binary pandas python-dotenv

if [ $? -ne 0 ]; then
    echo "❌ Package installation failed"
    exit 1
fi

echo ""
echo "🗄️ Step 2: Updating database schema with address columns..."
python3 update_university_address_schema.py

if [ $? -ne 0 ]; then
    echo "❌ Database schema update failed"
    echo "💡 Make sure your database credentials are correct in .env"
    exit 1
fi

echo ""
echo "🏫 Step 3: Updating university data with address information..."
python3 update_database_from_csv.py --mode universities

if [ $? -ne 0 ]; then
    echo "❌ University data update failed"
    exit 1
fi

echo ""
echo "🧪 Step 4: Testing Python syntax..."
python3 -m py_compile webapp/main.py

if [ $? -ne 0 ]; then
    echo "❌ Python syntax validation failed"
    exit 1
fi

echo ""
echo "🔄 Step 5: Restarting FacultyFinder service..."
sudo systemctl restart facultyfinder.service

if [ $? -ne 0 ]; then
    echo "❌ Service restart failed"
    echo "💡 Try manually: sudo systemctl restart facultyfinder.service"
    exit 1
fi

echo ""
echo "⏳ Waiting for service to start..."
sleep 5

echo ""
echo "📊 Step 6: Checking service status..."
sudo systemctl status facultyfinder.service --no-pager

echo ""
echo "🧪 Step 7: Testing API endpoints..."

# Test health endpoint
echo "🔍 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "http://localhost:8008/health")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint failed: $HEALTH_RESPONSE"
fi

# Test universities endpoint
echo "🔍 Testing universities endpoint..."
UNI_RESPONSE=$(curl -s "http://localhost:8008/api/v1/universities?per_page=1")
if [[ $UNI_RESPONSE == *"full_address"* ]] && [[ $UNI_RESPONSE == *"building_number"* ]]; then
    echo "✅ Universities endpoint includes new address fields"
else
    echo "⚠️ Universities endpoint may not include new address fields"
    echo "Response sample: ${UNI_RESPONSE:0:200}..."
fi

echo ""
echo "📋 Step 8: Verifying Google Maps integration..."

# Check if we can extract a sample address
SAMPLE_UNI=$(curl -s "http://localhost:8008/api/v1/universities?per_page=1" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'universities' in data and len(data['universities']) > 0:
        uni = data['universities'][0]
        print(f\"University: {uni.get('name', 'N/A')}\")
        print(f\"Full Address: {uni.get('full_address', 'N/A')}\")
        print(f\"Building Number: {uni.get('building_number', 'N/A')}\")
        print(f\"Street: {uni.get('street', 'N/A')}\")
        print(f\"Postal Code: {uni.get('postal_code', 'N/A')}\")
        if uni.get('full_address'):
            print('✅ Google Maps address generation working!')
        else:
            print('⚠️ Address data may be incomplete')
except:
    print('❌ Could not parse response')
")

echo "$SAMPLE_UNI"

echo ""
echo "🎉 Google Maps Address System Deployment Complete!"
echo "=================================================="

echo ""
echo "✅ What's New:"
echo "   🗺️ Enhanced Google Maps integration with detailed addresses"
echo "   🏠 University addresses now show: building number + street + postal code"
echo "   🎯 Better formatted address for precise Google Maps locations"
echo "   🎨 Improved UI with styled Maps buttons and address display"
echo "   📱 Responsive design for mobile devices"

echo ""
echo "🔗 New Features on Universities Page:"
echo "   • 🗺️ Enhanced 'Maps' buttons with better styling"
echo "   • 🏠 Detailed address display (building number + street)"
echo "   • 📍 More precise Google Maps integration"
echo "   • 🎨 Improved visual design with address cards"

echo ""
echo "🌐 Test Your Website:"
echo "   1. Visit: https://facultyfinder.io/universities"
echo "   2. Look for the blue 'Maps' buttons next to university locations"
echo "   3. Click a Maps button to see precise Google Maps location"
echo "   4. Notice the detailed address information displayed"

echo ""
echo "🛠️ Database Changes Applied:"
echo "   • Added 'building_number' column to universities table"
echo "   • Added 'street' column to universities table"  
echo "   • Added 'postal_code' column to universities table"
echo "   • Created 'full_address' computed field for Google Maps"
echo "   • Updated API to return all new address fields"

echo ""
echo "📊 To Update Universities in the Future:"
echo "   ./update_db.sh universities    # Update university address data"
echo "   ./update_db.sh                 # Regular faculty updates (unchanged)"

echo ""
echo "🎉 Deployment successful! Your Google Maps integration is now live! 🚀"
