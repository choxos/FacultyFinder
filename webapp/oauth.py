"""
Google and LinkedIn OAuth2 authentication for FacultyFinder
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
        # Google OAuth
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        # LinkedIn OAuth
        self.linkedin_client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.linkedin_client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        
        # General settings
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
        self.base_url = os.getenv('BASE_URL', 'http://localhost:8008')
        
        # Check configuration and warn about missing credentials
        missing_credentials = []
        if not self.google_client_id or not self.google_client_secret:
            missing_credentials.append("Google (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)")
        if not self.linkedin_client_id or not self.linkedin_client_secret:
            missing_credentials.append("LinkedIn (LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET)")
            
        if missing_credentials:
            print("⚠️  Warning: OAuth credentials not found for:")
            for cred in missing_credentials:
                print(f"   - {cred}")
            print("   OAuth will not work for providers with missing credentials.")
    
    @property
    def google_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(self.google_client_id and self.google_client_secret)
    
    @property
    def linkedin_configured(self) -> bool:
        """Check if LinkedIn OAuth is properly configured"""
        return bool(self.linkedin_client_id and self.linkedin_client_secret)
    
    @property
    def is_configured(self) -> bool:
        """Check if any OAuth provider is properly configured"""
        return self.google_configured or self.linkedin_configured

# Initialize OAuth
oauth_config = OAuthConfig()
oauth = OAuth()

# Register Google OAuth
if oauth_config.google_configured:
    oauth.register(
        name='google',
        client_id=oauth_config.google_client_id,
        client_secret=oauth_config.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# Register LinkedIn OAuth
if oauth_config.linkedin_configured:
    oauth.register(
        name='linkedin',
        client_id=oauth_config.linkedin_client_id,
        client_secret=oauth_config.linkedin_client_secret,
        access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
        access_token_params=None,
        authorize_url='https://www.linkedin.com/oauth/v2/authorization',
        authorize_params=None,
        api_base_url='https://api.linkedin.com/v2/',
        client_kwargs={
            'scope': 'r_liteprofile r_emailaddress'
        }
    )

class OAuthHandler:
    """Handles OAuth authentication flow for multiple providers"""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
    
    async def get_authorization_url(self, request: Request, provider: str) -> str:
        """Get OAuth authorization URL for specified provider"""
        if provider == 'google' and not oauth_config.google_configured:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        elif provider == 'linkedin' and not oauth_config.linkedin_configured:
            raise HTTPException(status_code=500, detail="LinkedIn OAuth not configured")
        elif provider not in ['google', 'linkedin']:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        redirect_uri = request.url_for('oauth_callback', provider=provider)
        client = getattr(oauth, provider)
        return await client.authorize_redirect(request, redirect_uri)
    
    async def handle_callback(self, request: Request, provider: str) -> Dict[str, Any]:
        """Handle OAuth callback and extract user info"""
        if provider == 'google' and not oauth_config.google_configured:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        elif provider == 'linkedin' and not oauth_config.linkedin_configured:
            raise HTTPException(status_code=500, detail="LinkedIn OAuth not configured")
        elif provider not in ['google', 'linkedin']:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        try:
            if provider == 'google':
                return await self._handle_google_callback(request)
            elif provider == 'linkedin':
                return await self._handle_linkedin_callback(request)
            
        except Exception as e:
            print(f"OAuth callback error for {provider}: {e}")
            raise HTTPException(status_code=400, detail="Authentication failed")
    
    async def _handle_google_callback(self, request: Request) -> Dict[str, Any]:
        """Handle Google OAuth callback"""
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
            'provider': 'google',
            'provider_id': user_info.get('sub'),
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
    
    async def _handle_linkedin_callback(self, request: Request) -> Dict[str, Any]:
        """Handle LinkedIn OAuth callback"""
        # Get access token from LinkedIn
        token = await oauth.linkedin.authorize_access_token(request)
        
        # Get user profile info
        async with httpx.AsyncClient() as client:
            # Get profile info
            profile_response = await client.get(
                'https://api.linkedin.com/v2/people/~?(projection=(id,firstName,lastName,profilePicture(displayImage~:playableStreams)))',
                headers={'Authorization': f'Bearer {token["access_token"]}'}
            )
            profile_data = profile_response.json()
            
            # Get email info
            email_response = await client.get(
                'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                headers={'Authorization': f'Bearer {token["access_token"]}'}
            )
            email_data = email_response.json()
        
        if not profile_data or 'id' not in profile_data:
            raise HTTPException(status_code=400, detail="Failed to get LinkedIn user information")
        
        # Extract email
        email = None
        if email_data and 'elements' in email_data and email_data['elements']:
            email = email_data['elements'][0].get('handle~', {}).get('emailAddress')
        
        # Extract profile picture
        picture = None
        if 'profilePicture' in profile_data and 'displayImage~' in profile_data['profilePicture']:
            images = profile_data['profilePicture']['displayImage~'].get('elements', [])
            if images:
                # Get the largest image
                picture = max(images, key=lambda x: x.get('data', {}).get('com.linkedin.digitalmedia.mediaartifact.StillImage', {}).get('storageSize', 0))
                picture = picture.get('identifiers', [{}])[0].get('identifier')
        
        # Extract user data
        user_data = {
            'provider': 'linkedin',
            'provider_id': profile_data['id'],
            'email': email,
            'name': f"{profile_data.get('firstName', {}).get('localized', {}).get('en_US', '')} {profile_data.get('lastName', {}).get('localized', {}).get('en_US', '')}".strip(),
            'given_name': profile_data.get('firstName', {}).get('localized', {}).get('en_US', ''),
            'family_name': profile_data.get('lastName', {}).get('localized', {}).get('en_US', ''),
            'picture': picture,
            'verified_email': bool(email)  # LinkedIn emails are generally verified
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
    
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user in database"""
        provider = user_data.get('provider')
        provider_id = user_data.get('provider_id')
        
        if not self.db_pool:
            # Return mock user data if no database
            return {
                'id': 1,
                'email': user_data['email'],
                'name': user_data['name'],
                'provider': provider,
                'provider_id': provider_id,
                'picture': user_data.get('picture'),
                'created_at': datetime.utcnow().isoformat()
            }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Check if user exists by provider ID or email
                if provider == 'google':
                    existing_user = await conn.fetchrow(
                        "SELECT * FROM users WHERE google_id = $1 OR email = $2",
                        provider_id, user_data['email']
                    )
                elif provider == 'linkedin':
                    existing_user = await conn.fetchrow(
                        "SELECT * FROM users WHERE linkedin_id = $1 OR email = $2",
                        provider_id, user_data['email']
                    )
                else:
                    existing_user = await conn.fetchrow(
                        "SELECT * FROM users WHERE email = $1",
                        user_data['email']
                    )
                
                if existing_user:
                    # Update existing user with new provider info
                    if provider == 'google':
                        user = await conn.fetchrow("""
                            UPDATE users 
                            SET name = $1, picture = $2, google_id = $3, last_login = CURRENT_TIMESTAMP
                            WHERE id = $4
                            RETURNING *
                        """, user_data['name'], user_data.get('picture'), provider_id, existing_user['id'])
                    elif provider == 'linkedin':
                        user = await conn.fetchrow("""
                            UPDATE users 
                            SET name = $1, picture = $2, linkedin_id = $3, last_login = CURRENT_TIMESTAMP
                            WHERE id = $4
                            RETURNING *
                        """, user_data['name'], user_data.get('picture'), provider_id, existing_user['id'])
                    else:
                        user = await conn.fetchrow("""
                            UPDATE users 
                            SET name = $1, picture = $2, last_login = CURRENT_TIMESTAMP
                            WHERE id = $3
                            RETURNING *
                        """, user_data['name'], user_data.get('picture'), existing_user['id'])
                else:
                    # Create new user
                    if provider == 'google':
                        user = await conn.fetchrow("""
                            INSERT INTO users (google_id, email, name, picture, verified_email, created_at, last_login)
                            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            RETURNING *
                        """, 
                        provider_id,
                        user_data['email'], 
                        user_data['name'],
                        user_data.get('picture'),
                        user_data.get('verified_email', False)
                        )
                    elif provider == 'linkedin':
                        user = await conn.fetchrow("""
                            INSERT INTO users (linkedin_id, email, name, picture, verified_email, created_at, last_login)
                            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            RETURNING *
                        """, 
                        provider_id,
                        user_data['email'], 
                        user_data['name'],
                        user_data.get('picture'),
                        user_data.get('verified_email', False)
                        )
                    else:
                        user = await conn.fetchrow("""
                            INSERT INTO users (email, name, picture, verified_email, created_at, last_login)
                            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            RETURNING *
                        """, 
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
                'provider': provider,
                'provider_id': provider_id,
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
oauth_handler = OAuthHandler()

def get_oauth_handler():
    """Get OAuth handler instance"""
    return oauth_handler

def init_oauth_handler(db_pool):
    """Initialize OAuth handler with database pool"""
    global oauth_handler
    oauth_handler = OAuthHandler(db_pool) 