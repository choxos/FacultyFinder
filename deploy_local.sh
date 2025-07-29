#!/bin/bash

echo "🚀 Deploying FacultyFinder on VPS"
echo "================================="

echo "📂 Already in project directory: $(pwd)"

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

echo "📊 Checking service status..."
sudo systemctl status facultyfinder.service --no-pager -l | head -10

echo "🧪 Testing service health..."
curl -s http://localhost:8008/health

echo -e "\n🧪 Testing universities API..."
curl -s "http://localhost:8008/api/v1/universities?per_page=1"

echo -e "\n🧪 Testing countries API..."
curl -s "http://localhost:8008/api/v1/countries"

echo -e "\n🎉 Local deployment complete!"
echo "🌐 Check your website: https://facultyfinder.io" 