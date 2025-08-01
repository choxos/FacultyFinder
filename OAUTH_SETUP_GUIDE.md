# OAuth Setup Guide for FacultyFinder

This guide will walk you through setting up Google and LinkedIn OAuth authentication for your FacultyFinder application.

## Overview

FacultyFinder supports OAuth authentication with:
- **Google OAuth 2.0** - For Google account login
- **LinkedIn OAuth 2.0** - For LinkedIn account login

Both providers allow users to sign in/register without creating a separate account.

## Prerequisites

1. A Google Cloud Platform account
2. A LinkedIn Developer account
3. Your FacultyFinder application running (to get redirect URLs)

## Part 1: Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `FacultyFinder OAuth`
4. Click "Create"

### Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API" or "People API"
3. Click on "Google+ API" and click "Enable"
4. Also enable "People API" for better profile information

### Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (unless you have Google Workspace)
3. Fill in the required fields:
   - **App name**: `FacultyFinder`
   - **User support email**: Your email
   - **Developer contact email**: Your email
   - **App domain**: Your domain (e.g., `facultyfinder.io`)
   - **Authorized domains**: Add your domain
4. Click "Save and Continue"
5. Add scopes (if asked):
   - `email`
   - `profile`
   - `openid`
6. Click "Save and Continue"

### Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set the name: `FacultyFinder Web Client`
5. Add **Authorized redirect URIs**:
   ```
   http://localhost:8008/auth/google/callback
   https://yourdomain.com/auth/google/callback
   ```
6. Click "Create"
7. **IMPORTANT**: Copy the **Client ID** and **Client Secret**

## Part 2: LinkedIn OAuth Setup

### Step 1: Create LinkedIn App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click "Create App"
3. Fill in the form:
   - **App name**: `FacultyFinder`
   - **LinkedIn Company Page**: Create one or use existing
   - **Privacy policy URL**: `https://yourdomain.com/privacy`
   - **App logo**: Upload your logo
4. Click "Create app"

### Step 2: Configure App Settings

1. In your LinkedIn app dashboard, go to "Settings"
2. Note down the **Client ID** and **Client Secret**

### Step 3: Add Redirect URLs

1. Go to "Auth" tab in your LinkedIn app
2. Add **Authorized redirect URLs for your app**:
   ```
   http://localhost:8008/auth/linkedin/callback
   https://yourdomain.com/auth/linkedin/callback
   ```
3. Click "Update"

### Step 4: Request Required Permissions

1. Go to "Products" tab
2. Request access to:
   - **Sign In with LinkedIn** (for basic profile)
   - **Share on LinkedIn** (optional, for future features)
3. Wait for approval (usually instant for Sign In with LinkedIn)

## Part 3: Application Configuration

### Step 1: Environment Variables

Create or update your `.env` file in the project root:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here

# General Settings
SECRET_KEY=your_super_secret_key_for_jwt_tokens
BASE_URL=http://localhost:8008
```

### Step 2: Database Schema

Add the following columns to your `users` table if they don't exist:

```sql
-- Add OAuth provider columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS picture TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_email BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_linkedin_id ON users(linkedin_id);
```

### Step 3: Install Required Dependencies

Make sure your `requirements.txt` includes:

```txt
authlib>=1.2.1
python-jose[cryptography]>=3.3.0
httpx>=0.24.0
```

Install them:
```bash
pip install authlib python-jose[cryptography] httpx
```

## Part 4: Testing OAuth Integration

### Step 1: Start Your Application

```bash
cd webapp
uvicorn main:app --host 127.0.0.1 --port 8008 --reload
```

### Step 2: Test Google OAuth

1. Go to `http://localhost:8008/login`
2. Click "Google" button
3. You should be redirected to Google's consent screen
4. Grant permissions
5. You should be redirected back and logged in

### Step 3: Test LinkedIn OAuth

1. Go to `http://localhost:8008/login`
2. Click "LinkedIn" button
3. You should be redirected to LinkedIn's consent screen
4. Grant permissions
5. You should be redirected back and logged in

## Part 5: Production Deployment

### Step 1: Update Environment Variables

For production, update your `.env` or environment variables:

```env
BASE_URL=https://yourdomain.com
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
SECRET_KEY=a_very_secure_random_key_for_production
```

### Step 2: Update OAuth Redirect URLs

1. **Google Cloud Console**:
   - Add your production URL: `https://yourdomain.com/auth/google/callback`

2. **LinkedIn Developer Portal**:
   - Add your production URL: `https://yourdomain.com/auth/linkedin/callback`

### Step 3: SSL Certificate

Ensure your production site has a valid SSL certificate (OAuth requires HTTPS in production).

## Troubleshooting

### Common Issues

1. **"OAuth not configured" error**:
   - Check that environment variables are set correctly
   - Restart your application after setting environment variables

2. **"redirect_uri_mismatch" error**:
   - Verify redirect URLs match exactly in your OAuth app settings
   - Check for trailing slashes or protocol mismatches

3. **"invalid_client" error**:
   - Verify your Client ID and Client Secret are correct
   - Check that the OAuth application is enabled

4. **LinkedIn permissions error**:
   - Ensure you've requested and been approved for "Sign In with LinkedIn"
   - Check that your app is verified

### Debugging Tips

1. Check application logs for detailed error messages
2. Use browser developer tools to inspect network requests
3. Verify that your OAuth applications are active in the respective consoles

## Security Considerations

1. **Never commit OAuth credentials to version control**
2. **Use strong, random SECRET_KEY for JWT token signing**
3. **Always use HTTPS in production**
4. **Regularly rotate OAuth credentials**
5. **Implement proper session management**
6. **Consider implementing OAuth token refresh for long-lived sessions**

## Additional Features

### User Profile Management

The OAuth implementation automatically:
- Creates new users from OAuth profiles
- Links OAuth accounts to existing email addresses
- Updates user profiles with latest OAuth information
- Manages profile pictures from OAuth providers

### Session Management

- JWT tokens are generated for authenticated users
- Sessions are stored server-side for security
- Automatic logout functionality is available at `/auth/logout`

## Support

If you encounter issues:

1. Check the application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure OAuth applications are properly configured
4. Test with simple OAuth flows first (login/logout)

For additional help, refer to:
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [LinkedIn OAuth 2.0 Documentation](https://docs.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow) 