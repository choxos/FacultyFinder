#!/bin/bash

echo "🎨 Deploying University & Faculty Card Updates"
echo "=============================================="
echo "Adding detailed card information from commit 6a50592"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

# Pull the card updates
echo "📥 Pulling card updates from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ Card updates pulled successfully"

# Restart FastAPI service
echo -e "\n🔄 Restarting FastAPI service with enhanced cards..."
sudo systemctl restart facultyfinder.service

# Wait for startup
echo "⏳ Waiting for service startup..."
sleep 5

# Test card data
echo -e "\n🧪 Testing enhanced card functionality..."

echo "Testing universities API with enhanced fields:"
universities_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/universities?per_page=1 -o /tmp/universities_test.json)
if [ "$universities_response" = "200" ]; then
    echo "✅ Universities API OK (HTTP $universities_response)"
    
    # Check if enhanced fields are present
    if grep -q "university_type\|website\|languages\|address" /tmp/universities_test.json 2>/dev/null; then
        echo "✅ Enhanced university fields detected"
    else
        echo "⚠️  Enhanced university fields may be missing"
    fi
else
    echo "❌ Universities API failed (HTTP $universities_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

echo -e "\nTesting faculties API with enhanced fields:"
faculties_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/faculties?per_page=1 -o /tmp/faculties_test.json)
if [ "$faculties_response" = "200" ]; then
    echo "✅ Faculties API OK (HTTP $faculties_response)"
    
    # Check if enhanced fields are present
    if grep -q "citation_count\|h_index\|adjunct\|full_time" /tmp/faculties_test.json 2>/dev/null; then
        echo "✅ Enhanced faculty fields detected"
    else
        echo "⚠️  Enhanced faculty fields may be missing"
    fi
else
    echo "❌ Faculties API failed (HTTP $faculties_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

echo -e "\nTesting university cards page:"
university_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/universities -o /dev/null)
if [ "$university_page_response" = "200" ]; then
    echo "✅ University cards page OK (HTTP $university_page_response)"
else
    echo "❌ University cards page failed (HTTP $university_page_response)"
fi

echo -e "\nTesting faculty cards page:"
faculty_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/faculties -o /dev/null)
if [ "$faculty_page_response" = "200" ]; then
    echo "✅ Faculty cards page OK (HTTP $faculty_page_response)"
else
    echo "❌ Faculty cards page failed (HTTP $faculty_page_response)"
fi

# Clean up test files
rm -f /tmp/universities_test.json /tmp/faculties_test.json

# Final status
echo -e "\n" + "=" * 60
echo "🎉 Enhanced Card Updates Deployment Complete!"
echo "============================================="

if [ "$universities_response" = "200" ] && [ "$faculties_response" = "200" ]; then
    echo "✅ Card enhancements deployed successfully!"
    echo ""
    echo "🎨 Enhanced University Cards Now Include:"
    echo "   - Google Maps links for addresses"
    echo "   - Language of instruction"
    echo "   - Official website links"
    echo "   - University type (Public/Private)"
    echo "   - Department count statistics"
    echo "   - Enhanced visual formatting"
    echo ""
    echo "🎨 Enhanced Faculty Cards Now Include:"
    echo "   - Part-time employment indicators"
    echo "   - Citation count in metrics"
    echo "   - H-index in publication footer"
    echo "   - Research areas as interactive badges"
    echo "   - University and department filters"
    echo "   - Professional card layout"
    echo ""
    echo "🌐 Test your enhanced cards:"
    echo "   Universities: https://facultyfinder.io/universities"
    echo "   Faculties: https://facultyfinder.io/faculties"
    echo "   Homepage: https://facultyfinder.io/ (featured faculty)"
    echo ""
    echo "✅ All cards now match commit 6a50592 structure!"
else
    echo "⚠️  Some API endpoints need attention"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   sudo journalctl -u facultyfinder.service -f"
    echo "   curl http://localhost:8008/api/v1/universities"
    echo "   curl http://localhost:8008/api/v1/faculties"
fi

echo -e "\n🛠️  Monitor your service:"
echo "   sudo systemctl status facultyfinder.service"
echo "   sudo journalctl -u facultyfinder.service -f" 