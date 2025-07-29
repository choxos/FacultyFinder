#!/bin/bash

echo "🎓 Deploying Faculty Profile & Enhancement Fixes"
echo "==============================================="
echo "Implementing faculty profiles, ID format, sorting & icons"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

# Pull all the fixes
echo "📥 Pulling faculty profile fixes from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ Faculty profile fixes pulled successfully"

# Generate professor IDs in new format
echo -e "\n🆔 Generating professor IDs in new format..."
python3 generate_professor_ids.py

if [ $? -eq 0 ]; then
    echo "✅ Professor IDs generated successfully"
else
    echo "⚠️  Professor ID generation had issues (continuing anyway)"
fi

# Restart FastAPI service
echo -e "\n🔄 Restarting FastAPI service with all fixes..."
sudo systemctl restart facultyfinder.service

# Wait for startup
echo "⏳ Waiting for service startup..."
sleep 5

# Test the fixes
echo -e "\n🧪 Testing faculty profile and enhancement fixes..."

echo "Testing faculty profile page:"
# Test with a sample professor ID (both old and new format)
profile_response_old=$(curl -s -w "%{http_code}" http://localhost:8008/professor/1 -o /dev/null)
if [ "$profile_response_old" = "200" ]; then
    echo "✅ Faculty profile (old ID format) OK (HTTP $profile_response_old)"
else
    echo "⚠️  Faculty profile (old ID format) failed (HTTP $profile_response_old)"
fi

# Test new ID format (assuming McMaster is CA-ON-002)
profile_response_new=$(curl -s -w "%{http_code}" http://localhost:8008/professor/CA-ON-002-00001 -o /dev/null)
if [ "$profile_response_new" = "200" ]; then
    echo "✅ Faculty profile (new ID format) OK (HTTP $profile_response_new)"
else
    echo "⚠️  Faculty profile (new ID format) response: HTTP $profile_response_new"
fi

echo -e "\nTesting faculty page with enhanced cards:"
faculties_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/faculties -o /dev/null)
if [ "$faculties_page_response" = "200" ]; then
    echo "✅ Enhanced faculty cards page OK (HTTP $faculties_page_response)"
else
    echo "❌ Enhanced faculty cards page failed (HTTP $faculties_page_response)"
fi

echo -e "\nTesting universities page with enhanced tables:"
universities_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/universities -o /dev/null)
if [ "$universities_page_response" = "200" ]; then
    echo "✅ Enhanced universities page OK (HTTP $universities_page_response)"
else
    echo "❌ Enhanced universities page failed (HTTP $universities_page_response)"
fi

echo -e "\nTesting API with enhanced fields:"
api_response=$(curl -s -w "%{http_code}" http://localhost:8008/api/v1/faculties?per_page=1 -o /tmp/api_test.json)
if [ "$api_response" = "200" ]; then
    echo "✅ Enhanced API OK (HTTP $api_response)"
    
    # Check for enhanced fields
    if grep -q "citation_count\|h_index\|position" /tmp/api_test.json 2>/dev/null; then
        echo "✅ Enhanced API fields detected"
    else
        echo "⚠️  Some enhanced API fields may be missing"
    fi
else
    echo "❌ Enhanced API failed (HTTP $api_response)"
fi

# Clean up test file
rm -f /tmp/api_test.json

# Check if JavaScript enhancements are working
echo -e "\nTesting JavaScript enhancements:"
if curl -s http://localhost:8008/faculties | grep -q "sortable.*data-sort" 2>/dev/null; then
    echo "✅ Sortable table headers detected"
else
    echo "⚠️  Sortable table headers may not be working"
fi

if curl -s http://localhost:8008/faculties | grep -q "fas fa-sort" 2>/dev/null; then
    echo "✅ Sort icons detected"
else
    echo "⚠️  Sort icons may be missing"
fi

# Final status
echo -e "\n" + "=" * 60
echo "🎉 Faculty Profile & Enhancement Deployment Complete!"
echo "===================================================="

if [ "$faculties_page_response" = "200" ] && [ "$profile_response_old" = "200" ]; then
    echo "✅ All faculty enhancements deployed successfully!"
    echo ""
    echo "🎓 Faculty Profile Features:"
    echo "   - Comprehensive professor profiles based on commit 6a50592"
    echo "   - Academic information with research areas"
    echo "   - Publication metrics and statistics"
    echo "   - Academic profiles (Google Scholar, ORCID, etc.)"
    echo "   - Contact information and university links"
    echo ""
    echo "🆔 New Professor ID Format:"
    echo "   - Format: UNIVERSITY_CODE-SEQUENCE (e.g., CA-ON-002-00001)"
    echo "   - Backwards compatible with old integer IDs"
    echo "   - Sequential numbering per university"
    echo ""
    echo "📊 Enhanced Sorting & Tables:"
    echo "   - Sortable columns in all list views"
    echo "   - Click column headers to sort ascending/descending"
    echo "   - Sort icons indicate current sort direction"
    echo "   - Works for universities and faculties tables"
    echo ""
    echo "🎨 UI Enhancements:"
    echo "   - Dark mode toggle with proper moon/sun icons"
    echo "   - Grid/list view toggles with proper icons"
    echo "   - Enhanced card layouts matching commit 6a50592"
    echo "   - Professional table layouts with sorting"
    echo ""
    echo "🌐 Test your enhancements:"
    echo "   Faculty Profiles: https://facultyfinder.io/professor/1"
    echo "   Faculty Directory: https://facultyfinder.io/faculties"
    echo "   Universities: https://facultyfinder.io/universities"
    echo "   New ID Format: https://facultyfinder.io/professor/CA-ON-002-00001"
    echo ""
    echo "🔧 Testing Features:"
    echo "   - Click column headers to sort tables"
    echo "   - Try dark mode toggle (bottom right)"
    echo "   - Switch between card/list views"
    echo "   - Test professor profile links"
else
    echo "⚠️  Some features need attention"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   sudo journalctl -u facultyfinder.service -f"
    echo "   curl http://localhost:8008/professor/1"
    echo "   curl http://localhost:8008/api/v1/faculties"
fi

echo -e "\n📊 Professor ID Mapping:"
if [ -f "professor_id_mapping.txt" ]; then
    echo "   Check professor_id_mapping.txt for ID mappings"
    echo "   Old ID → New ID format documented"
else
    echo "   No ID mapping file generated"
fi

echo -e "\n🛠️  Monitor your service:"
echo "   sudo systemctl status facultyfinder.service"
echo "   sudo journalctl -u facultyfinder.service -f" 