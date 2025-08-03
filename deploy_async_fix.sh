#!/bin/bash

echo "🔧 Deploying Async Syntax Fix to VPS"
echo "===================================="

# Copy the fixed main.py to VPS
echo "📤 Transferring fixed main.py..."
scp webapp/main.py xeradb@91.99.161.136:/var/www/ff/webapp/

if [ $? -eq 0 ]; then
    echo "✅ File transferred successfully"
else
    echo "❌ File transfer failed"
    exit 1
fi

# SSH to VPS and restart the service
echo "🔄 Restarting service on VPS..."
ssh xeradb@91.99.161.136 << 'EOF'
    echo "Testing Python syntax..."
    cd /var/www/ff
    python3 -m py_compile webapp/main.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Python syntax is valid"
        echo "🔄 Restarting service..."
        sudo systemctl restart facultyfinder.service
        sleep 3
        
        echo "🧪 Testing service..."
        curl -s http://localhost:8008/health | jq .
        
        echo "🧪 Testing universities API..."
        curl -s "http://localhost:8008/api/v1/universities?per_page=1" | jq '.pagination'
        
        echo "🎉 Deployment complete!"
    else
        echo "❌ Syntax error still exists"
        exit 1
    fi
EOF

echo "✅ Async syntax fix deployed successfully!" 