"""
Google OAuth2 authentication for FacultyFinder
"""

import os
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from datetime import datetime, timedelta
import httpx
import json

# OAuth Configuration
class OAuthConfig:
    """OAuth configuration manager"""
    
    def __init__(self):
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
        self.redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8008/auth/callback')
        
        if not self.google_client_id or not self.google_client_secret:
            print("⚠️  Warning: Google OAuth credentials not found. OAuth will not work.")
            print("   Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file")
    
    @property
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured"""
        return bool(self.google_client_id and self.google_client_secret)

# Initialize OAuth
oauth_config = OAuthConfig()
oauth = OAuth()

if oauth_config.is_configured:
    oauth.register(
        name='google',
        client_id=oauth_config.google_client_id,
        client_secret=oauth_config.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

class GoogleOAuthHandler:
    """Handles Google OAuth authentication flow"""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
    
    async def get_authorization_url(self, request: Request) -> str:
        """Get Google OAuth authorization URL"""
        if not oauth_config.is_configured:
            raise HTTPException(status_code=500, detail="OAuth not configured")
        
        redirect_uri = request.url_for('oauth_callback')
        return await oauth.google.authorize_redirect(request, redirect_uri)
    
    async def handle_callback(self, request: Request) -> Dict[str, Any]:
        """Handle OAuth callback and extract user info"""
        if not oauth_config.is_configured:
            raise HTTPException(status_code=500, detail="OAuth not configured")
        
        try:
            # Get access token from Google
            token = await oauth.google.authorize_access_token(request)
            
            # Get user info from Google
            user_info = token.get('userinfo')
            if not user_info:
                # If userinfo is not in token, fetch it separately
                resp = await oauth.google.parse_id_token(request, token)
                user_info = resp
            
            if not user_info:
                raise HTTPException(status_code=400, detail="Failed to get user information")
            
            # Extract user data
            user_data = {
                'google_id': user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('email_verified', False)
            }
            
            # Create or update user in database
            user = await self.create_or_update_user(user_data)
            
            # Generate JWT token for session
            access_token = self.create_access_token(user)
            
            return {
                'user': user,
                'access_token': access_token,
                'token_type': 'bearer'
            }
            
        except Exception as e:
            print(f"OAuth callback error: {e}")
            raise HTTPException(status_code=400, detail="Authentication failed")
    
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user in database"""
        if not self.db_pool:
            # Return mock user data if no database
            return {
                'id': 1,
                'email': user_data['email'],
                'name': user_data['name'],
                'google_id': user_data['google_id'],
                'picture': user_data.get('picture'),
                'created_at': datetime.utcnow().isoformat()
            }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Check if user exists
                existing_user = await conn.fetchrow(
                    "SELECT * FROM users WHERE google_id = $1 OR email = $2",
                    user_data['google_id'], user_data['email']
                )
                
                if existing_user:
                    # Update existing user
                    user = await conn.fetchrow("""
                        UPDATE users 
                        SET name = $1, picture = $2, last_login = CURRENT_TIMESTAMP
                        WHERE id = $3
                        RETURNING *
                    """, user_data['name'], user_data.get('picture'), existing_user['id'])
                else:
                    # Create new user
                    user = await conn.fetchrow("""
                        INSERT INTO users (google_id, email, name, picture, verified_email, created_at, last_login)
                        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING *
                    """, 
                    user_data['google_id'],
                    user_data['email'], 
                    user_data['name'],
                    user_data.get('picture'),
                    user_data.get('verified_email', False)
                    )
                
                return dict(user)
                
        except Exception as e:
            print(f"Database error creating/updating user: {e}")
            # Return mock user if database fails
            return {
                'id': 1,
                'email': user_data['email'],
                'name': user_data['name'],
                'google_id': user_data['google_id'],
                'picture': user_data.get('picture'),
                'created_at': datetime.utcnow().isoformat()
            }
    
    def create_access_token(self, user: Dict[str, Any]) -> str:
        """Create JWT access token for user session"""
        expires_delta = timedelta(days=7)  # Token valid for 7 days
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            'sub': str(user['id']),
            'email': user['email'],
            'name': user['name'],
            'exp': expire,
            'iat': datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(to_encode, oauth_config.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, oauth_config.secret_key, algorithms=["HS256"])
            return payload
        except JWTError:
            return None

# Global OAuth handler instance
oauth_handler = GoogleOAuthHandler()

def get_oauth_handler():
    """Get OAuth handler instance"""
    return oauth_handler

def init_oauth_handler(db_pool):
    """Initialize OAuth handler with database pool"""
    global oauth_handler
    oauth_handler = GoogleOAuthHandler(db_pool) 