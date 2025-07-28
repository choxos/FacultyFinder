#!/usr/bin/env python3
"""
Authentication and User Management System for FacultyFinder
"""

from flask import request, session, jsonify, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import bcrypt
import secrets
import json
from datetime import datetime, timedelta
import logging
from email_validator import validate_email, EmailNotValidError
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Initialize Flask-Login
login_manager = LoginManager()

class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, user_data):
        self.id = str(user_data['id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.role = user_data.get('role', 'user')
        self.is_active = user_data.get('is_active', True)
        self.email_verified = user_data.get('email_verified', False)
        self.profile_picture = user_data.get('profile_picture')
        self.institution = user_data.get('institution', '')
        self.field_of_study = user_data.get('field_of_study', '')
        self.academic_level = user_data.get('academic_level', '')
        self.bio = user_data.get('bio', '')
        self.website = user_data.get('website', '')
        self.orcid = user_data.get('orcid', '')
        self.created_at = user_data.get('created_at')
        self.last_login = user_data.get('last_login')
        self.login_count = user_data.get('login_count', 0)
        self.preferences = json.loads(user_data.get('preferences', '{}'))
    
    def get_id(self):
        return self.id
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_moderator(self):
        return self.role in ['admin', 'moderator']
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def to_dict(self):
        return {
            'id': int(self.id),
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'role': self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'profile_picture': self.profile_picture,
            'institution': self.institution,
            'field_of_study': self.field_of_study,
            'academic_level': self.academic_level,
            'bio': self.bio,
            'website': self.website,
            'orcid': self.orcid,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'login_count': self.login_count,
            'preferences': self.preferences
        }

class AuthManager:
    """Handles authentication operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            return self.get_user_by_id(int(user_id))
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    def validate_username(self, username: str) -> tuple[bool, str]:
        """Validate username"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            return False, "Username can only contain letters, numbers, dots, hyphens, and underscores"
        
        # Check if username exists
        existing_user = self.get_user_by_username(username)
        if existing_user:
            return False, "Username already exists"
        
        return True, "Username is valid"
    
    def validate_email(self, email: str) -> tuple[bool, str]:
        """Validate email address"""
        try:
            validated_email = validate_email(email)
            email = validated_email.email
            
            # Check if email exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                return False, "Email already registered"
            
            return True, "Email is valid"
        except EmailNotValidError:
            return False, "Invalid email address"
    
    def create_user(self, user_data: Dict[str, Any]) -> tuple[bool, str, Optional[User]]:
        """Create a new user account"""
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not user_data.get(field):
                    return False, f"{field.capitalize()} is required", None
            
            # Validate username
            username_valid, username_msg = self.validate_username(user_data['username'])
            if not username_valid:
                return False, username_msg, None
            
            # Validate email
            email_valid, email_msg = self.validate_email(user_data['email'])
            if not email_valid:
                return False, email_msg, None
            
            # Validate password
            password_valid, password_msg = self.validate_password(user_data['password'])
            if not password_valid:
                return False, password_msg, None
            
            # Hash password
            password_hash = self.hash_password(user_data['password'])
            
            # Create user record
            query = """
            INSERT INTO users (username, email, password_hash, first_name, last_name, 
                             institution, field_of_study, academic_level, bio, website, orcid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = [
                user_data['username'],
                user_data['email'],
                password_hash,
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                user_data.get('institution', ''),
                user_data.get('field_of_study', ''),
                user_data.get('academic_level', ''),
                user_data.get('bio', ''),
                user_data.get('website', ''),
                user_data.get('orcid', '')
            ]
            
            result = self.db.execute_query("SELECT last_insert_rowid() as user_id", 
                                         fetch_one=True) if self.db.dev_mode else None
            
            # Execute insert
            self.db.execute_query(query, params)
            
            # Get the new user
            new_user = self.get_user_by_username(user_data['username'])
            if new_user:
                self.log_user_activity(new_user.id, 'user_registered', {
                    'registration_method': 'web_form',
                    'ip_address': request.remote_addr if request else None
                })
                return True, "User created successfully", new_user
            else:
                return False, "Failed to create user", None
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, "An error occurred while creating the account", None
    
    def authenticate_user(self, username_or_email: str, password: str) -> tuple[bool, str, Optional[User]]:
        """Authenticate user login"""
        try:
            # Get user by username or email
            user = self.get_user_by_username(username_or_email) or self.get_user_by_email(username_or_email)
            
            if not user:
                return False, "Invalid username/email or password", None
            
            if not user.is_active:
                return False, "Account is deactivated", None
            
            # Verify password
            user_data = self.db.execute_query(
                "SELECT password_hash FROM users WHERE id = ?", 
                [user.id], 
                fetch_one=True
            )
            
            if not user_data or not self.verify_password(password, user_data['password_hash']):
                return False, "Invalid username/email or password", None
            
            # Update login stats
            self.update_user_login_stats(user.id)
            
            # Log activity
            self.log_user_activity(user.id, 'user_login', {
                'login_method': 'web_form',
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.user_agent.string if request else None
            })
            
            return True, "Login successful", user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, "An error occurred during login", None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            query = "SELECT * FROM users WHERE id = ? AND is_active = TRUE"
            user_data = self.db.execute_query(query, [user_id], fetch_one=True)
            return User(user_data) if user_data else None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            query = "SELECT * FROM users WHERE username = ? AND is_active = TRUE"
            user_data = self.db.execute_query(query, [username], fetch_one=True)
            return User(user_data) if user_data else None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            query = "SELECT * FROM users WHERE email = ? AND is_active = TRUE"
            user_data = self.db.execute_query(query, [email], fetch_one=True)
            return User(user_data) if user_data else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def update_user_login_stats(self, user_id: int):
        """Update user login statistics"""
        try:
            query = """
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1 
            WHERE id = ?
            """
            self.db.execute_query(query, [user_id])
        except Exception as e:
            logger.error(f"Error updating login stats: {e}")
    
    def log_user_activity(self, user_id: Optional[int], activity_type: str, activity_data: Dict[str, Any]):
        """Log user activity"""
        try:
            query = """
            INSERT INTO user_activity_log (user_id, activity_type, activity_data, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
            """
            
            params = [
                user_id,
                activity_type,
                json.dumps(activity_data),
                request.remote_addr if request else None,
                request.user_agent.string if request else None
            ]
            
            self.db.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error logging user activity: {e}")

# Decorators
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def moderator_required(f):
    """Decorator to require moderator or admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_moderator():
            flash('Moderator access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def api_auth_required(f):
    """Decorator for API authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session authentication first
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # TODO: Implement API key validation
            pass
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function 