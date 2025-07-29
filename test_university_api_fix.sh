#!/bin/bash

# Test script for Universities API and Favicon fixes
echo "🧪 Testing Universities API and Favicon Fixes"
echo "=============================================="

# Test health endpoint first
echo ""
echo "Testing health endpoint..."
health_response=$(curl -s "http://localhost:8008/health" || echo "Failed")
echo "Health: $health_response"

# Test universities endpoint
echo ""
echo "Testing universities endpoint..."
universities_response=$(curl -s "http://localhost:8008/api/v1/universities?page=1&per_page=5" || echo "Failed")
if [[ $universities_response == *"universities"* ]]; then
    echo "✅ Universities API working!"
    echo "Sample response: $(echo $universities_response | head -c 200)..."
else
    echo "❌ Universities API failed:"
    echo "$universities_response"
fi

# Test favicon endpoint
echo ""
echo "Testing favicon endpoint..."
favicon_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8008/favicon.ico")
if [[ $favicon_status == "204" ]]; then
    echo "✅ Favicon endpoint working! (Returns 204 No Content)"
else
    echo "❌ Favicon endpoint returned: $favicon_status"
fi

echo ""
echo "🎉 Test complete!"
echo ""
echo "Next steps:"
echo "1. Deploy to VPS: git pull && sudo systemctl restart facultyfinder.service"
echo "2. Test on live site: https://facultyfinder.io/universities" 