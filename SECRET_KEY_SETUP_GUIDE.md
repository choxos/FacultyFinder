# 🔐 Flask Secret Key Setup Guide for FacultyFinder

## What is a Flask Secret Key?

The Flask secret key is used for:
- **Session Management**: Encrypting session data
- **CSRF Protection**: Generating CSRF tokens
- **Flash Messages**: Securing flash message encryption
- **JWT Tokens**: Signing JSON Web Tokens
- **Cookie Security**: Encrypting secure cookies

## 🚨 Security Requirements

### ✅ Must Have:
- **Minimum 32 characters (256 bits)**
- **Cryptographically random**
- **Unique per environment** (dev/staging/production)
- **Stored in environment variables**
- **Never committed to version control**

### ❌ Never Use:
- Development keys in production
- Predictable patterns or words
- Short keys (< 32 characters)
- Keys stored in source code
- Same key across environments

## 🔧 Generation Methods

### Method 1: Using Provided Generator (Recommended)
```bash
cd /var/www/ff
python3 generate_secret_key.py
```

**Output Example:**
```
🔐 Flask Secret Key Generator for FacultyFinder
==================================================

✅ PRIMARY SECRET KEY (Recommended):
SECRET_KEY=a7f8d923c1e6b4a8f2d9c3e7b1a5f9d2c6e0b4a8f3d7c1e5b9a3f7d1c5e9b3a7f1

📝 Add to your .env file:
------------------------------
SECRET_KEY=a7f8d923c1e6b4a8f2d9c3e7b1a5f9d2c6e0b4a8f3d7c1e5b9a3f7d1c5e9b3a7f1
```

### Method 2: Python Commands
```bash
# Most secure - using secrets module (Python 3.6+)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Alternative - using os.urandom
python3 -c "import os, base64; print('SECRET_KEY=' + base64.b64encode(os.urandom(32)).decode())"

# URL-safe version
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

### Method 3: OpenSSL
```bash
# Generate 32-byte hex key (64 characters)
openssl rand -hex 32

# Generate base64 key
openssl rand -base64 32
```

### Method 4: Linux/Unix Systems
```bash
# Using /dev/urandom (secure)
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1

# Using dd and base64
dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 | tr -d '\n'
```

### Method 5: Online Generator (Use with Caution)
```bash
# Only if other methods don't work
curl -s "https://www.random.org/cgi-bin/randbyte?nbytes=32&format=h" | tr -d '\n'
```

## 📝 Implementation Steps

### Step 1: Generate Your Secret Key
Choose one of the methods above and generate your secret key.

### Step 2: Add to Environment File
```bash
# Edit your .env file
nano /var/www/ff/.env

# Add the secret key
SECRET_KEY=your_generated_secret_key_here
```

### Step 3: Verify Flask Configuration
The Flask app should be configured to use the environment variable:

```python
# In webapp/app.py (should already be configured)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'development-key-change-in-production'
```

### Step 4: Test the Configuration
```bash
# Test that the secret key is loaded correctly
cd /var/www/ff
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
secret_key = os.environ.get('SECRET_KEY')
if secret_key and secret_key != 'development-key-change-in-production':
    print('✅ Secret key configured correctly')
    print(f'Length: {len(secret_key)} characters')
else:
    print('❌ Secret key not configured or using development key')
"
```

## 🔄 Multiple Environment Setup

### Development Environment
```bash
# .env.development
SECRET_KEY=dev_key_different_from_production_32chars_minimum
FLASK_ENV=development
DEBUG=True
```

### Staging Environment
```bash
# .env.staging
SECRET_KEY=staging_key_different_from_dev_and_prod_32chars_min
FLASK_ENV=staging
DEBUG=False
```

### Production Environment
```bash
# .env.production (or just .env on production server)
SECRET_KEY=production_key_super_secure_never_shared_32chars_plus
FLASK_ENV=production
DEBUG=False
```

## 🛡️ Security Best Practices

### ✅ Do:
1. **Generate a new key for each environment**
2. **Use minimum 32 characters (64 recommended)**
3. **Store in environment variables**
4. **Rotate keys periodically**
5. **Use different keys for different applications**
6. **Keep keys in secure password manager**

### ❌ Don't:
1. **Never commit keys to git**
2. **Never share keys in plain text**
3. **Never reuse keys across environments**
4. **Never use predictable patterns**
5. **Never store in source code**
6. **Never use short keys**

## 🚨 Emergency Key Rotation

If your secret key is compromised:

### Step 1: Generate New Key Immediately
```bash
python3 -c "import secrets; print('NEW_SECRET_KEY=' + secrets.token_hex(32))"
```

### Step 2: Update Environment
```bash
# Backup old .env
cp /var/www/ff/.env /var/www/ff/.env.backup

# Update with new key
nano /var/www/ff/.env
# Replace SECRET_KEY with new value
```

### Step 3: Restart Application
```bash
sudo systemctl restart facultyfinder
sudo systemctl status facultyfinder
```

### Step 4: Verify Users
- All users will need to log in again
- All sessions will be invalidated
- CSRF tokens will be regenerated

## 🔍 Troubleshooting

### Issue: "RuntimeError: The session is unavailable"
**Solution**: Check if SECRET_KEY is properly set
```bash
echo $SECRET_KEY
python3 -c "import os; print(os.environ.get('SECRET_KEY', 'NOT SET'))"
```

### Issue: "CSRF token missing or incorrect"
**Solution**: Ensure SECRET_KEY is consistent and properly loaded

### Issue: Users constantly logged out
**Solution**: SECRET_KEY might be changing - ensure it's static in .env

## ✅ Verification Checklist

- [ ] Secret key generated using secure method
- [ ] Key is minimum 32 characters
- [ ] Key added to .env file
- [ ] .env file has correct permissions (600)
- [ ] Flask app loads environment variables
- [ ] Application starts without errors
- [ ] User sessions work correctly
- [ ] CSRF protection functions
- [ ] Different keys for dev/staging/production

## 📞 Emergency Contacts

If you need immediate help with secret key issues:
- Check Flask documentation
- Review FacultyFinder deployment logs
- Regenerate key if in doubt

**Remember: When in doubt, regenerate the key. It's better to be safe!** 