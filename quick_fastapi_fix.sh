#!/bin/bash
# Quick FastAPI Fix Script
# Run this on the VPS to manually fix the FastAPI service

echo "🔧 Quick FastAPI Fix"
echo "==================="

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Stop any running services
echo "🛑 Stopping services..."
sudo systemctl stop facultyfinder_fastapi 2>/dev/null || true
sudo systemctl stop facultyfinder 2>/dev/null || true

# Update the service file with the fixed version
echo "📝 Updating service file..."
sudo cp facultyfinder_fastapi_fixed.service /etc/systemd/system/facultyfinder_fastapi.service
sudo systemctl daemon-reload

# Test FastAPI manually first
echo "🧪 Testing FastAPI manually..."
cd /var/www/ff
source venv/bin/activate

# Quick test
timeout 5s uvicorn webapp.main:app --host 127.0.0.1 --port 8009 &
TEST_PID=$!
sleep 3

if curl -s http://127.0.0.1:8009/health | grep -q "healthy"; then
    echo "✅ Manual test successful"
    kill $TEST_PID 2>/dev/null || true
    
    # Start the actual service
    echo "🚀 Starting FastAPI service..."
    sudo systemctl enable facultyfinder_fastapi
    sudo systemctl start facultyfinder_fastapi
    
    # Wait and test
    sleep 5
    
    if sudo systemctl is-active --quiet facultyfinder_fastapi; then
        echo "✅ Service is running"
        
        if curl -s http://127.0.0.1:8008/health | grep -q "healthy"; then
            echo "✅ Service responds to health check"
            echo "🎉 FastAPI migration successful!"
            
            # Test the website
            if curl -s https://facultyfinder.io/health >/dev/null 2>&1; then
                echo "✅ Website is responding"
            else
                echo "⚠️  Website not responding - check nginx"
            fi
        else
            echo "❌ Service not responding on port 8008"
            sudo journalctl -u facultyfinder_fastapi -n 10
        fi
    else
        echo "❌ Service failed to start"
        sudo journalctl -u facultyfinder_fastapi -n 10
    fi
else
    echo "❌ Manual test failed"
    kill $TEST_PID 2>/dev/null || true
    
    # Show logs for debugging
    echo "Debug info:"
    python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')
print(f'DB_USER: {os.getenv(\"DB_USER\")}')
print(f'DB_NAME: {os.getenv(\"DB_NAME\")}')
"
fi 