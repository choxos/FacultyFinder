#!/bin/bash
# FastAPI Service Debugging Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo -e "${BLUE}🔍 FastAPI Service Debugging${NC}"
echo "============================="

# Check if service exists
print_info "Checking service status..."
if systemctl is-enabled facultyfinder_fastapi >/dev/null 2>&1; then
    print_status "Service is enabled"
else
    print_warning "Service is not enabled"
fi

if systemctl is-active facultyfinder_fastapi >/dev/null 2>&1; then
    print_status "Service is active"
else
    print_error "Service is not active"
fi

# Show service status
print_info "Service status details:"
sudo systemctl status facultyfinder_fastapi --no-pager -l

# Check service logs
print_info "Recent service logs:"
sudo journalctl -u facultyfinder_fastapi -n 20 --no-pager

# Test database connection
print_info "Testing database connection..."
cd /var/www/ff
source venv/bin/activate

python3 -c "
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv('.env')

async def test_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        result = await conn.fetchval('SELECT COUNT(*) FROM professors')
        print(f'✅ Database connection OK: {result} professors')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"

# Test FastAPI import
print_info "Testing FastAPI app import..."
python3 -c "
try:
    from webapp.main import app
    print('✅ FastAPI app imports successfully')
    print(f'   Title: {app.title}')
    print(f'   Version: {app.version}')
except Exception as e:
    print(f'❌ FastAPI import failed: {e}')
    import traceback
    traceback.print_exc()
"

# Test port binding
print_info "Checking port 8008..."
if netstat -tlnp | grep -q ":8008 "; then
    print_status "Port 8008 is in use"
    netstat -tlnp | grep ":8008 "
else
    print_warning "Port 8008 is not in use"
fi

# Test health endpoint if service is running
print_info "Testing health endpoint..."
if curl -s http://127.0.0.1:8008/health >/dev/null 2>&1; then
    response=$(curl -s http://127.0.0.1:8008/health)
    print_status "Health endpoint responds: $response"
else
    print_error "Health endpoint not responding"
    
    # Try to manually start and test
    print_info "Attempting manual start for testing..."
    timeout 10s uvicorn webapp.main:app --host 127.0.0.1 --port 8009 --log-level debug &
    PID=$!
    sleep 3
    
    if curl -s http://127.0.0.1:8009/health >/dev/null 2>&1; then
        response=$(curl -s http://127.0.0.1:8009/health)
        print_status "Manual test successful: $response"
    else
        print_error "Manual test also failed"
    fi
    
    kill $PID 2>/dev/null || true
    wait $PID 2>/dev/null || true
fi

# Environment check
print_info "Environment variables:"
echo "DB_HOST: ${DB_HOST:-not set}"
echo "DB_PORT: ${DB_PORT:-not set}"
echo "DB_USER: ${DB_USER:-not set}"
echo "DB_NAME: ${DB_NAME:-not set}"

print_info "Debug complete!" 