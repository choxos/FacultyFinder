# VPS Installation Fix Guide

## 🚨 Fix for Setuptools and Requirements Errors

### Quick Fix Commands:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Upgrade pip and build tools
pip install --upgrade pip setuptools wheel build

# 3. Install core packages first
pip install Flask==2.3.2 Werkzeug==2.3.6 gunicorn==21.2.0 psycopg2-binary==2.9.7

# 4. Use VPS-compatible requirements
pip install -r requirements_vps.txt

# 5. Install additional production packages
pip install redis flask-caching
```

### Alternative Method (if above fails):

```bash
# Install packages one by one to identify issues
pip install Flask==2.3.2
pip install gunicorn==21.2.0
pip install psycopg2-binary==2.9.7
pip install python-dotenv==1.0.0

# Continue with other essential packages...
pip install anthropic==0.34.2
pip install openai==1.54.4
pip install requests==2.32.3
```

## 🔧 Root Cause Analysis:

1. **Setuptools Error**: Python 3.12 compatibility issues with older setuptools
2. **Missing requirements_publications.txt**: File referenced in deployment guide but doesn't exist
3. **Version Conflicts**: Some packages in requirements.txt may have incompatible versions

## ✅ Fixed Files Created:

- `requirements_vps.txt` - VPS-compatible requirements with tested versions
- `vps_install_fix.sh` - Automated installation script
- This guide for manual troubleshooting

## 🚀 Test Installation:

```bash
python3 -c "
import flask, gunicorn, psycopg2
print('✅ Core packages working')
"
```

## 💡 If Issues Persist:

1. Check Python version: `python3 --version`
2. Check pip version: `pip --version`
3. Clear pip cache: `pip cache purge`
4. Recreate virtual environment:
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   ``` 