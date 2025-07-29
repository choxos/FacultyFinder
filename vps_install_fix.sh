#!/bin/bash
# VPS Installation Fix Script for FacultyFinder
# Run this script to fix pip/setuptools issues and install requirements properly

echo "🔧 FacultyFinder VPS Installation Fix"
echo "======================================"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Please activate your virtual environment first:"
    echo "   source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"
echo

# Step 1: Upgrade pip, setuptools, and wheel
echo "📦 Step 1: Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel
echo

# Step 2: Install build dependencies
echo "🔧 Step 2: Installing build dependencies..."
pip install --upgrade build setuptools-scm
echo

# Step 3: Install requirements with compatibility fixes
echo "📋 Step 3: Installing FacultyFinder requirements..."

# Check if requirements_vps.txt exists, otherwise use requirements.txt
if [ -f "requirements_vps.txt" ]; then
    echo "Using VPS-compatible requirements file..."
    pip install -r requirements_vps.txt
elif [ -f "requirements.txt" ]; then
    echo "Using standard requirements file with compatibility fixes..."
    
    # Install problematic packages individually first
    echo "Installing core packages first..."
    pip install Flask==2.3.2 Werkzeug==2.3.6 gunicorn==21.2.0
    
    echo "Installing database drivers..."
    pip install psycopg2-binary==2.9.7
    
    echo "Installing remaining packages..."
    pip install -r requirements.txt --no-deps --force-reinstall
    
    echo "Resolving dependencies..."
    pip check || pip install -r requirements.txt
else
    echo "❌ No requirements file found!"
    exit 1
fi

echo

# Step 4: Install additional production dependencies
echo "🚀 Step 4: Installing additional production dependencies..."
pip install redis flask-caching
echo

# Step 5: Verify installation
echo "✅ Step 5: Verifying installation..."
python3 -c "
import flask
import gunicorn
import psycopg2
import redis
print('✅ Core packages imported successfully')

try:
    import anthropic
    import openai
    print('✅ AI packages imported successfully')
except ImportError as e:
    print(f'⚠️  AI packages: {e}')

try:
    import cv_analyzer
    import research_areas_generator
    print('✅ FacultyFinder modules imported successfully')
except ImportError as e:
    print(f'⚠️  FacultyFinder modules: {e}')
"

echo
echo "🎉 Installation completed!"
echo
echo "📋 Next steps:"
echo "1. Set up your .env file"
echo "2. Initialize the database"
echo "3. Start the application with: gunicorn --bind 0.0.0.0:8008 webapp.wsgi:application"
echo 