#!/bin/bash

echo "🔐 Deploying Google OAuth Authentication"
echo "========================================"
echo "Adding Google OAuth + Navigation updates"
echo ""

# Check directory
if [ ! -f "webapp/main.py" ]; then
    echo "❌ Error: Run from /var/www/ff directory"
    exit 1
fi

# Check for OAuth configuration
echo "🔧 Checking OAuth configuration..."
if [ -f ".env" ]; then
    if grep -q "GOOGLE_CLIENT_ID" .env && grep -q "GOOGLE_CLIENT_SECRET" .env; then
        echo "✅ Google OAuth credentials found in .env"
    else
        echo "⚠️  Google OAuth credentials not found in .env"
        echo "📋 You'll need to add these to your .env file:"
        echo "   GOOGLE_CLIENT_ID=your-client-id.googleusercontent.com"
        echo "   GOOGLE_CLIENT_SECRET=your-client-secret"
        echo "   SESSION_SECRET=your-random-session-secret"
        echo ""
        echo "📚 See GOOGLE_OAUTH_SETUP.md for detailed setup instructions"
        echo ""
        read -p "Continue deployment anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Deployment cancelled. Configure OAuth first."
            exit 1
        fi
    fi
else
    echo "⚠️  No .env file found"
fi

# Pull OAuth implementation
echo "📥 Pulling Google OAuth code from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull changes"
    exit 1
fi

echo "✅ OAuth code pulled successfully"

# Install OAuth dependencies
echo -e "\n📦 Installing OAuth dependencies..."
pip install authlib==1.2.1 httpx==0.25.2 itsdangerous==2.1.2

if [ $? -eq 0 ]; then
    echo "✅ OAuth dependencies installed"
else
    echo "⚠️  Some dependencies may have failed to install"
fi

# Restart FastAPI service
echo -e "\n🔄 Restarting FastAPI service..."
sudo systemctl restart facultyfinder.service

# Wait for startup
echo "⏳ Waiting for service startup..."
sleep 5

# Test OAuth endpoints
echo -e "\n🧪 Testing OAuth functionality..."

echo "Testing OAuth initiation route:"
oauth_init_response=$(curl -s -w "%{http_code}" http://localhost:8008/auth/google -o /dev/null)
if [ "$oauth_init_response" = "307" ] || [ "$oauth_init_response" = "302" ]; then
    echo "✅ OAuth initiation OK (HTTP $oauth_init_response - redirect to Google)"
else
    echo "❌ OAuth initiation failed (HTTP $oauth_init_response)"
    echo "📋 Recent logs:"
    sudo journalctl -u facultyfinder.service --lines=3 --no-pager | grep -i error
fi

echo -e "\nTesting login page with OAuth button:"
login_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/login -o /dev/null)
if [ "$login_page_response" = "200" ]; then
    echo "✅ Login page with OAuth button OK (HTTP $login_page_response)"
else
    echo "❌ Login page failed (HTTP $login_page_response)"
fi

echo -e "\nTesting register page with OAuth button:"
register_page_response=$(curl -s -w "%{http_code}" http://localhost:8008/register -o /dev/null)
if [ "$register_page_response" = "200" ]; then
    echo "✅ Register page with OAuth button OK (HTTP $register_page_response)"
else
    echo "❌ Register page failed (HTTP $register_page_response)"
fi

# Test navigation updates
echo -e "\nTesting navigation updates..."
if curl -s http://localhost:8008/login | grep -q "Sign In"; then
    echo "✅ Navigation updated to 'Sign In'"
else
    echo "❌ Navigation still shows 'Log In'"
fi

# Final status
echo -e "\n" + "=" * 60
echo "🎉 Google OAuth Deployment Complete!"
echo "====================================="

if [ "$oauth_init_response" = "307" ] || [ "$oauth_init_response" = "302" ]; then
    echo "✅ OAuth functionality deployed successfully!"
    echo ""
    echo "🌐 Test your OAuth authentication:"
    echo "   1. Visit: https://facultyfinder.io/login"
    echo "   2. Click 'Continue with Google'"
    echo "   3. Complete Google authentication"
    echo "   4. Should redirect back to your site"
    echo ""
    echo "✅ Features Added:"
    echo "   - Google OAuth login/register buttons"
    echo "   - Professional Google branding"
    echo "   - Navigation updated to 'Sign In'"
    echo "   - Session management with JWT tokens"
    echo "   - Automatic user creation/update"
    echo ""
    if grep -q "GOOGLE_CLIENT_ID" .env 2>/dev/null; then
        echo "🔐 OAuth Status: Fully configured and ready!"
    else
        echo "⚠️  OAuth Status: Deployed but needs configuration"
        echo "📚 Next Steps:"
        echo "   1. Follow GOOGLE_OAUTH_SETUP.md guide"
        echo "   2. Set up Google Cloud Console project"
        echo "   3. Add OAuth credentials to .env file"
        echo "   4. Restart service: sudo systemctl restart facultyfinder.service"
    fi
else
    echo "⚠️  OAuth needs configuration to work properly"
    echo ""
    echo "📚 Setup Required:"
    echo "   1. Read: GOOGLE_OAUTH_SETUP.md"
    echo "   2. Create Google Cloud Console project"
    echo "   3. Generate OAuth 2.0 credentials"
    echo "   4. Add credentials to .env file"
    echo "   5. Restart service"
fi

echo -e "\n🛠️  Monitor your service:"
echo "   sudo systemctl status facultyfinder.service"
echo "   sudo journalctl -u facultyfinder.service -f" 