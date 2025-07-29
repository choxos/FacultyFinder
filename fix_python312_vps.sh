#!/bin/bash
# Python 3.12 Compatibility Fix for FacultyFinder VPS
# This script fixes the pkgutil.ImpImporter error

echo "🔧 Python 3.12 VPS Compatibility Fix"
echo "===================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Please activate your virtual environment first:"
    echo "   cd /var/www/ff"
    echo "   source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"
echo "🐍 Python version: $(python3 --version)"
echo

# Step 1: Clean slate approach
echo "🧹 Step 1: Cleaning pip cache and temporary files..."
pip cache purge
rm -rf /tmp/pip-*
echo

# Step 2: Install compatible setuptools first
echo "🔧 Step 2: Installing Python 3.12 compatible setuptools..."
pip uninstall -y setuptools pkg_resources
pip install --upgrade pip
pip install "setuptools>=68.0.0" "wheel>=0.41.0"
echo

# Step 3: Install packages with binary-only approach (avoid source builds)
echo "📦 Step 3: Installing core packages (binary-only)..."

# Core Flask packages
pip install --only-binary=all Flask==2.3.2 || pip install Flask==2.3.2 --force-reinstall
pip install --only-binary=all Werkzeug==2.3.6 || pip install Werkzeug==2.3.6 --force-reinstall
pip install --only-binary=all gunicorn==21.2.0 || pip install gunicorn==21.2.0 --force-reinstall

# Database
pip install --only-binary=all psycopg2-binary==2.9.7 || pip install psycopg2-binary==2.9.7 --force-reinstall

# Essential utilities
pip install --only-binary=all python-dotenv==1.0.0 requests==2.32.3

echo

# Step 4: Install packages individually with fallbacks
echo "🔨 Step 4: Installing remaining packages individually..."

# Define packages with fallback versions
declare -a packages=(
    "Flask-Login==0.6.3"
    "bcrypt==4.1.3"
    "email-validator==2.1.1"
    "anthropic==0.34.2"
    "openai==1.54.4"
    "PyPDF2==3.0.1"
    "python-docx==0.8.11"
    "redis==5.0.1"
    "flask-caching==2.1.0"
    "pandas==2.1.4"
    "schedule==1.2.0"
    "lxml==4.9.3"
    "beautifulsoup4==4.12.3"
    "python-dateutil==2.8.2"
    "tqdm==4.66.1"
)

for package in "${packages[@]}"; do
    echo "Installing $package..."
    pip install --only-binary=all "$package" || {
        echo "Binary install failed, trying source build with timeout..."
        timeout 300 pip install "$package" --no-cache-dir || {
            echo "⚠️  Failed to install $package, skipping..."
            continue
        }
    }
done

echo

# Step 5: Install optional packages (can fail without breaking core functionality)
echo "📋 Step 5: Installing optional packages..."

declare -a optional_packages=(
    "google-generativeai==0.8.3"
    "biopython==1.83"
    "cryptography==41.0.8"
    "qrcode==7.4.2"
    "Pillow==10.1.0"
    "retrying==1.3.4"
)

for package in "${optional_packages[@]}"; do
    echo "Installing optional $package..."
    pip install --only-binary=all "$package" 2>/dev/null || {
        echo "⚠️  Optional package $package failed, continuing..."
    }
done

echo

# Step 6: Verify installation
echo "✅ Step 6: Verifying installation..."
python3 -c "
import sys
print(f'Python version: {sys.version}')

# Test core imports
try:
    import flask, gunicorn, psycopg2
    print('✅ Core web packages: OK')
except ImportError as e:
    print(f'❌ Core packages: {e}')

try:
    import flask_login, bcrypt, email_validator
    print('✅ Authentication packages: OK')
except ImportError as e:
    print(f'⚠️  Auth packages: {e}')

try:
    import anthropic, openai
    print('✅ AI packages: OK')
except ImportError as e:
    print(f'⚠️  AI packages: {e}')

try:
    import redis, flask_caching
    print('✅ Caching packages: OK')
except ImportError as e:
    print(f'⚠️  Cache packages: {e}')

try:
    import pandas, schedule
    print('✅ Data processing packages: OK')
except ImportError as e:
    print(f'⚠️  Data packages: {e}')
"

echo
echo "🎉 Python 3.12 compatibility fix completed!"
echo
echo "📋 Next steps:"
echo "1. Test your FacultyFinder app: python3 -c 'from webapp.app import app; print(\"App loads successfully\")'"
echo "2. Start the application: gunicorn --bind 127.0.0.1:8008 webapp.wsgi:application"
echo 