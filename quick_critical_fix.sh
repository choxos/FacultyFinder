#!/bin/bash

echo "🚨 Quick Critical Fix"
echo "===================="
echo "Fixing universities typo and professor schema mismatch"

# Check if we're in the right directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

echo "🔧 Step 1: Fixing universities API typo..."

# Fix the languagess typo
sed -i 's/u\.languagess/u.languages/g' webapp/main.py
echo "✅ Fixed languagess → languages typo"

# Make sure all university field references are correct
sed -i 's/u\.type/u.university_type/g' webapp/main.py
sed -i 's/u\.language/u.languages/g' webapp/main.py
sed -i 's/u\.established/u.year_established/g' webapp/main.py
echo "✅ Fixed university field mappings"

echo "🔧 Step 2: Creating simplified professor API..."

# Create a backup
cp webapp/main.py webapp/main.py.backup

# Create a new simplified professor API endpoint that matches the actual database
cat > temp_professor_api.py << 'EOF'

@app.get("/api/v1/professor/{professor_id}")
async def get_professor(professor_id: str = Path(..., description="Professor ID")):
    """Get individual professor details"""
    try:
        async with await get_db_connection() as conn:
            # Handle both integer IDs and string format IDs
            if professor_id.isdigit():
                # Legacy integer ID
                query = """
                    SELECT p.id, p.name, p.professor_code, 
                           p.university_code, p.department, p.position, p.email, p.phone,
                           p.office, p.biography, p.research_interests, p.research_areas,
                           p.education, p.experience, p.awards_honors, p.memberships,
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name, 
                           COALESCE(u.city, '') as city, 
                           COALESCE(u.province_state, '') as province_state, 
                           COALESCE(u.country, '') as country, 
                           COALESCE(u.address, '') as address, 
                           COALESCE(u.website, '') as university_website
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.id = $1
                """
                params = [int(professor_id)]
            else:
                # String format ID - try professor_id_new first
                query = """
                    SELECT p.id, p.name, p.professor_code, 
                           p.university_code, p.department, p.position, p.email, p.phone,
                           p.office, p.biography, p.research_interests, p.research_areas,
                           p.education, p.experience, p.awards_honors, p.memberships,
                           COALESCE(p.professor_id_new, '') as professor_id_new,
                           COALESCE(u.name, '') as university_name, 
                           COALESCE(u.city, '') as city, 
                           COALESCE(u.province_state, '') as province_state, 
                           COALESCE(u.country, '') as country, 
                           COALESCE(u.address, '') as address, 
                           COALESCE(u.website, '') as university_website
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.professor_id_new = $1
                """
                params = [professor_id]

            row = await conn.fetchrow(query, *params)
            
            if not row:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            return dict(row)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professor {professor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

EOF

echo "✅ Created simplified professor API"

echo "🔧 Step 3: Replacing professor API in main.py..."

# Find the start and end of the professor API function and replace it
python3 << 'PYTHON_SCRIPT'
import re

with open('webapp/main.py', 'r') as f:
    content = f.read()

# Read the new professor API
with open('temp_professor_api.py', 'r') as f:
    new_api = f.read().strip()

# Replace the old professor API function
pattern = r'@app\.get\("/api/v1/professor/\{professor_id\}"\).*?(?=@app\.get|# Professor detail route|$)'
content = re.sub(pattern, new_api + '\n\n', content, flags=re.DOTALL)

with open('webapp/main.py', 'w') as f:
    f.write(content)

print("✅ Professor API replaced")
PYTHON_SCRIPT

# Clean up temp file
rm -f temp_professor_api.py

echo "🔄 Step 4: Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

echo "⏳ Waiting for service startup..."
sleep 5

echo "🧪 Step 5: Testing fixes..."

echo "Testing universities API:"
uni_response=$(curl -s -w "%{http_code}" -o /tmp/uni_test.json http://localhost:8008/api/v1/universities?per_page=3)

if [ "$uni_response" = "200" ]; then
    echo "✅ Universities API: HTTP $uni_response"
    if grep -q '"universities"' /tmp/uni_test.json; then
        echo "✅ Universities data returned successfully"
    fi
else
    echo "❌ Universities API: HTTP $uni_response"
    echo "📋 Error:"
    head -3 /tmp/uni_test.json 2>/dev/null
fi

echo "Testing professor API:"
prof_response=$(curl -s -w "%{http_code}" -o /tmp/prof_test.json http://localhost:8008/api/v1/professor/1)

if [ "$prof_response" = "200" ]; then
    echo "✅ Professor API: HTTP $prof_response"
    if grep -q '"name"' /tmp/prof_test.json; then
        prof_name=$(grep -o '"name":"[^"]*"' /tmp/prof_test.json | cut -d'"' -f4)
        echo "✅ Professor data: $prof_name"
    fi
else
    echo "❌ Professor API: HTTP $prof_response"
    echo "📋 Error:"
    head -3 /tmp/prof_test.json 2>/dev/null
fi

# Clean up
rm -f /tmp/uni_test.json /tmp/prof_test.json

echo ""
echo "🎯 Quick Fix Summary:"
echo "===================="

if [ "$uni_response" = "200" ] && [ "$prof_response" = "200" ]; then
    echo "✅ Both APIs fixed and working!"
    echo ""
    echo "🌐 Test your pages:"
    echo "   Universities: https://facultyfinder.io/universities"
    echo "   Professor: https://facultyfinder.io/professor/1"
else
    echo "⚠️  Some APIs still need attention"
    echo ""
    echo "🔧 Check logs: sudo journalctl -u facultyfinder.service -f"
fi

echo ""
echo "🛠️  Monitor service: sudo systemctl status facultyfinder.service" 