# 🚨 Emergency VPS Installation Fix - Python 3.12

## The Problem
Python 3.12 removed `pkgutil.ImpImporter`, causing build failures with older setuptools versions.

## 🔥 IMMEDIATE FIX (Run these commands on VPS):

```bash
# 1. Go to your project and activate venv
cd /var/www/ff
source venv/bin/activate

# 2. Emergency cleanup and setup
pip cache purge
pip uninstall -y setuptools pkg_resources
pip install --upgrade pip
pip install "setuptools>=68.0.0" "wheel>=0.41.0"

# 3. Install ONLY essential packages with binary wheels
pip install --only-binary=all Flask==2.3.2 Werkzeug==2.3.6 gunicorn==21.2.0
pip install --only-binary=all psycopg2-binary==2.9.7 python-dotenv==1.0.0
pip install --only-binary=all requests==2.32.3 Flask-Login==0.6.3
pip install --only-binary=all anthropic==0.34.2 openai==1.54.4
```

## ✅ Test Core Functionality:

```bash
python3 -c "import flask, gunicorn, psycopg2, anthropic; print('✅ Core packages working')"
```

## 🎯 Minimal Working Setup:

If the above works, you can start your app with just these packages:

```bash
# Test the app
python3 -c "from webapp.app import app; print('✅ App loads')"

# Start the server
gunicorn --bind 127.0.0.1:8008 webapp.wsgi:application
```

## 📦 Add More Packages Later (one by one):

```bash
# Add caching
pip install --only-binary=all redis==5.0.1 flask-caching==2.1.0

# Add document processing
pip install --only-binary=all PyPDF2==3.0.1 python-docx==0.8.11

# Add data processing
pip install --only-binary=all pandas==2.1.4 schedule==1.2.0
```

## 🔧 Alternative: Downgrade Python (if nothing else works)

```bash
# Only if absolutely necessary
sudo apt install python3.11 python3.11-venv python3.11-dev
python3.11 -m venv venv_311
source venv_311/bin/activate
pip install -r requirements.txt
```

## 🏃‍♂️ Quick Success Path:

1. ✅ Clean setuptools: `pip install "setuptools>=68.0.0"`
2. ✅ Install core only: Flask, gunicorn, psycopg2-binary, anthropic, openai  
3. ✅ Test app loads: `python3 -c "from webapp.app import app"`
4. ✅ Start server: `gunicorn --bind 127.0.0.1:8008 webapp.wsgi:application`
5. ✅ Add features incrementally

**Priority: Get the app running first, add features later!** 🚀 