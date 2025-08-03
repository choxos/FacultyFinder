#!/bin/bash

echo "🚀 Deploying FacultyFinder via GitHub"
echo "====================================="

# SSH to VPS and pull latest changes from GitHub
echo "🔄 Pulling latest changes from GitHub on VPS..."
ssh xeradb@91.99.161.136 << 'EOF'
    echo "📂 Navigating to project directory..."
    cd /var/www/ff
    
    echo "📥 Pulling latest changes from GitHub..."
    git pull origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pulled changes from GitHub"
    else
        echo "❌ Failed to pull changes from GitHub"
        exit 1
    fi
    
    echo "🧪 Testing Python syntax..."
    python3 -m py_compile webapp/main.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Python syntax is valid"
    else
        echo "❌ Python syntax error still exists"
        exit 1
    fi
    
    echo "🔄 Restarting FacultyFinder service..."
    sudo systemctl restart facultyfinder.service
    sleep 3
    
    echo "🧪 Testing service health..."
    curl -s http://localhost:8008/health | jq .
    
    if [ $? -eq 0 ]; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check failed - checking service status..."
        sudo systemctl status facultyfinder.service --no-pager -l
    fi
    
    echo "🧪 Testing universities API..."
    curl -s "http://localhost:8008/api/v1/universities?per_page=1" | jq '.pagination // "Error"'
    
    echo "🧪 Testing countries API..."
    curl -s "http://localhost:8008/api/v1/countries" | jq 'length // "Error"'
    
    echo "🎉 GitHub deployment complete!"
EOF

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Check your website: https://facultyfinder.io"
else
    echo "❌ Deployment failed"
    exit 1
fi 