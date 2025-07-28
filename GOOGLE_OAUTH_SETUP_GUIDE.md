# Google OAuth Setup Guide for FacultyFinder 🔐

This guide will walk you through setting up Google OAuth authentication for FacultyFinder, allowing users to sign in and register using their Google accounts.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Google Cloud Console Setup](#google-cloud-console-setup)
4. [Environment Configuration](#environment-configuration)
5. [Testing Setup](#testing-setup)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

---

## Overview

### ✅ Features Implemented

- **🔑 OAuth 2.0 Authentication**: Secure Google login integration
- **👤 Automatic Account Creation**: New users automatically get accounts
- **📧 Email Verification**: Uses verified Google email addresses
- **🖼️ Profile Pictures**: Imports Google profile pictures
- **🔄 Seamless Integration**: Works alongside existing email/password login
- **📱 Mobile Friendly**: Works on all devices and platforms

### 🛠️ How It Works

1. User clicks "Sign in with Google" button
2. Redirected to Google's secure authentication
3. User grants permission to FacultyFinder
4. Google returns user profile information
5. System either logs in existing user or creates new account
6. User is redirected to dashboard or profile completion

---

## Prerequisites

### 📦 Required Dependencies

Make sure these packages are installed:

```bash
pip install authlib==1.6.1
pip install requests==2.32.3
pip install flask-login==0.6.3
```

### 🏗️ System Requirements

- Python 3.8+
- Flask 2.0+
- SSL certificate (required for OAuth callbacks)
- Domain name (for production)

---

## Google Cloud Console Setup

### Step 1: Create a Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project**
   - Click "Select a project" → "New Project"
   - **Project Name**: `FacultyFinder OAuth`
   - **Organization**: Leave as default
   - Click "Create"

3. **Select Your Project**
   - Make sure your new project is selected in the top dropdown

### Step 2: Enable Google+ API

1. **Navigate to APIs & Services**
   - In the left sidebar: `APIs & Services` → `Library`

2. **Enable Required APIs**
   - Search for "Google+ API" → Click → Enable
   - Search for "People API" → Click → Enable (optional but recommended)

### Step 3: Configure OAuth Consent Screen

1. **Go to OAuth Consent Screen**
   - Left sidebar: `APIs & Services` → `OAuth consent screen`

2. **Choose User Type**
   - Select **"External"** (unless you have Google Workspace)
   - Click "Create"

3. **App Information**
   ```
   App name: FacultyFinder
   User support email: your-email@domain.com
   App logo: (optional - upload FacultyFinder logo)
   ```

4. **App Domain**
   ```
   Application home page: https://facultyfinder.io
   Application privacy policy: https://facultyfinder.io/privacy
   Application terms of service: https://facultyfinder.io/terms
   ```

5. **Authorized Domains**
   ```
   facultyfinder.io
   localhost (for development)
   ```

6. **Developer Contact Information**
   ```
   Email addresses: your-email@domain.com
   ```

7. **Scopes**
   - Click "Add or Remove Scopes"
   - Select these scopes:
     - `openid`
     - `email`
     - `profile`
   - Click "Update"

8. **Test Users** (for development)
   - Add your test email addresses
   - Click "Add Users"

### Step 4: Create OAuth 2.0 Credentials

1. **Go to Credentials**
   - Left sidebar: `APIs & Services` → `Credentials`

2. **Create Credentials**
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"

3. **Application Type**
   - Select **"Web application"**
   - **Name**: `FacultyFinder Web Client`

4. **Authorized JavaScript Origins**
   ```
   For Development:
   http://localhost:5000
   http://localhost:8080
   http://127.0.0.1:5000
   
   For Production:
   https://facultyfinder.io
   https://www.facultyfinder.io
   ```

5. **Authorized Redirect URIs**
   ```
   For Development:
   http://localhost:5000/auth/google/callback
   http://localhost:8080/auth/google/callback
   
   For Production:
   https://facultyfinder.io/auth/google/callback
   https://www.facultyfinder.io/auth/google/callback
   ```

6. **Download Credentials**
   - Click "Create"
   - **Save the Client ID and Client Secret** - you'll need these!

---

## Environment Configuration

### Development Setup

Create or update your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Example values (replace with your actual credentials):
# GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=GOCSPX-abcd1234efgh5678ijkl
```

### Production Setup

1. **Environment Variables**
   ```bash
   export GOOGLE_CLIENT_ID="your_production_client_id"
   export GOOGLE_CLIENT_SECRET="your_production_client_secret"
   ```

2. **Secure Storage**
   - Never commit OAuth credentials to version control
   - Use secure environment variable management
   - Consider using services like AWS Secrets Manager or Azure Key Vault

---

## Testing Setup

### Local Development Testing

1. **Start Your Flask App**
   ```bash
   cd webapp
   python app.py
   ```

2. **Test OAuth Flow**
   - Visit: `http://localhost:5000/login`
   - Click "Sign in with Google"
   - Complete Google authentication
   - Verify redirect back to your app

3. **Verify Database Integration**
   ```bash
   sqlite3 ../database/facultyfinder_dev.db "SELECT * FROM users WHERE email LIKE '%gmail.com';"
   ```

### Test Account Management

#### For New Users:
- Should create account automatically
- Should populate name and email from Google
- Should redirect to profile completion page

#### For Existing Users:
- Should log in automatically
- Should update profile picture if not set
- Should redirect to dashboard

---

## Production Deployment

### SSL Certificate Requirement

⚠️ **CRITICAL**: Google OAuth requires HTTPS in production!

```bash
# Example with Let's Encrypt
sudo certbot --nginx -d facultyfinder.io -d www.facultyfinder.io
```

### Domain Configuration

1. **Update Google Console**
   - Add your production domain to authorized origins
   - Add your production callback URL
   - Remove localhost URLs for security

2. **Update Environment Variables**
   ```bash
   # Production environment
   FLASK_ENV=production
   GOOGLE_CLIENT_ID=your_production_client_id
   GOOGLE_CLIENT_SECRET=your_production_client_secret
   ```

### Deployment Checklist

- [ ] SSL certificate installed and working
- [ ] Production domain added to Google Console
- [ ] Environment variables configured securely
- [ ] Database schema includes users table with OAuth fields
- [ ] OAuth consent screen published (not in testing mode)
- [ ] Test user flow on production domain

---

## Troubleshooting

### Common Issues

#### 1. "redirect_uri_mismatch" Error

**Problem**: The callback URL doesn't match what's configured in Google Console.

**Solution**:
```bash
# Check your current callback URL
echo "Current URL: $(python -c "from webapp.app import app; print(app.config.get('SERVER_NAME', 'localhost:5000'))")/auth/google/callback"

# Update Google Console with exact URL
```

#### 2. "access_denied" Error

**Problem**: User denied permission or app not verified.

**Solutions**:
- Ensure OAuth consent screen is properly configured
- Check if app is in testing mode (add test users)
- Verify required scopes are requested

#### 3. "invalid_client" Error

**Problem**: Wrong client ID or client secret.

**Solutions**:
```bash
# Verify environment variables
echo "Client ID: $GOOGLE_CLIENT_ID"
echo "Client Secret: ${GOOGLE_CLIENT_SECRET:0:10}..." # Show only first 10 chars

# Regenerate credentials if needed
```

#### 4. Database Errors

**Problem**: User creation fails.

**Check**:
```sql
-- Verify users table exists
.schema users

-- Check for constraint violations
PRAGMA foreign_key_check;
```

### Debug Mode

Enable detailed OAuth debugging:

```python
# Add to app.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# OAuth-specific debugging
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'  # Development only!
```

### Log Monitoring

Monitor these log entries:

```bash
# Successful OAuth login
grep "User logged in via Google" app.log

# OAuth errors
grep "Google OAuth error" app.log

# New user registrations
grep "New user registered via Google" app.log
```

---

## Security Considerations

### 🔒 Production Security

#### Environment Variables
```bash
# Use secure secret management
# Never hardcode credentials
GOOGLE_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id oauth/google --query SecretString --output text)
```

#### Database Security
```sql
-- Ensure sensitive data is protected
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_oauth_provider ON users(oauth_provider);
```

#### Session Security
```python
# app.py security configuration
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
```

### 🛡️ OAuth Best Practices

1. **Scope Minimization**
   - Only request `openid`, `email`, `profile`
   - Avoid requesting unnecessary permissions

2. **State Parameter**
   - Our implementation uses Authlib's built-in CSRF protection
   - Verify state parameter on callback

3. **Token Handling**
   - Never store access tokens long-term
   - Use refresh tokens only when necessary
   - Implement token revocation

4. **User Data**
   - Only store essential user information
   - Follow GDPR/privacy regulations
   - Implement data deletion procedures

### 🔍 Monitoring & Alerts

Set up monitoring for:

```bash
# Failed authentication attempts
grep -c "Google OAuth error" app.log

# Unusual user creation patterns
sqlite3 database.db "SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-1 hour') AND oauth_provider = 'google';"

# Database integrity
sqlite3 database.db "SELECT COUNT(*) FROM users WHERE email IS NULL OR email = '';"
```

---

## Advanced Configuration

### Multiple OAuth Providers

To add more OAuth providers (GitHub, Microsoft, etc.):

```python
# app.py - Add after Google configuration
github = oauth.register(
    name='github',
    client_id=os.environ.get('GITHUB_CLIENT_ID'),
    client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)
```

### Custom User Attributes

Add OAuth-specific fields to users table:

```sql
ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);
ALTER TABLE users ADD COLUMN oauth_id VARCHAR(100);
ALTER TABLE users ADD COLUMN profile_picture TEXT;
ALTER TABLE users ADD COLUMN last_oauth_login TIMESTAMP;
```

### Rate Limiting

Implement OAuth rate limiting:

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/auth/google')
@limiter.limit("10 per minute")
def google_login():
    # OAuth login logic
```

---

## Maintenance

### Regular Tasks

#### Monthly:
- Review OAuth logs for errors
- Update dependencies
- Check Google Cloud Console for usage stats
- Verify SSL certificate status

#### Quarterly:
- Review OAuth consent screen
- Update privacy policy if needed
- Audit user permissions
- Security penetration testing

#### Annually:
- Rotate OAuth credentials
- Review and update scopes
- Complete security audit
- Update terms of service

### Migration Considerations

If migrating existing users to OAuth:

```sql
-- Link existing accounts by email
UPDATE users 
SET oauth_provider = 'google', 
    oauth_id = 'pending'
WHERE email IN (
    SELECT email FROM oauth_users
) AND oauth_provider IS NULL;
```

---

## Support & Resources

### 📚 Documentation Links

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Flask Integration](https://docs.authlib.org/en/latest/client/flask.html)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)

### 🆘 Getting Help

If you encounter issues:

1. **Check the logs** for specific error messages
2. **Verify your configuration** against this guide
3. **Test with a simple OAuth flow** outside the app
4. **Contact support** with specific error details

### 📞 Support Contacts

- **Technical Issues**: dev-support@facultyfinder.io
- **OAuth Setup Help**: oauth-help@facultyfinder.io
- **Security Concerns**: security@facultyfinder.io

---

## Conclusion

Google OAuth is now fully integrated with FacultyFinder! Users can:

- ✅ Sign in with their Google accounts
- ✅ Register new accounts automatically
- ✅ Access all features seamlessly
- ✅ Maintain secure authentication

### 🎯 Next Steps

1. **Test thoroughly** in development
2. **Deploy to staging** for final testing  
3. **Configure production** environment
4. **Monitor usage** and optimize as needed

### 🔄 Future Enhancements

Consider adding:
- Multiple OAuth providers (GitHub, Microsoft, etc.)
- Social login analytics
- Advanced user profile syncing
- Enterprise SSO integration

---

*Last updated: January 2025*  
*Version: 1.0.0*  
*FacultyFinder Google OAuth Integration* 