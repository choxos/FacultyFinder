#!/bin/bash

echo "🚀 FacultyFinder FastAPI Service Fix"
echo "===================================="

# Change to app directory
cd /var/www/ff

echo -e "\n📍 Current directory: $(pwd)"

# Stop any running services first
echo -e "\n🛑 Stopping current services..."
sudo systemctl stop facultyfinder.service 2>/dev/null

# Kill any remaining processes on port 8008
echo "🔫 Killing processes on port 8008..."
sudo pkill -f "uvicorn"
sudo pkill -f "gunicorn"
sleep 2

# Check if FastAPI files exist
echo -e "\n📁 Checking FastAPI files..."
if [ ! -f "webapp/main.py" ]; then
    echo "❌ webapp/main.py not found. Need to pull latest code."
    echo "Running: git pull origin main"
    git pull origin main
fi

if [ ! -f "requirements_fastapi.txt" ]; then
    echo "❌ requirements_fastapi.txt not found. Creating it..."
    cat > requirements_fastapi.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
asyncpg==0.29.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
psycopg2-binary==2.9.7
pandas==2.1.4
requests==2.31.0
EOF
fi

# Install/update FastAPI dependencies
echo -e "\n📦 Installing FastAPI dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_fastapi.txt

# Check .env file
echo -e "\n⚙️  Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file missing!"
    exit 1
fi

# Add DATABASE_URL if missing
if ! grep -q "DATABASE_URL" .env; then
    echo "Adding DATABASE_URL to .env..."
    echo "" >> .env
    echo "# FastAPI Database URL" >> .env
    echo "DATABASE_URL=postgresql://ff_user:Choxos10203040@localhost:5432/ff_production" >> .env
fi

# Test database connection
echo -e "\n🗄️  Testing database connection..."
python3 -c "
import asyncio
import asyncpg
async def test():
    try:
        conn = await asyncpg.connect('postgresql://ff_user:Choxos10203040@localhost:5432/ff_production')
        count = await conn.fetchval('SELECT COUNT(*) FROM professors')
        print(f'✅ Database connection successful - {count} professors')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False
    return True
asyncio.run(test())
"

# Test FastAPI app import
echo -e "\n🧪 Testing FastAPI app import..."
python3 -c "
try:
    from webapp.main import app
    print('✅ FastAPI app imported successfully')
except Exception as e:
    print(f'❌ FastAPI app import failed: {e}')
"

# Update service file to use FastAPI
echo -e "\n⚙️  Updating service configuration..."
sudo tee /etc/systemd/system/facultyfinder.service > /dev/null << 'EOF'
[Unit]
Description=FacultyFinder FastAPI Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=xeradb
Group=xeradb
WorkingDirectory=/var/www/ff
Environment=PATH=/var/www/ff/venv/bin
EnvironmentFile=/var/www/ff/.env
ExecStart=/var/www/ff/venv/bin/uvicorn webapp.main:app --host 0.0.0.0 --port 8008 --workers 1
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3
TimeoutStartSec=30
TimeoutStopSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=false
ProtectSystem=full
ReadWritePaths=/var/www/ff

[Install]
WantedBy=multi-user.target
EOF

# Reload and start service
echo -e "\n🔄 Reloading and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable facultyfinder.service
sudo systemctl start facultyfinder.service

# Wait a moment for service to start
sleep 5

# Check service status
echo -e "\n📊 Service status:"
sudo systemctl status facultyfinder.service --no-pager -l

# Test the API endpoints
echo -e "\n🧪 Testing API endpoints..."

echo "Testing /health:"
if curl -s http://localhost:8008/health; then
    echo -e "\n✅ Health endpoint OK"
else
    echo -e "\n❌ Health endpoint failed"
fi

echo -e "\nTesting /api/v1/stats:"
if curl -s http://localhost:8008/api/v1/stats; then
    echo -e "\n✅ Stats endpoint OK"
else
    echo -e "\n❌ Stats endpoint failed"
fi

echo -e "\nTesting /api/v1/universities:"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8008/api/v1/universities?page=1&per_page=5")
echo "Response code: $RESPONSE"
if [ "$RESPONSE" = "200" ]; then
    echo "✅ Universities endpoint OK"
else
    echo "❌ Universities endpoint failed"
fi

echo -e "\nTesting /api/v1/faculties:"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8008/api/v1/faculties?page=1&per_page=5")
echo "Response code: $RESPONSE"
if [ "$RESPONSE" = "200" ]; then
    echo "✅ Faculties endpoint OK"
else
    echo "❌ Faculties endpoint failed"
fi

# Test website
echo -e "\n🌐 Testing website:"
WEBSITE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://facultyfinder.io)
echo "Website response: $WEBSITE_RESPONSE"

if [ "$WEBSITE_RESPONSE" = "200" ]; then
    echo "✅ Website is responding"
else
    echo "❌ Website is not responding properly"
fi

echo -e "\n✅ FastAPI service fix completed!"
echo -e "\n📋 Summary:"
echo "- Service should now be running on port 8008"
echo "- Check logs with: sudo journalctl -u facultyfinder.service -f"
echo "- Test API directly: curl http://localhost:8008/health"
echo "- If issues persist, check the logs for specific errors" 