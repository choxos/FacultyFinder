# 🔐 Google OAuth Setup Guide for FacultyFinder

This guide will help you set up Google OAuth authentication for your FacultyFinder application.

## 📋 Prerequisites

- Google Cloud Console access
- FacultyFinder application running
- Access to your server's `.env` file

## 🚀 Step 1: Create Google Cloud Project

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** or select existing one
3. **Enable the Google+ API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" 
   - Click "Enable"

## 🔧 Step 2: Create OAuth 2.0 Credentials

1. **Go to "APIs & Services" > "Credentials"**
2. **Click "Create Credentials" > "OAuth 2.0 Client IDs"**
3. **Configure OAuth consent screen** (if prompted):
   - Choose "External" for public app
   - Fill in required fields:
     - App name: `FacultyFinder`
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if needed

4. **Create OAuth 2.0 Client ID**:
   - Application type: **Web application**
   - Name: `FacultyFinder OAuth`
   - Authorized redirect URIs:
     ```
     http://localhost:8008/auth/callback
     https://facultyfinder.io/auth/callback
     ```

5. **Download credentials** - you'll get:
   - Client ID (starts with numbers, ends with `.googleusercontent.com`)
   - Client Secret (random string)

## ⚙️ Step 3: Configure Environment Variables

Add these to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
SESSION_SECRET=your-random-session-secret-here
OAUTH_REDIRECT_URI=https://facultyfinder.io/auth/callback
```

### 🔑 Generate Session Secret

```bash
# Generate a secure random session secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🗄️ Step 4: Create Users Table (Optional)

If you want to store user data, create a users table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture VARCHAR(500),
    verified_email BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
```

## 🚀 Step 5: Deploy and Test

1. **Install OAuth dependencies**:
   ```bash
   pip install -r requirements_fastapi.txt
   ```

2. **Restart your FastAPI service**:
   ```bash
   sudo systemctl restart facultyfinder.service
   ```

3. **Test OAuth flow**:
   - Visit: `https://facultyfinder.io/login`
   - Click "Continue with Google"
   - Complete Google authentication
   - Should redirect back to your site

## 🧪 Testing OAuth Integration

### Local Testing:
```bash
# Test OAuth initiation
curl http://localhost:8008/auth/google

# Test user endpoint (after login)
curl http://localhost:8008/auth/user
```

### Production Testing:
- `https://facultyfinder.io/auth/google` - Should redirect to Google
- `https://facultyfinder.io/auth/user` - Should return user info (if logged in)
- `https://facultyfinder.io/auth/logout` - Should clear session

## 🛡️ Security Configuration

### For Production:

1. **Update CORS settings** in `main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://facultyfinder.io"],  # Your domain only
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

2. **Use strong session secret**:
   ```bash
   SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
   ```

3. **Set secure cookie options** (add to `main.py`):
   ```python
   app.add_middleware(
       SessionMiddleware, 
       secret_key=os.getenv("SESSION_SECRET"),
       max_age=7*24*60*60,  # 7 days
       https_only=True,      # HTTPS only in production
       same_site="lax"
   )
   ```

## 🔧 Troubleshooting

### Common Issues:

1. **"OAuth not configured" error**:
   - Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
   - Restart FastAPI service after adding credentials

2. **"redirect_uri_mismatch" error**:
   - Add your callback URL to Google Cloud Console
   - Ensure URL matches exactly (http vs https)

3. **Session not persisting**:
   - Check `SESSION_SECRET` is set
   - Verify SessionMiddleware is added to FastAPI

4. **CORS errors**:
   - Update `allow_origins` in CORS middleware
   - Ensure cookies are allowed

### Debug Commands:

```bash
# Check environment variables
grep GOOGLE /var/www/ff/.env

# Check service logs
sudo journalctl -u facultyfinder.service -f

# Test OAuth endpoints
curl -v http://localhost:8008/auth/google
```

## 📚 OAuth Flow Summary

1. User clicks "Continue with Google" on login/register page
2. App redirects to Google OAuth (`/auth/google`)
3. User authenticates with Google
4. Google redirects to callback (`/auth/callback`)
5. App extracts user info and creates/updates user record
6. App creates session and redirects to homepage
7. User is now logged in across the site

## 🎯 Next Steps

After OAuth is working:

1. **Add user profile page** (`/profile`)
2. **Add logout button** to navigation (when logged in)
3. **Personalize user experience** based on login status
4. **Add user preferences** and saved searches
5. **Implement role-based access** (if needed)

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review FastAPI service logs
3. Verify Google Cloud Console configuration
4. Test with different browsers/incognito mode

OAuth setup is complete! Users can now sign in with their Google accounts for a seamless experience. 🎉 