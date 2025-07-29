#!/usr/bin/env python3
"""
FacultyFinder Web Application
Flask-based web interface for discovering academic faculty and their research
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
import functools
from functools import wraps
import hashlib
import gzip
import io
import psutil
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, g, make_response, redirect, url_for, flash, abort, send_from_directory
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional

# Authentication imports
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import re
from email_validator import validate_email, EmailNotValidError

# Google OAuth imports
from authlib.integrations.flask_client import OAuth
import requests

# Performance monitoring
import time
import psutil

# CV Analysis
from cv_analyzer import CVAnalyzer, allowed_file, validate_file_size

# Email functionality
try:
    from flask_mail import Mail, Message
    MAIL_AVAILABLE = True
except ImportError:
    MAIL_AVAILABLE = False
    logging.warning("Flask-Mail not installed. Email functionality disabled.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'development-key-change-in-production'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize OAuth
oauth = OAuth(app)

# Google OAuth configuration
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, first_name=None, last_name=None, role='user', 
                 is_active=True, email_verified=False, institution=None, field_of_study=None,
                 academic_level=None, bio=None, website=None, orcid=None):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.is_active = is_active
        self.email_verified = email_verified
        self.institution = institution
        self.field_of_study = field_of_study
        self.academic_level = academic_level
        self.bio = bio
        self.website = website
        self.orcid = orcid
    
    def get_id(self):
        return str(self.id)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_moderator(self):
        return self.role in ['admin', 'moderator']
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.execute(
            "SELECT * FROM users WHERE id = ? AND is_active = 1", 
            (user_id,)
        )
        user_data = cursor.fetchone()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                is_active=user_data['is_active'],
                email_verified=user_data['email_verified'],
                institution=user_data['institution'],
                field_of_study=user_data['field_of_study'],
                academic_level=user_data['academic_level'],
                bio=user_data['bio'],
                website=user_data['website'],
                orcid=user_data['orcid']
            )
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
    
    return None

# Performance configuration
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # 1 day for static files
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty printing for performance

# Email configuration
if MAIL_AVAILABLE:
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Email addresses
    app.config['SUPPORT_EMAIL'] = os.getenv('SUPPORT_EMAIL', 'support@facultyfinder.io')
    app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL', 'admin@facultyfinder.io')
    
    # Initialize Flask-Mail
    mail = Mail(app)
else:
    mail = None

# Database configuration
DEV_DB = '../database/facultyfinder_dev.db'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'facultyfinder_dev.db')

def test_database_connection():
    """Test database connection and log basic info"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed!")
            return False
        
        # Test basic queries
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ Database connected. Tables: {tables}")
        
        # Count data
        if 'universities' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM universities")
            uni_count = cursor.fetchone()[0]
            logger.info(f"Universities in DB: {uni_count}")
        
        if 'professors' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM professors")
            prof_count = cursor.fetchone()[0]
            logger.info(f"Professors in DB: {prof_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

# Enhanced connection pool implementation for SQLite
class SQLiteConnectionPool:
    def __init__(self, database_path, max_connections=20):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connections = []
        self.in_use = set()
        self.lock = threading.Lock()
        self.connection_timeout = 30.0  # Connection timeout in seconds
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.connection_metadata = {}  # Store connection metadata separately
        
        # Pre-create optimized connections
        for _ in range(min(5, max_connections)):  # Start with 5 connections
            conn = self._create_optimized_connection()
            if conn:
                self.connections.append(conn)
                self.connection_metadata[id(conn)] = {'created_at': time.time()}
    
    def _create_optimized_connection(self):
        """Create a highly optimized database connection"""
        try:
            conn = sqlite3.connect(
                self.database_path, 
                check_same_thread=False,
                timeout=self.connection_timeout,
                isolation_level=None  # Autocommit mode for better performance
            )
            conn.row_factory = sqlite3.Row
            
            # Advanced SQLite optimizations
            optimizations = [
                "PRAGMA journal_mode=WAL",
                "PRAGMA synchronous=NORMAL",
                "PRAGMA cache_size=-64000",  # 64MB cache
                "PRAGMA temp_store=MEMORY",
                "PRAGMA mmap_size=268435456",  # 256MB mmap
                "PRAGMA page_size=4096",
                "PRAGMA wal_autocheckpoint=1000",
                "PRAGMA busy_timeout=10000",  # 10 second timeout
                "PRAGMA optimize",
            ]
            
            for pragma in optimizations:
                try:
                    conn.execute(pragma)
                except Exception as e:
                    logger.warning(f"Failed to apply {pragma}: {e}")
            
            # Mark connection creation time for cleanup in metadata
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    def get_connection(self):
        """Get connection with automatic cleanup and health checks"""
        with self.lock:
            # Periodic cleanup of old connections
            current_time = time.time()
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_stale_connections()
                self.last_cleanup = current_time
            
            # Return existing healthy connection if available
            while self.connections:
                conn = self.connections.pop()
                # Health check - verify connection is still valid
                try:
                    conn.execute("SELECT 1").fetchone()
                    self.in_use.add(conn)
                    logger.debug(f"Reusing existing connection from pool. Available: {len(self.connections)}, In use: {len(self.in_use)}")
                    return conn
                except Exception as e:
                    # Connection is invalid, try next one
                    logger.warning(f"Removing invalid connection from pool: {e}")
                    try:
                        conn.close()
                        self.connection_metadata.pop(id(conn), None)
                    except:
                        pass
                    continue
            
            # Create new connection if under limit
            if len(self.in_use) < self.max_connections:
                logger.debug(f"Creating new connection. In use: {len(self.in_use)}, Max: {self.max_connections}")
                conn = self._create_optimized_connection()
                if conn:
                    self.connection_metadata[id(conn)] = {'created_at': time.time()}
                    self.in_use.add(conn)
                    logger.debug(f"Created new connection successfully")
                    return conn
                else:
                    logger.error("Failed to create new database connection")
        
        # Return None if no connections available
        logger.error(f"No database connections available. In use: {len(self.in_use)}, Available: {len(self.connections)}")
        return None
    
    def return_connection(self, conn):
        """Return connection to pool with health check"""
        with self.lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
                # Health check before returning to pool
                try:
                    conn.execute("SELECT 1").fetchone()
                    self.connections.append(conn)
                except:
                    # Connection is invalid, close it
                    try:
                        conn.close()
                        # Remove metadata for closed connection
                        self.connection_metadata.pop(id(conn), None)
                    except:
                        pass
    
    def _cleanup_stale_connections(self):
        """Remove old or stale connections"""
        current_time = time.time()
        max_age = 3600  # 1 hour max connection age
        
        # Clean up connections in pool
        healthy_connections = []
        for conn in self.connections:
            try:
                conn_id = id(conn)
                conn_created = self.connection_metadata.get(conn_id, {}).get('created_at', 0)
                if (current_time - conn_created) < max_age:
                    conn.execute("SELECT 1").fetchone()
                    healthy_connections.append(conn)
                else:
                    conn.close()
                    # Remove metadata for closed connection
                    self.connection_metadata.pop(conn_id, None)
            except:
                try:
                    conn.close()
                    # Remove metadata for closed connection
                    self.connection_metadata.pop(id(conn), None)
                except:
                    pass
        
        self.connections = healthy_connections
        logger.debug(f"Connection pool cleanup: {len(healthy_connections)} healthy connections remaining")
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        with self.lock:
            for conn in self.connections + list(self.in_use):
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()
            self.in_use.clear()
            self.connection_metadata.clear()
            
    def get_pool_stats(self):
        """Get connection pool statistics"""
        with self.lock:
            return {
                'total_connections': len(self.connections) + len(self.in_use),
                'available_connections': len(self.connections),
                'in_use_connections': len(self.in_use),
                'max_connections': self.max_connections
            }

# Global connection pool
db_pool = SQLiteConnectionPool(DATABASE_PATH)

# Simple user context for templates
@app.context_processor
def inject_user():
    """Inject current_user context for templates"""
    # Flask-Login provides current_user automatically
    # Just return an empty dict since current_user is already available
    return dict()

def get_db_connection():
    """Get database connection from pool"""
    if not hasattr(g, 'db_conn'):
        g.db_conn = db_pool.get_connection()
        if not g.db_conn:
            logger.error("Failed to get database connection from pool")
            return None
    return g.db_conn

@app.teardown_appcontext
def close_db_connection(error):
    """Return connection to pool after request"""
    if hasattr(g, 'db_conn') and g.db_conn:
        try:
            db_pool.return_connection(g.db_conn)
            logger.debug("Database connection returned to pool")
        except Exception as e:
            logger.warning(f"Error returning connection to pool: {e}")
        finally:
            # Clear the connection from g to prevent reuse
            g.db_conn = None

# Performance monitoring decorator
def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if duration > 500:  # Log slow requests
                logger.warning(f"Slow request: {func.__name__} took {duration:.2f}ms")
            
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

# Simple in-memory cache for frequently accessed data
class SimpleCache:
    def __init__(self, default_timeout=300):
        self.cache = {}
        self.timeouts = {}
        self.default_timeout = default_timeout
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                if time.time() < self.timeouts[key]:
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.timeouts[key]
            return None
    
    def set(self, key, value, timeout=None):
        with self.lock:
            self.cache[key] = value
            self.timeouts[key] = time.time() + (timeout or self.default_timeout)
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.timeouts.clear()

# Global cache instance
cache = SimpleCache()

def cached(timeout=300, key_func=None):
    """Caching decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

# HTTP compression middleware 
def compress_response(response):
    """Compress response if beneficial, excluding HTML pages and API routes"""
    try:
        # Skip compression for specific routes and content types
        if (hasattr(request, 'path') and 
            (request.path.startswith('/professor/') or 
             request.path.startswith('/university/') or
             request.path.startswith('/faculties') or
             request.path.startswith('/universities') or
             request.path.startswith('/countries') or
             request.path.startswith('/country/') or
             request.path.startswith('/api/') or
             request.path.startswith('/auth/') or
             request.path.startswith('/admin/') or
             request.path.startswith('/static/'))):
            return response
            
        # Skip compression for HTML content types
        content_type = response.content_type
        if (content_type and 
            ('text/html' in content_type or 
             'text/plain' in content_type or
             'application/json' in content_type)):
            return response
        
        # Only compress if we have actual data and it's compressible
        if (hasattr(response, 'data') and response.data and 
            len(response.data) > 1024 and  # Only compress if > 1KB
            'gzip' in request.headers.get('Accept-Encoding', '')):
            
            # Compress the data
            import gzip
            import io
            
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gzip_file:
                gzip_file.write(response.data)
            
            response.data = buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(response.data)
            
    except Exception as e:
        logger.warning(f"Compression failed: {e}")
        # Return uncompressed response on error
    
    return response

# Add caching and compression headers
@app.after_request
def add_performance_headers(response):
    """Add performance and security headers"""
    # Caching headers for static content
    if request.endpoint and 'static' in request.endpoint:
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
    else:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Compression - but skip for API routes to avoid JSON parsing issues
    if (response.mimetype.startswith('text/') or response.mimetype == 'application/json') and \
       not (request.path.startswith('/api/') or 'api' in (request.endpoint or '')):
        response = compress_response(response)
    
    return response

def send_contact_confirmation(user_email, user_name, subject, message):
    """Send confirmation email to user"""
    if not mail:
        logger.warning("Email not configured. Cannot send confirmation.")
        return False
    
    try:
        msg = Message(
            subject="Thank you for contacting FacultyFinder",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email]
        )
        
        # Try to use HTML template, fallback to plain text
        try:
            msg.html = render_template('emails/contact_confirmation.html',
                                     name=user_name,
                                     subject=subject,
                                     message=message)
        except:
            msg.body = f"""Dear {user_name},

Thank you for contacting FacultyFinder! We have received your message regarding "{subject}" and will respond within 24 hours.

Your message:
{message}

If you have urgent questions, please contact us directly at {app.config['SUPPORT_EMAIL']}.

Best regards,
The FacultyFinder Team

---
FacultyFinder - Connecting researchers worldwide
https://facultyfinder.io"""
        
        mail.send(msg)
        logger.info(f"Confirmation email sent to {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending confirmation email: {e}")
        return False

def notify_support_team(user_email, user_name, subject, message):
    """Send notification to support team"""
    if not mail:
        logger.warning("Email not configured. Cannot notify support team.")
        return False
    
    try:
        msg = Message(
            subject=f"New Contact Form Submission: {subject}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['SUPPORT_EMAIL']]
        )
        
        msg.body = f"""New contact form submission:

From: {user_name} ({user_email})
Subject: {subject}

Message:
{message}

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        mail.send(msg)
        logger.info(f"Support notification sent for contact from {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending support notification: {e}")
        return False

@cached(timeout=1800)  # Cache for 30 minutes
@monitor_performance
def get_summary_statistics():
    """Get platform summary statistics with reliable simple connection"""
    try:
        # Use direct sqlite3 connection for cached function reliability
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Basic optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA busy_timeout=30000")
        
        try:
            # Count professors
            cursor = conn.execute("SELECT COUNT(*) FROM professors")
            professor_count = cursor.fetchone()[0]
            logger.info(f"Professor count: {professor_count}")
            
            # Count only universities that have at least one faculty member
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT u.university_code) 
                FROM universities u 
                INNER JOIN professors p ON u.university_code = p.university_code
            """)
            university_count = cursor.fetchone()[0]
            logger.info(f"Universities with faculty: {university_count}")
            
            # Count publications
            cursor = conn.execute("SELECT COUNT(*) FROM publications")
            publication_count = cursor.fetchone()[0]
            logger.info(f"Publication count: {publication_count}")
            
            # Count countries that have universities with faculty
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT u.country) 
                FROM universities u 
                INNER JOIN professors p ON u.university_code = p.university_code
                WHERE u.country IS NOT NULL AND u.country != ''
            """)
            countries_count = cursor.fetchone()[0]
            logger.info(f"Countries with faculty: {countries_count}")
            
            stats = {
                'total_professors': professor_count,
                'total_universities': university_count,
                'total_publications': publication_count,
                'countries_count': countries_count
            }
            
            # Close simple connection
            conn.close()
            
            logger.info(f"Final homepage statistics (universities with faculty only): {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error executing statistics queries: {e}")
            try:
                conn.close()
            except:
                pass
            return {
                'total_professors': 0,
                'total_universities': 0,
                'total_publications': 0,
                'countries_count': 0
            }
        
    except Exception as e:
        logger.error(f"Error getting summary statistics: {e}")
        return {
            'total_professors': 0,
            'total_universities': 0,
            'total_publications': 0,
            'countries_count': 0
        }

@cached(timeout=1800)  # Cache for 30 minutes
@monitor_performance
def get_top_universities():
    """Get top universities by professor count (cached) - only show universities with faculty"""
    try:
        # Use direct sqlite3 connection for cached function reliability
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Basic optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA busy_timeout=30000")
        
        # Only show universities that have at least one faculty member
        query = """
        SELECT u.university_code, u.name, u.city, u.province_state, u.country, u.address, u.website,
               u.university_type, u.languages, u.year_established,
               COUNT(p.id) as professor_count
        FROM universities u
        INNER JOIN professors p ON u.university_code = p.university_code
        GROUP BY u.university_code, u.name, u.city, u.province_state, u.country, u.address, u.website,
                 u.university_type, u.languages, u.year_established
        HAVING COUNT(p.id) > 0
        ORDER BY professor_count DESC, u.name
        LIMIT 5
        """
        
        cursor = conn.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        
        # For cached functions, use simple connection and close it
        conn.close()
        
        logger.info(f"Successfully retrieved {len(results)} top universities (only those with faculty)")
        return results
        
    except Exception as e:
        logger.error(f"Error getting top universities: {e}")
        logger.error(f"Database path: {DATABASE_PATH}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

@cached(timeout=3600)  # Cache for 1 hour since this data rarely changes
@monitor_performance
def get_available_university_filters():
    """Get available filter options from universities with faculty (cached and optimized)"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return {
                'countries': [],
                'provinces_by_country': {},
                'types': [],
                'languages': []
            }
        
        # Optimized batch query to reduce database round trips
        query = """
        WITH university_data AS (
            SELECT DISTINCT u.country, u.province_state, u.university_type, u.languages
            FROM universities u 
            INNER JOIN professors p ON u.university_code = p.university_code 
            WHERE u.country IS NOT NULL AND u.country != ''
        )
        SELECT 
            array_agg(DISTINCT country) as countries,
            array_agg(DISTINCT province_state) as provinces, 
            array_agg(DISTINCT university_type) as types,
            array_agg(DISTINCT languages) as languages
        FROM university_data
        """
        
        # Fallback to individual queries for SQLite compatibility
        # Get countries with faculty
        cursor = conn.execute('''
            SELECT DISTINCT u.country 
            FROM universities u 
            INNER JOIN professors p ON u.university_code = p.university_code 
            WHERE u.country IS NOT NULL AND u.country != ''
            ORDER BY u.country
        ''')
        countries = [row[0] for row in cursor.fetchall()]
        
        # Get provinces by country in a single query
        cursor = conn.execute('''
            SELECT u.country, u.province_state 
            FROM universities u 
            INNER JOIN professors p ON u.university_code = p.university_code 
            WHERE u.country IS NOT NULL AND u.country != ''
            AND u.province_state IS NOT NULL AND u.province_state != ''
            GROUP BY u.country, u.province_state
            ORDER BY u.country, u.province_state
        ''')
        provinces_by_country = {}
        for row in cursor.fetchall():
            country, province = row
            if country not in provinces_by_country:
                provinces_by_country[country] = []
            provinces_by_country[country].append(province)
        
        # Get university types
        cursor = conn.execute('''
            SELECT DISTINCT u.university_type 
            FROM universities u 
            INNER JOIN professors p ON u.university_code = p.university_code 
            WHERE u.university_type IS NOT NULL AND u.university_type != ''
            ORDER BY u.university_type
        ''')
        types = [row[0] for row in cursor.fetchall()]
        
        # Get languages with optimized parsing
        cursor = conn.execute('''
            SELECT DISTINCT u.languages 
            FROM universities u 
            INNER JOIN professors p ON u.university_code = p.university_code 
            WHERE u.languages IS NOT NULL AND u.languages != ''
        ''')
        languages = set()
        for row in cursor.fetchall():
            language_string = row[0]
            if language_string:
                # Optimized language parsing
                if ';' in language_string:
                    for lang in language_string.split(';'):
                        lang = lang.strip()
                        if lang:
                            languages.add(lang)
                elif ',' in language_string:
                    for lang in language_string.split(','):
                        lang = lang.strip()
                        if lang:
                            languages.add(lang)
                else:
                    languages.add(language_string.strip())
        
        languages = sorted(list(languages))
        
        # Only close if we created a direct connection
        if hasattr(conn, '_direct_connection'):
            conn.close()
        
        return {
            'countries': countries,
            'provinces_by_country': provinces_by_country,
            'types': types,
            'languages': languages
        }
        
    except Exception as e:
        logger.error(f"Error getting university filters: {e}")
        return {
            'countries': [],
            'provinces_by_country': {},
            'types': [],
            'languages': []
        }

def generate_search_cache_key(search, country, province, uni_type, language, sort_by):
    """Generate cache key for university search"""
    params = f"{search}:{country}:{province}:{uni_type}:{language}:{sort_by}"
    return f"university_search:{hashlib.md5(params.encode()).hexdigest()}"

@monitor_performance
def search_universities_with_filters(search='', country='', province='', uni_type='', language='', sort_by='faculty_count'):
    """Search universities with filters applied (with smart caching)"""
    # Check cache first
    cache_key = generate_search_cache_key(search, country, province, uni_type, language, sort_by)
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        conn = get_optimized_connection()
        if not conn:
            return []
        
        # Optimized query with JOINs for better performance
        base_query = """
        SELECT u.university_code, u.name, u.city, u.province_state, u.country, u.address, u.website,
               u.university_type, u.languages, u.year_established,
               COUNT(p.id) as professor_count,
               COALESCE(COUNT(DISTINCT CASE WHEN p.department IS NOT NULL AND p.department != '' THEN p.department END), 0) as department_count
        FROM universities u
        LEFT JOIN professors p ON u.university_code = p.university_code
        """
        
        conditions = []
        params = []
        
        # Add filters dynamically with index-friendly conditions
        if search:
            conditions.append("(u.name LIKE ? OR u.city LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if country:
            conditions.append("u.country = ?")
            params.append(country)
        
        if province:
            conditions.append("u.province_state = ?")  # Changed from LIKE for better index usage
            params.append(province)
        
        if uni_type:
            conditions.append("u.university_type = ?")
            params.append(uni_type)
        
        if language:
            conditions.append("u.languages LIKE ?")
            params.append(f'%{language}%')
        
        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        
        # Add GROUP BY and ORDER BY with proper indexing
        group_clause = " GROUP BY u.university_code, u.name, u.city, u.province_state, u.country, u.address, u.website, u.university_type, u.languages, u.year_established"
        
        # Optimized sorting options
        order_clauses = {
            'faculty_count': 'ORDER BY professor_count DESC, u.name',
            'name': 'ORDER BY u.name',
            'year': 'ORDER BY u.year_established DESC NULLS LAST',
            'country': 'ORDER BY u.country, u.name'
        }
        order_clause = " " + order_clauses.get(sort_by, order_clauses['faculty_count'])
        
        # Complete query
        final_query = base_query + where_clause + group_clause + order_clause
        
        cursor = conn.execute(final_query, params)
        results = []
        for row in cursor.fetchall():
            results.append({
                'university_code': row[0],
                'name': row[1],
                'city': row[2],
                'province_state': row[3],
                'country': row[4],
                'address': row[5],
                'website': row[6],
                'university_type': row[7],
                'languages': row[8],
                'year_established': row[9],
                'professor_count': row[10],
                'department_count': row[11]
            })
        
        # Only close if we created a direct connection
        if hasattr(conn, '_direct_connection'):
            conn.close()
        
        # Cache the result for 30 minutes with longer timeout for stable data
        cache.set(cache_key, results, timeout=1800)
        return results
        
    except Exception as e:
        logger.error(f"Error searching universities: {e}")
        return []

@app.route('/')
@monitor_performance
def index():
    """Homepage with summary statistics and top universities"""
    try:
        stats = get_summary_statistics()
        
        # Validate that we got real stats, not fallback zeros
        if all(value == 0 for value in stats.values()):
            logger.warning("Received zero stats - this might indicate a database issue")
        
        # Only get top universities if we have data
        if stats.get('total_universities', 0) > 0:
            top_universities = get_top_universities()
        else:
            top_universities = []
        
        return render_template('index.html', 
                             stats=stats,
                             top_universities=top_universities)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        
        # Try to get stats one more time before falling back
        try:
            stats = get_summary_statistics()
            logger.info("Recovered stats on retry")
            return render_template('index.html', 
                                 stats=stats,
                                 top_universities=[])
        except:
            logger.error("Failed to recover stats, using fallback")
            return render_template('index.html', 
                                 stats={"total_professors": 0, "total_universities": 0, "total_publications": 0, "countries_count": 0},
                                 top_universities=[])

@app.route('/universities')
@monitor_performance
def universities():
    """Universities listing page with dynamic filters"""
    try:
        # Get filter parameters
        search = request.args.get('search', '').strip()
        country = request.args.get('country', '').strip()
        province = request.args.get('province', '').strip()
        uni_type = request.args.get('type', '').strip()
        language = request.args.get('language', '').strip()
        sort_by = request.args.get('sort_by', 'faculty_count')
        
        # Get available filters (cached)
        filters = get_available_university_filters()
        
        # Get filtered universities (with smart caching)
        universities_data = search_universities_with_filters(
            search=search,
            country=country, 
            province=province,
            uni_type=uni_type,
            language=language,
            sort_by=sort_by
        )
        
        return render_template('universities.html', 
                             universities=universities_data,
                             search=search, 
                             country=country, 
                             province=province, 
                             uni_type=uni_type, 
                             language=language, 
                             sort_by=sort_by,
                             available_countries=filters['countries'],
                             provinces_by_country=filters['provinces_by_country'],
                             available_types=filters['types'],
                             available_languages=filters['languages'])
    
    except Exception as e:
        logger.error(f"Error in universities route: {e}")
        filters = get_available_university_filters()
        return render_template('universities.html', 
                             universities=[],
                             search='', country='', province='', 
                             uni_type='', language='', sort_by='faculty_count',
                             available_countries=filters['countries'],
                             provinces_by_country=filters['provinces_by_country'],
                             available_types=filters['types'],
                             available_languages=filters['languages'])

def generate_faculty_cache_key(search, university, department, research_area, degree, sort_by, page, per_page):
    """Generate cache key for faculty search"""
    params = f"{search}:{university}:{department}:{research_area}:{degree}:{sort_by}:{page}:{per_page}"
    return f"faculty_search:{hashlib.md5(params.encode()).hexdigest()}"

@cached(timeout=600)  # Cache for 10 minutes
@monitor_performance
def search_faculty_optimized(search='', university='', department='', research_area='', 
                           position='', employment_type='', sort_by='name', page=1, per_page=20):
    """Search faculty with optimized query and pagination including publication data"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return {"results": [], "total": 0, "page": page, "per_page": per_page, "has_more": False}
        
        # Check if citation_count and h_index columns exist
        cursor = conn.execute("PRAGMA table_info(professors)")
        columns = [row[1] for row in cursor.fetchall()]
        
        has_citation_count = 'citation_count' in columns
        has_h_index = 'h_index' in columns
        
        # Build query with conditional columns and only existing fields
        citation_select = "p.citation_count" if has_citation_count else "0 as citation_count"
        h_index_select = "p.h_index" if has_h_index else "0 as h_index"
        
        # Enhanced query with publication data - using only known columns
        base_query = f"""
        SELECT p.id, p.name, p.position, p.department, p.research_areas, p.full_time, p.adjunct,
               p.uni_email as email, p.website,
               u.name as university_name, u.university_code,
               COUNT(DISTINCT ap.publication_id) as publication_count,
               {citation_select},
               {h_index_select}
        FROM professors p
        JOIN universities u ON p.university_code = u.university_code
        LEFT JOIN author_publications ap ON p.id = ap.professor_id
        """
        
        # Build WHERE conditions
        conditions = []
        params = []
        
        if search:
            conditions.append("(p.name LIKE ? OR p.research_areas LIKE ? OR p.department LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if university:
            # Handle both university codes (CA-ON-002) and university names (McMaster University)
            if '-' in university and len(university.split('-')) >= 3:
                # This looks like a university code
                conditions.append("u.university_code = ?")
                params.append(university)
            else:
                # This looks like a university name
                conditions.append("u.name = ?")
                params.append(university)
        
        if department:
            conditions.append("p.department = ?")
            params.append(department)
        
        if research_area:
            conditions.append("p.research_areas LIKE ?")
            params.append(f'%{research_area}%')
        
        if position:
            conditions.append("p.position = ?")
            params.append(position)
        
        if employment_type:
            if employment_type == 'full_time':
                conditions.append("p.full_time = 1")
            elif employment_type == 'adjunct':
                conditions.append("p.adjunct = 1")
            elif employment_type == 'part_time':
                conditions.append("p.full_time = 0 AND p.adjunct = 0")
        
        # Construct WHERE clause
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        
        # Add GROUP BY clause for aggregation
        group_fields = "p.id, p.name, p.position, p.department, p.research_areas, p.full_time, p.adjunct, p.uni_email, p.website, u.name, u.university_code"
        if has_citation_count:
            group_fields += ", p.citation_count"
        if has_h_index:
            group_fields += ", p.h_index"
        
        group_clause = f" GROUP BY {group_fields}"
        
        # Count total results (simplified query for counting)
        count_query = f"""
        SELECT COUNT(DISTINCT p.id) FROM professors p
        JOIN universities u ON p.university_code = u.university_code
        {where_clause}
        """
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add ORDER BY and LIMIT
        order_clause = {
            'name': 'ORDER BY p.name',
            'university': 'ORDER BY u.name, p.name',
            'department': 'ORDER BY p.department, p.name',
            'position': 'ORDER BY p.position, p.name',
            'publications': 'ORDER BY publication_count DESC, p.name'
        }.get(sort_by, 'ORDER BY p.name')
        
        # Build final query with conditional pagination
        final_query = base_query + where_clause + group_clause + f" {order_clause}"
        
        if per_page is not None:
            # Add pagination only when per_page is specified
            offset = (page - 1) * per_page
            final_query += f" LIMIT {per_page} OFFSET {offset}"
        
        cursor = conn.execute(final_query, params)
        results = []
        for row in cursor.fetchall():
            result_dict = dict(row)
            # Ensure we have default values
            if 'publication_count' not in result_dict or result_dict['publication_count'] is None:
                result_dict['publication_count'] = 0
            if 'citation_count' not in result_dict or result_dict['citation_count'] is None:
                result_dict['citation_count'] = 0
            if 'h_index' not in result_dict or result_dict['h_index'] is None:
                result_dict['h_index'] = 0
            results.append(result_dict)
        
        # Only close if we created a direct connection
        if hasattr(conn, '_direct_connection'):
            conn.close()
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": total > page * per_page if per_page is not None else False
        }
        
    except Exception as e:
        logger.error(f"Error in search_faculty_optimized: {e}")
        return {"results": [], "total": 0, "page": page, "per_page": per_page, "has_more": False}

@app.route('/faculties')
@monitor_performance
def faculties():
    """Faculty listing page with advanced filters"""
    try:
        # Get search parameters
        search = request.args.get('search', '').strip()
        university_code = request.args.get('university', '').strip()
        department = request.args.get('department', '').strip()
        research_area = request.args.get('research_area', '').strip()
        position = request.args.get('position', '').strip()  # Changed from degree to position
        employment_type = request.args.get('employment_type', '').strip()  # New parameter
        sort_by = request.args.get('sort_by', 'name')
        
        # Get available filter options
        filter_options = get_available_faculty_filters()
        
        # Check if we need to show all results (for table view)
        page = int(request.args.get('page', 1))
        show_all = request.args.get('show_all', '').lower() == 'true'
        per_page = None if show_all else 20
        
        # Get faculty results with pagination
        faculty_data = search_faculty_optimized(
            search=search,
            university=university_code,  # Now using university_code 
            department=department,
            research_area=research_area,
            position=position,  # Changed from degree to position
            employment_type=employment_type,  # New parameter
            sort_by=sort_by,
            page=page if not show_all else 1,
            per_page=per_page
        )
        
        # Calculate shown count correctly
        faculty_shown = len(faculty_data['results']) if show_all else min(page * 20, faculty_data['total'])
        
        return render_template('faculties.html',
                             faculty=faculty_data['results'],
                             faculty_shown=faculty_shown,
                             faculty_total=faculty_data['total'],
                             faculty_page=faculty_data['page'],
                             faculty_has_more=faculty_data['has_more'] and not show_all,
                             search=search,
                             university=university_code,  # Changed variable name
                             department=department,
                             research_area=research_area,
                             position=position,  # Changed from degree
                             employment_type=employment_type,  # New parameter
                             sort_by=sort_by,
                             filter_options=filter_options)  # Pass filter options
                             
    except Exception as e:
        logger.error(f"Error in faculties route: {e}")
        return render_template('faculties.html',
                             faculty=[],
                             faculty_shown=0,
                             faculty_total=0,
                             faculty_page=1,
                             faculty_has_more=False,
                             search='',
                             university='',
                             department='',
                             research_area='',
                             position='',
                             employment_type='',
                             sort_by='name',
                             filter_options={"universities": [], "departments": [], "positions": [], "employment_types": []})

@app.route('/professor/<string:professor_id>')
@monitor_performance
def professor_profile(professor_id):
    """Professor profile page with caching - now uses string IDs like CA-ON-002-0001"""
    cache_key = f"professor_profile:{professor_id}"
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return render_template('professor_profile.html', 
                             professor=cached_result['professor'], 
                             publications=cached_result['publications'])
    
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection error", 500
        
        # Optimized single query to get all professor data
        query = """
        SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
               p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
               p.university_code, p.faculty, p.department, p.other_departments,
               p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
               p.position, p.full_time, p.adjunct, p.uni_email as email, p.other_email,
               p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
               p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
               p.academicedu, p.created_at, p.updated_at,
               u.name as university_name, u.city, u.province_state, u.country, u.address, u.website as university_website
        FROM professors p
        LEFT JOIN universities u ON p.university_code = u.university_code
        WHERE p.id = ?
        """
        
        cursor = conn.execute(query, (professor_id,))
        professor = cursor.fetchone()
        
        if not professor:
            return "Professor not found", 404
        
        # Convert professor row to dictionary and parse research areas
        professor_dict = dict(professor)
        
        # Parse research areas from JSON
        if professor_dict.get('research_areas'):
            try:
                professor_dict['research_areas'] = json.loads(professor_dict['research_areas'])
            except (json.JSONDecodeError, TypeError):
                professor_dict['research_areas'] = []
        else:
            professor_dict['research_areas'] = []
        
        # Fetch publications for this professor
        publications_query = """
        SELECT pub.id, pub.pmid, pub.title, pub.authors, pub.journal_name, 
               pub.volume, pub.issue, pub.pages, pub.publication_date, 
               pub.publication_year, pub.abstract, pub.doi
        FROM author_publications ap
        JOIN publications pub ON ap.publication_id = pub.id
        WHERE ap.professor_id = ?
        ORDER BY pub.publication_year DESC, pub.publication_date DESC
        """
        
        cursor = conn.execute(publications_query, (professor_id,))
        publications_rows = cursor.fetchall()
        
        # Convert to list of dictionaries and parse JSON authors
        publications = []
        for row in publications_rows:
            pub_dict = dict(row)
            # Parse JSON authors field
            try:
                import json
                authors_list = json.loads(pub_dict['authors']) if pub_dict['authors'] else []
                pub_dict['authors'] = ', '.join(authors_list) if authors_list else 'Unknown authors'
            except:
                pub_dict['authors'] = 'Unknown authors'
            publications.append(pub_dict)
        
        # Cache both professor and publications for 1 hour
        cache_data = {
            'professor': professor_dict,
            'publications': publications
        }
        cache.set(cache_key, cache_data, 3600)
        
        return render_template('professor_profile.html', 
                             professor=professor_dict, 
                             publications=publications)
        
    except Exception as e:
        logger.error(f"Error getting professor {professor_id}: {e}")
        return "Error loading professor profile", 500

@app.route('/university/<string:university_code>')
@monitor_performance
@cached(timeout=1800)  # Cache university profiles for 30 minutes
def university_profile(university_code):
    """University profile page with statistics (optimized)"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return "Database connection error", 500
        
        # Single comprehensive query to get all university and faculty data at once
        comprehensive_query = """
        SELECT 
            u.university_code, u.name, u.city, u.province_state, u.country, u.address, 
            u.website, u.university_type, u.languages, u.year_established,
            COUNT(p.id) as total_faculty,
            COUNT(DISTINCT p.department) as unique_departments,
            COUNT(CASE WHEN p.full_time = 1 THEN 1 END) as full_time_faculty,
            COUNT(CASE WHEN p.adjunct = 1 THEN 1 END) as adjunct_faculty
        FROM universities u
        LEFT JOIN professors p ON u.university_code = p.university_code
        WHERE u.university_code = ?
        GROUP BY u.university_code, u.name, u.city, u.province_state, u.country, u.address, 
                 u.website, u.university_type, u.languages, u.year_established
        """
        
        cursor = conn.execute(comprehensive_query, (university_code,))
        result = cursor.fetchone()
        
        if not result:
            if hasattr(conn, '_direct_connection'):
                conn.close()
            logger.error(f"University {university_code} not found")
            return "University not found", 404
        
        university = {
            'university_code': result[0],
            'name': result[1],
            'city': result[2],
            'province_state': result[3],
            'country': result[4],
            'address': result[5],
            'website': result[6],
            'university_type': result[7],
            'languages': result[8],
            'year_established': result[9]
        }
        
        faculty_stats = {
            'total_faculty': result[10] or 0,
            'unique_departments': result[11] or 0,
            'full_time_faculty': result[12] or 0,
            'adjunct_faculty': result[13] or 0
        }
        
        logger.info(f"Found university: {university['name']} with {faculty_stats['total_faculty']} faculty")
        
        # Batch remaining queries efficiently
        batch_queries = {
            'departments': """
                SELECT department, COUNT(*) as faculty_count
                FROM professors
                WHERE university_code = ? AND department IS NOT NULL AND department != ''
                GROUP BY department
                ORDER BY faculty_count DESC
                LIMIT 10
            """,
            'research_areas': """
                SELECT research_areas, COUNT(*) as faculty_count
                FROM professors
                WHERE university_code = ? AND research_areas IS NOT NULL AND research_areas != ''
                GROUP BY research_areas
                ORDER BY faculty_count DESC
                LIMIT 10
            """,
            'recent_faculty': """
                SELECT name, position, department
                FROM professors
                WHERE university_code = ?
                ORDER BY id DESC
                LIMIT 5
            """
        }
        
        batch_results = {}
        for key, query in batch_queries.items():
            try:
                cursor = conn.execute(query, (university_code,))
                batch_results[key] = []
                for row in cursor.fetchall():
                    if key == 'recent_faculty':
                        batch_results[key].append({
                            'name': row[0],
                            'position': row[1],
                            'department': row[2]
                        })
                    else:
                        batch_results[key].append({
                            key[:-1]: row[0],  # Remove 's' from key name
                            'faculty_count': row[1]
                        })
                logger.info(f"Found {len(batch_results[key])} {key}")
            except Exception as e:
                logger.error(f"Error getting {key}: {e}")
                batch_results[key] = []
        
        # Optimized publication stats (simplified to avoid complex joins)
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM publications p
                INNER JOIN author_publications ap ON p.id = ap.publication_id
                INNER JOIN professors pr ON ap.professor_id = pr.id
                WHERE pr.university_code = ?
            """, (university_code,))
            
            pub_count = cursor.fetchone()[0] or 0
            publication_stats = {
                'total_publications': pub_count,
                'recent_publications': 0  # Simplified for performance
            }
        except Exception as e:
            logger.warning(f"Publications table not available: {e}")
            publication_stats = {
                'total_publications': 0,
                'recent_publications': 0
            }
        
        # Only close if we created a direct connection
        if hasattr(conn, '_direct_connection'):
            conn.close()
        
        return render_template('university_profile.html',
                             university=university,
                             faculty_stats=faculty_stats,
                             departments=batch_results['departments'],
                             publication_stats=publication_stats,
                             research_areas=batch_results['research_areas'],
                             recent_faculty=batch_results['recent_faculty'])
        
    except Exception as e:
        logger.error(f"Error in university_profile for {university_code}: {e}")
        return "Error loading university profile", 500

@app.route('/api/ai-stats')
@monitor_performance
def get_ai_stats_endpoint():
    """API endpoint to get AI usage statistics"""
    try:
        stats = get_ai_usage_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in AI stats endpoint: {e}")
        return jsonify({"error": "Failed to load AI statistics"}), 500

@app.route('/ai-assistant')
@monitor_performance 
def ai_assistant():
    """AI Assistant page with CV analysis"""
    try:
        ai_stats = get_ai_usage_statistics()
        return render_template('ai_assistant.html', ai_stats=ai_stats)
    except Exception as e:
        logger.error(f"Error in ai_assistant route: {e}")
        return render_template('ai_assistant.html', ai_stats={"total_sessions": 0, "successful_sessions": 0, "unique_providers": 0, "sessions_with_own_key": 0, "sessions_last_7_days": 0, "sessions_last_30_days": 0})

@app.route('/about')
@monitor_performance
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@monitor_performance
def contact():
    """Contact form page"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            
            # Basic validation
            if not all([name, email, subject, message]):
                return render_template('contact.html', 
                                     error="All fields are required.")
            
            # Send emails (if configured)
            confirmation_sent = send_contact_confirmation(email, name, subject, message)
            notification_sent = notify_support_team(email, name, subject, message)
            
            # Show success message
            if confirmation_sent or notification_sent:
                return render_template('contact.html', 
                                     success="Thank you for your message! We'll get back to you soon.")
            else:
                return render_template('contact.html', 
                                     warning="Your message was received, but email notifications are currently unavailable.")
        
        except Exception as e:
            logger.error(f"Error processing contact form: {e}")
            return render_template('contact.html', 
                                 error="An error occurred. Please try again later.")
    
    return render_template('contact.html')

@app.route('/privacy-policy')
@monitor_performance
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
@monitor_performance
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms_of_service.html')

@app.route('/login', methods=['GET', 'POST'])
@monitor_performance
def login():
    """Login page"""
    if request.method == 'POST':
        # Handle login form submission
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Basic validation
        if not username or not password:
            return render_template('auth/login.html', error="Please enter both username and password.")
        
        # For now, return a message that authentication is in development
        return render_template('auth/login.html', 
                             error="Authentication system is currently under development. Please check back soon!")
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
@monitor_performance
def register():
    """Registration page"""
    if request.method == 'POST':
        # Handle registration form submission
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Basic validation
        if not all([username, email, password, first_name, last_name]):
            return render_template('auth/register.html', error="Please fill in all required fields.")
        
        # For now, return a message that authentication is in development
        return render_template('auth/register.html', 
                             error="Authentication system is currently under development. Please check back soon!")
    
    return render_template('auth/register.html')

@app.route('/logout')
@monitor_performance
def logout():
    """Logout page"""
    # For now, just redirect to home
    return redirect(url_for('index'))

@app.route('/dashboard')
@monitor_performance
def dashboard():
    """User dashboard (placeholder)"""
    return render_template('user/dashboard.html')

@app.route('/profile')
@monitor_performance
def profile():
    """User profile page (placeholder)"""
    return render_template('user/profile.html')

@app.route('/user/crypto-payments')
@monitor_performance
def user_crypto_payments():
    """User crypto payments page (placeholder)"""
    return render_template('user/crypto_payments.html')

@app.route('/auth/google')
@monitor_performance
def google_login():
    """Google OAuth login (placeholder)"""
    return render_template('auth/login.html', 
                         error="Google OAuth is currently under development. Please check back soon!")

@app.route('/auth/google/callback')
@monitor_performance
def google_callback():
    """Google OAuth callback (placeholder)"""
    return redirect(url_for('index'))

@app.route('/api')
@monitor_performance
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')

@app.route('/test-icons')
@monitor_performance
def test_icons():
    """Icon loading diagnostic page"""
    return render_template('test_icons.html')

@app.route('/api/analyze-cv', methods=['POST'])
@monitor_performance
def analyze_cv():
    """
    AI CV Analysis API Endpoint
    Handles the complete workflow: CV upload -> AI analysis -> Faculty matching -> Recommendations
    """
    try:
        # Initialize CV analyzer
        cv_analyzer = CVAnalyzer(get_db_connection)
        
        # Validate request
        if 'cv_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No CV file uploaded. Please select a PDF or DOCX file.'
            }), 400
        
        file = request.files['cv_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected. Please choose a CV file to upload.'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload a PDF or DOCX file.'
            }), 400
        
        # Read file data
        file_data = file.read()
        
        # Validate file size (10MB limit)
        if not validate_file_size(file_data, max_size_mb=10):
            return jsonify({
                'success': False,
                'error': 'File too large. Please upload a file smaller than 10MB.'
            }), 400
        
        # Get form data
        ai_service = request.form.get('ai_service', 'claude')
        analysis_option = request.form.get('analysis_option', 'quick_pay')
        api_key = request.form.get('api_key') if analysis_option == 'api_key' else None
        
        # Collect user data
        user_data = {
            'academic_level': request.form.get('guest_level') or request.form.get('user_level'),
            'broad_category': request.form.get('broad_category'),
            'narrow_field': request.form.get('narrow_field'),
            'career_goals': request.form.get('career_goals'),
            'research_keywords': request.form.get('research_keywords'),
            'specific_interests': request.form.get('specific_interests'),
            'institution': request.form.get('guest_institution') or request.form.get('user_institution'),
            'name': request.form.get('guest_name') or request.form.get('user_name'),
            'email': request.form.get('guest_email'),
            'location': request.form.get('guest_location'),
            'bio': request.form.get('guest_bio') or request.form.get('user_bio')
        }
        
        # Validate required fields
        required_fields = ['broad_category', 'narrow_field', 'academic_level']
        missing_fields = [field for field in required_fields if not user_data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        logger.info(f"Starting CV analysis for {user_data.get('name', 'anonymous')} with {ai_service}")
        
        # Perform CV analysis
        result = cv_analyzer.analyze_cv(
            file_data=file_data,
            filename=file.filename,
            ai_service=ai_service,
            user_data=user_data,
            analysis_option=analysis_option,
            api_key=api_key
        )
        
        # Log the analysis
        if result['success']:
            logger.info(f"CV analysis completed successfully. Found {len(result['results']['matching_faculty'])} matching faculty.")
        else:
            logger.warning(f"CV analysis failed: {result.get('error')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in CV analysis endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred during analysis. Please try again or contact support.'
        }), 500

@app.route('/health')
@monitor_performance
def health_check():
    """Health check endpoint with performance metrics"""
    try:
        # Check database connection
        conn = get_db_connection()
        if conn:
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            db_status = "healthy"
        else:
            db_status = "unhealthy"
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Cache statistics
        cache_stats = {
            "cache_size": len(cache.cache),
            "cache_hits": getattr(cache, 'hits', 0),
            "cache_misses": getattr(cache, 'misses', 0)
        }
        
        # Connection pool stats
        pool_stats = {
            "available_connections": len(db_pool.connections),
            "connections_in_use": len(db_pool.in_use),
            "max_connections": db_pool.max_connections
        }
        
        health_data = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "email_configured": MAIL_AVAILABLE,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024)
            },
            "cache": cache_stats,
            "database_pool": pool_stats
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/performance')
@monitor_performance
def performance_metrics():
    """Performance metrics endpoint for monitoring"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent_used": disk.percent
                }
            },
            "process": {
                "memory_mb": process_memory.rss / (1024**2),
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "open_files": process.num_fds() if hasattr(process, 'num_fds') else 0
            },
            "database": {
                "pool_size": len(db_pool.connections),
                "active_connections": len(db_pool.in_use),
                "max_connections": db_pool.max_connections
            },
            "cache": {
                "size": len(cache.cache),
                "timeout_entries": len(cache.timeouts)
            }
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({"error": str(e)}), 500

# Static file optimization
@app.route('/static/css/<path:filename>')
def static_css(filename):
    """Serve CSS with optimization headers"""
    try:
        from flask import send_from_directory as sfd  # Explicit import
        response = sfd('static/css', filename)
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        response.headers['Content-Type'] = 'text/css'
        return response
    except Exception as e:
        logger.error(f"Error serving CSS file {filename}: {e}")
        # Fallback to default Flask static serving
        return app.send_static_file(f'css/{filename}')

@app.route('/static/js/<path:filename>')
def static_js(filename):
    """Serve JavaScript with optimization headers"""
    try:
        from flask import send_from_directory as sfd  # Explicit import
        response = sfd('static/js', filename)
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        response.headers['Content-Type'] = 'application/javascript'
        return response
    except Exception as e:
        logger.error(f"Error serving JS file {filename}: {e}")
        # Fallback to default Flask static serving
        return app.send_static_file(f'js/{filename}')

# Error handlers with performance monitoring
@app.errorhandler(404)
@monitor_performance
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
@monitor_performance
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return "Internal server error", 500

# Cache warming on startup
@cached(timeout=1800)  # Cache for 30 minutes
def get_ai_usage_statistics():
    """Get AI assistant usage statistics (cached)"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"total_sessions": 0, "successful_sessions": 0, "unique_providers": 0, "sessions_with_own_key": 0}
        
        query = """
        SELECT 
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN recommendations IS NOT NULL AND recommendations != '' THEN 1 END) as successful_sessions,
            COUNT(DISTINCT ai_provider) as unique_providers,
            COUNT(CASE WHEN api_key_provided = 1 THEN 1 END) as sessions_with_own_key,
            COUNT(CASE WHEN created_at >= date('now', '-7 days') THEN 1 END) as sessions_last_7_days,
            COUNT(CASE WHEN created_at >= date('now', '-30 days') THEN 1 END) as sessions_last_30_days
        FROM ai_sessions
        """
        
        cursor = conn.execute(query)
        row = cursor.fetchone()
        
        return {
            "total_sessions": row['total_sessions'],
            "successful_sessions": row['successful_sessions'],
            "unique_providers": row['unique_providers'],
            "sessions_with_own_key": row['sessions_with_own_key'],
            "sessions_last_7_days": row['sessions_last_7_days'],
            "sessions_last_30_days": row['sessions_last_30_days']
        }
        
    except Exception as e:
        logger.error(f"Error getting AI usage statistics: {e}")
        return {"total_sessions": 0, "successful_sessions": 0, "unique_providers": 0, "sessions_with_own_key": 0, "sessions_last_7_days": 0, "sessions_last_30_days": 0}

@app.route('/api/faculty/load-more')
@monitor_performance
def api_load_more_faculty():
    """API endpoint for loading more faculty with pagination"""
    try:
        # Get search parameters from URL
        search = request.args.get('search', '').strip()
        university = request.args.get('university', '').strip()
        department = request.args.get('department', '').strip()
        research_area = request.args.get('research_area', '').strip()
        position = request.args.get('position', '').strip()  # Use position instead of degree
        employment_type = request.args.get('employment_type', '').strip()
        sort_by = request.args.get('sort_by', 'name').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Search faculty with correct parameters
        result = search_faculty_optimized(
            search=search,
            university=university, 
            department=department,
            research_area=research_area,
            position=position,  # Use position instead of degree
            employment_type=employment_type,
            sort_by=sort_by,
            page=page,
            per_page=per_page
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in load more faculty API: {e}")
        return jsonify({"error": "Failed to load more faculty"}), 500

@app.route('/api/university/<university_code>/departments')
@monitor_performance 
def get_university_departments(university_code):
    """API endpoint to get departments for a specific university"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"departments": []})
        
        cursor = conn.execute('''
            SELECT department, COUNT(*) as count
            FROM professors 
            WHERE university_code = ? AND department IS NOT NULL AND department != ''
            GROUP BY department
            ORDER BY department
        ''', (university_code,))
        
        departments = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"departments": departments})
        
    except Exception as e:
        logger.error(f"Error getting departments for university {university_code}: {e}")
        return jsonify({"departments": []})

@app.route('/debug/stats-check')
def debug_stats_check():
    """Debug endpoint to check stats and cache status"""
    try:
        # Get current stats
        stats = get_summary_statistics()
        
        # Check cache status
        cache_key = f"get_summary_statistics:bcd8b0c2eb1fce714eab6cef0d771acc"
        is_cached = cache_key in cache.cache
        cache_expiry = cache.timeouts.get(cache_key, 0)
        current_time = time.time()
        cache_valid = cache_expiry > current_time if is_cached else False
        
        # Database connection test
        conn = get_db_connection()
        db_connected = conn is not None
        if conn:
            conn.close()
        
        return f"""
        <h1>Stats Debug</h1>
        <h2>Current Stats:</h2>
        <pre>{stats}</pre>
        
        <h2>Cache Status:</h2>
        <ul>
            <li>Is Cached: {is_cached}</li>
            <li>Cache Valid: {cache_valid}</li>
            <li>Cache Expiry: {cache_expiry}</li>
            <li>Current Time: {current_time}</li>
            <li>Time to Expiry: {cache_expiry - current_time if is_cached else 'N/A'} seconds</li>
        </ul>
        
        <h2>Database Status:</h2>
        <ul>
            <li>DB Connected: {db_connected}</li>
        </ul>
        
        <h2>Actions:</h2>
        <a href="/debug/clear-cache" style="margin: 10px; padding: 10px; background: red; color: white; text-decoration: none;">Clear Cache</a>
        <a href="/" style="margin: 10px; padding: 10px; background: blue; color: white; text-decoration: none;">Go to Homepage</a>
        """
    except Exception as e:
        return f"Error in debug check: {e}"

@app.route('/debug/clear-cache')
def debug_clear_cache():
    """Clear the cache and redirect to homepage"""
    try:
        cache.clear()
        logger.info("Cache manually cleared via debug endpoint")
        return "Cache cleared! <a href='/'>Go to Homepage</a>"
    except Exception as e:
        return f"Error clearing cache: {e}"

@cached(timeout=300)  # Cache for 5 minutes
@monitor_performance
def get_available_faculty_filters():
    """Get available filter options for faculty search with dynamic data"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return {"countries": [], "universities": [], "departments": [], "positions": [], "employment_types": []}
        
        # Get available countries with faculty counts
        countries_query = """
        SELECT DISTINCT u.country, COUNT(p.id) as count
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        WHERE u.country IS NOT NULL AND u.country != ''
        GROUP BY u.country
        ORDER BY u.country
        """
        cursor = conn.execute(countries_query)
        countries = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Get available universities with faculty counts
        universities_query = """
        SELECT u.university_code as code, u.name, u.country, COUNT(p.id) as count
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        GROUP BY u.university_code, u.name, u.country
        ORDER BY u.name
        """
        cursor = conn.execute(universities_query)
        universities = [{"code": row[0], "name": row[1], "country": row[2], "count": row[3]} for row in cursor.fetchall()]
        
        # Get available departments with faculty counts
        departments_query = """
        SELECT DISTINCT p.department, p.university_code, COUNT(p.id) as count
        FROM professors p 
        WHERE p.department IS NOT NULL AND p.department != ''
        GROUP BY p.department, p.university_code
        ORDER BY p.department
        """
        cursor = conn.execute(departments_query)
        departments = [{"name": row[0], "university_code": row[1], "count": row[2]} for row in cursor.fetchall()]
        
        # Get available academic positions/ranks with counts
        positions_query = """
        SELECT DISTINCT p.position, COUNT(p.id) as count
        FROM professors p 
        WHERE p.position IS NOT NULL AND p.position != ''
        GROUP BY p.position
        ORDER BY p.position
        """
        cursor = conn.execute(positions_query)
        positions = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Get available employment types with counts
        employment_types = []
        
        # Full-time count
        cursor = conn.execute("SELECT COUNT(*) FROM professors WHERE full_time = 1")
        full_time_count = cursor.fetchone()[0]
        if full_time_count > 0:
            employment_types.append({"value": "full-time", "label": "Full-time", "count": full_time_count})
        
        # Part-time count
        cursor = conn.execute("SELECT COUNT(*) FROM professors WHERE full_time = 0 AND adjunct = 0")
        part_time_count = cursor.fetchone()[0]
        if part_time_count > 0:
            employment_types.append({"value": "part-time", "label": "Part-time", "count": part_time_count})
        
        # Adjunct count
        cursor = conn.execute("SELECT COUNT(*) FROM professors WHERE adjunct = 1")
        adjunct_count = cursor.fetchone()[0]
        if adjunct_count > 0:
            employment_types.append({"value": "adjunct", "label": "Adjunct", "count": adjunct_count})
        
        conn.close()
        
        return {
            "countries": countries,
            "universities": universities,
            "departments": departments,
            "positions": positions,
            "employment_types": employment_types
        }
        
    except Exception as e:
        logger.error(f"Error getting faculty filters: {e}")
        return {"countries": [], "universities": [], "departments": [], "positions": [], "employment_types": []}

@cached(timeout=3600)  # Cache for 1 hour - country data is relatively stable
def get_country_statistics(country):
    """Get comprehensive statistics for a specific country (optimized)"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return None
        
        # Single optimized query to get most statistics at once
        main_stats_query = """
        SELECT 
            u.country,
            COUNT(DISTINCT u.university_code) as university_count,
            COUNT(DISTINCT p.id) as faculty_count,
            COUNT(DISTINCT u.province_state) as region_count,
            COUNT(DISTINCT u.city) as city_count,
            COUNT(DISTINCT u.university_type) as type_count,
                           COALESCE(COUNT(DISTINCT CASE WHEN p.department IS NOT NULL AND p.department != '' THEN p.department END), 0) as department_count
        FROM universities u 
        LEFT JOIN professors p ON u.university_code = p.university_code
        WHERE u.country = ?
        GROUP BY u.country
        """
        
        cursor = conn.execute(main_stats_query, (country,))
        basic_stats = cursor.fetchone()
        if not basic_stats:
            if hasattr(conn, '_direct_connection'):
                conn.close()
            return None
        
        stats = {
            'country': basic_stats[0],
            'university_count': basic_stats[1],
            'faculty_count': basic_stats[2],
            'region_count': basic_stats[3],
            'city_count': basic_stats[4],
            'type_count': basic_stats[5],
            'department_count': basic_stats[6]
        }
        
        # Batch additional queries for detailed breakdowns
        detail_queries = {
            'university_types': """
                SELECT university_type, COUNT(*) as count
                FROM universities 
                WHERE country = ? AND university_type IS NOT NULL
                GROUP BY university_type
                ORDER BY count DESC
                LIMIT 10
            """,
            'languages': """
                SELECT languages, COUNT(*) as count
                FROM universities 
                WHERE country = ? AND languages IS NOT NULL AND languages != ''
                GROUP BY languages
                ORDER BY count DESC
                LIMIT 10
            """,
            'regions': """
                SELECT u.province_state, COUNT(DISTINCT u.university_code) as university_count,
                       COUNT(p.id) as faculty_count
                FROM universities u 
                LEFT JOIN professors p ON u.university_code = p.university_code
                WHERE u.country = ? AND u.province_state IS NOT NULL
                GROUP BY u.province_state
                ORDER BY faculty_count DESC
                LIMIT 10
            """,
            'top_universities': """
                SELECT u.university_code, u.name, u.city, u.province_state, 
                       COUNT(p.id) as faculty_count
                FROM universities u 
                LEFT JOIN professors p ON u.university_code = p.university_code
                WHERE u.country = ?
                GROUP BY u.university_code, u.name, u.city, u.province_state
                ORDER BY faculty_count DESC
                LIMIT 10
            """,
            'top_departments': """
                SELECT p.department, COUNT(*) as faculty_count
                FROM professors p
                INNER JOIN universities u ON p.university_code = u.university_code
                WHERE u.country = ? AND p.department IS NOT NULL AND p.department != ''
                GROUP BY p.department
                ORDER BY faculty_count DESC
                LIMIT 15
            """,
            'academic_positions': """
                SELECT p.position, COUNT(*) as count
                FROM professors p
                INNER JOIN universities u ON p.university_code = u.university_code
                WHERE u.country = ? AND p.position IS NOT NULL AND p.position != ''
                GROUP BY p.position
                ORDER BY count DESC
                LIMIT 10
            """
        }
        
        # Execute all detail queries efficiently
        for key, query in detail_queries.items():
            try:
                cursor = conn.execute(query, (country,))
                stats[key] = []
                for row in cursor.fetchall():
                    if key == 'university_types':
                        stats[key].append({'university_type': row[0], 'count': row[1]})
                    elif key == 'languages':
                        stats[key].append({'languages': row[0], 'count': row[1]})
                    elif key == 'regions':
                        stats[key].append({'province_state': row[0], 'university_count': row[1], 'faculty_count': row[2]})
                    elif key == 'top_universities':
                        stats[key].append({
                            'university_code': row[0], 'name': row[1], 'city': row[2], 
                            'province_state': row[3], 'faculty_count': row[4]
                        })
                    elif key == 'top_departments':
                        stats[key].append({'department': row[0], 'faculty_count': row[1]})
                    elif key == 'academic_positions':
                        stats[key].append({'position': row[0], 'count': row[1]})
            except Exception as e:
                logger.warning(f"Error getting {key} for country {country}: {e}")
                stats[key] = []
        
        # Only close if we created a direct connection
        if hasattr(conn, '_direct_connection'):
            conn.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting country statistics for {country}: {e}")
        return None


def get_all_countries():
    """Get list of all countries with university data"""
    try:
        import sqlite3
        # Use the same database path as the main app
        db_path = DATABASE_PATH
        conn = sqlite3.connect(db_path)
        
        cursor = conn.execute('''
            SELECT u.country, COUNT(DISTINCT u.university_code) as university_count,
                   COUNT(p.id) as faculty_count
            FROM universities u 
            LEFT JOIN professors p ON u.university_code = p.university_code
            WHERE u.country IS NOT NULL AND u.country != ''
            GROUP BY u.country
            ORDER BY faculty_count DESC
        ''')
        
        countries = []
        for row in cursor.fetchall():
            countries.append({
                'country': row[0],
                'university_count': row[1], 
                'faculty_count': row[2]
            })
        
        conn.close()
        return countries
        
    except Exception as e:
        logger.error(f"Error getting countries list: {e}")
        return []


# Removed duplicate route - using the updated version with string parameter below

@app.route('/countries')
@monitor_performance
def countries():
    """Display countries with faculty data"""
    try:
        countries_list = get_countries_list()
        logger.info(f"Countries route: Found {len(countries_list) if countries_list else 0} countries")
        return render_template('countries.html', 
                             countries=countries_list,
                             countries_count=len(countries_list) if countries_list else 0)
    except Exception as e:
        logger.error(f"Error in countries route: {e}")
        return render_template('countries.html', 
                             countries=[],
                             countries_count=0)

@app.route('/country/<string:country_code>')
@monitor_performance  
def country_profile(country_code):
    """Display country profile with statistics using ISO country code"""
    try:
        # Convert to uppercase for consistency
        country_code = country_code.upper()
        
        country_stats = get_country_statistics(country_code)
        if not country_stats:
            logger.warning(f"Country not found: {country_code}")
            abort(404)
            
        return render_template('country_profile.html', 
                             country=country_stats)
    except Exception as e:
        logger.error(f"Error in country profile for {country_code}: {e}")
        abort(404)

def get_actual_database_path():
    """Get the actual database path being used by the live server (cached result)"""
    if not hasattr(get_actual_database_path, '_cached_path'):
        import os
        possible_paths = [
            '../database/facultyfinder_dev.db',  # Try this first - it has the data
            DATABASE_PATH,
            '../facultyfinder_dev.db',
            'facultyfinder_dev.db',
            os.path.join(os.path.dirname(__file__), '..', 'database', 'facultyfinder_dev.db'),
            os.path.join(os.path.dirname(__file__), 'facultyfinder_dev.db')
        ]
        
        for path in possible_paths:
            try:
                if os.path.exists(path) and os.path.getsize(path) > 10000:  # Has actual data
                    get_actual_database_path._cached_path = path
                    break
            except:
                continue
        else:
            # If none found with data, return the default
            get_actual_database_path._cached_path = DATABASE_PATH
    
    return get_actual_database_path._cached_path

def execute_cached_query(query, params=None, timeout=300, fetch_one=False):
    """Execute query with caching and optimization"""
    try:
        # Check cache first
        cache_result = query_cache.get(query, params)
        if cache_result is not None:
            return cache_result
        
        # Execute query with optimized connection
        conn = get_optimized_connection()
        if not conn:
            return None if fetch_one else []
        
        start_time = time.time()
        
        if params:
            cursor = conn.execute(query, params)
        else:
            cursor = conn.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
            if result:
                result = dict(result) if hasattr(result, 'keys') else result
        else:
            result = cursor.fetchall()
            result = [dict(row) if hasattr(row, 'keys') else row for row in result]
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log slow queries
        if execution_time > 500:
            logger.warning(f"Slow query ({execution_time:.2f}ms): {query[:100]}...")
        
        # Close connection if it's a direct connection
        if hasattr(conn, '_direct_connection'):
            conn.close()
        
        # Cache the result
        query_cache.set(query, params, result, timeout)
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing cached query: {e}")
        logger.error(f"Query: {query[:200]}...")
        return None if fetch_one else []

def get_optimized_connection():
    """Get optimized database connection with fallback options"""
    try:
        # First try performance optimizer
        if performance_optimizer:
            conn = performance_optimizer.get_optimized_connection()
            if conn:
                return conn
        
        # Try connection pool
        if db_pool:
            conn = db_pool.get_connection()
            if conn:
                return conn
        
        # Fallback to direct optimized connection
        db_path = get_actual_database_path()
        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Apply critical optimizations
        critical_pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=-32000",  # 32MB cache
            "PRAGMA temp_store=MEMORY",
            "PRAGMA busy_timeout=10000",
        ]
        
        for pragma in critical_pragmas:
            try:
                conn.execute(pragma)
            except Exception as e:
                logger.warning(f"Failed to apply {pragma}: {e}")
        
        # Mark as direct connection for cleanup
        conn._direct_connection = True
        return conn
        
    except Exception as e:
        logger.error(f"Failed to get optimized connection: {e}")
        return None

def create_performance_indexes():
    """Create additional database indexes for better query performance"""
    try:
        conn = get_optimized_connection()
        if not conn:
            logger.error("Cannot create indexes - no database connection")
            return False
        
        # Performance indexes for common query patterns
        performance_indexes = [
            # University-related indexes
            "CREATE INDEX IF NOT EXISTS idx_universities_country_type ON universities(country, university_type)",
            "CREATE INDEX IF NOT EXISTS idx_universities_province_country ON universities(province_state, country)",
            "CREATE INDEX IF NOT EXISTS idx_universities_name_lower ON universities(LOWER(name))",
            
            # Professor-related indexes  
            "CREATE INDEX IF NOT EXISTS idx_professors_name_search ON professors(name, department)",
            "CREATE INDEX IF NOT EXISTS idx_professors_position_type ON professors(position, full_time, adjunct)",
            "CREATE INDEX IF NOT EXISTS idx_professors_research_areas ON professors(research_areas)",
            "CREATE INDEX IF NOT EXISTS idx_professors_university_department ON professors(university_code, department)",
            
            # Publication-related indexes (if tables exist)
            "CREATE INDEX IF NOT EXISTS idx_publications_year_journal ON publications(publication_year, journal)",
            "CREATE INDEX IF NOT EXISTS idx_author_publications_compound ON author_publications(professor_id, publication_id)",
            
            # Full-text search optimization (SQLite FTS if available)
            "CREATE INDEX IF NOT EXISTS idx_professors_name_fts ON professors(name) WHERE name IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_universities_name_fts ON universities(name) WHERE name IS NOT NULL"
        ]
        
        created_count = 0
        for index_sql in performance_indexes:
            try:
                conn.execute(index_sql)
                created_count += 1
                logger.debug(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create index: {e}")
        
        conn.commit()
        if hasattr(conn, '_direct_connection'):
            conn.close()
            
        logger.info(f"Successfully processed {created_count} performance indexes")
        return True
        
    except Exception as e:
        logger.error(f"Error creating performance indexes: {e}")
        return False


def optimize_database_settings():
    """Optimize database settings for better performance"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return False
            
        # Apply performance optimizations
        optimizations = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=-64000",  # 64MB cache
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=268435456",  # 256MB mmap
            "PRAGMA page_size=4096",
            "PRAGMA optimize"  # Run SQLite optimizer
        ]
        
        for pragma in optimizations:
            try:
                conn.execute(pragma)
            except Exception as e:
                logger.warning(f"Failed to apply optimization {pragma}: {e}")
        
        if hasattr(conn, '_direct_connection'):
            conn.close()
            
        logger.info("Database optimization settings applied")
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        return False


# Initialize performance optimizations on startup
def initialize_performance_optimizations():
    """Initialize performance optimizations when the app starts"""
    try:
        logger.info("🚀 Initializing performance optimizations...")
        
        if not performance_optimizer:
            logger.warning("⚠️ Performance optimizer not available")
            return False
        
        # Create performance indexes
        if performance_optimizer.create_performance_indexes():
            logger.info("✅ Performance indexes created/verified")
        else:
            logger.warning("⚠️ Some performance indexes may not have been created")
        
        # Optimize cache strategy
        if performance_optimizer.optimize_cache_strategy():
            logger.info("✅ Cache strategy optimized")
        else:
            logger.warning("⚠️ Cache optimization may have failed")
        
        logger.info("✅ Performance optimization initialization complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing performance optimizations: {e}")
        return False


# Add performance cleanup route for admin use
@app.route('/admin/performance/cleanup')
@monitor_performance
def admin_performance_cleanup():
    """Admin endpoint to clean up cache and optimize performance"""
    try:
        if not performance_optimizer:
            return jsonify({"error": "Performance optimizer not available"}), 500
        
        # Clean up cache
        performance_optimizer.cleanup_cache()
        
        # Get performance summary
        summary = query_profiler.get_performance_summary()
        
        return jsonify({
            "status": "success",
            "message": "Performance cleanup completed",
            "performance_summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error in performance cleanup: {e}")
        return jsonify({"error": str(e)}), 500

# Import the performance optimizer
try:
    from performance_optimizer import create_performance_optimizer, query_profiler
    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZER_AVAILABLE = False
    logger.warning("Performance optimizer not available")

# Initialize performance optimizer
if PERFORMANCE_OPTIMIZER_AVAILABLE:
    performance_optimizer = create_performance_optimizer(get_actual_database_path(), cache)
else:
    performance_optimizer = None

@cached(timeout=600)  # Cache for 10 minutes
@monitor_performance
def get_countries_list():
    """Get list of countries with faculty data including universities and departments count"""
    try:
        # Import country codes locally to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from country_codes import get_country_code, normalize_country_name
        
        conn = get_optimized_connection()
        if not conn:
            return []
        
        query = """
        SELECT 
            u.country,
            COUNT(DISTINCT p.id) as faculty_count,
            COUNT(DISTINCT u.university_code) as university_count,
            COUNT(DISTINCT p.department) as department_count
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        WHERE u.country IS NOT NULL AND u.country != ''
        GROUP BY u.country
        ORDER BY faculty_count DESC
        """
        
        cursor = conn.execute(query)
        countries = []
        
        for row in cursor.fetchall():
            country_name = row[0]
            normalized_name = normalize_country_name(country_name)
            country_code = get_country_code(normalized_name)
            
            if country_code:  # Only include countries with valid ISO codes
                countries.append({
                    "name": normalized_name,
                    "code": country_code,
                    "faculty_count": row[1],
                    "university_count": row[2],
                    "department_count": row[3]
                })
        
        conn.close()
        logger.info(f"Found {len(countries)} countries with faculty data")
        return countries
        
    except Exception as e:
        logger.error(f"Error getting countries list: {e}")
        return []

@cached(timeout=600)  # Cache for 10 minutes  
@monitor_performance
def get_country_statistics(country_code):
    """Get detailed statistics for a specific country using ISO code"""
    try:
        # Import country codes locally
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from country_codes import get_country_name
        
        country_name = get_country_name(country_code)
        if not country_name:
            logger.error(f"Invalid country code: {country_code}")
            return None
        
        conn = get_optimized_connection()
        if not conn:
            return None
        
        # Get basic country statistics
        stats_query = """
        SELECT 
            u.country,
            COUNT(DISTINCT p.id) as total_faculty,
            COUNT(DISTINCT u.university_code) as total_universities,
            COUNT(DISTINCT p.department) as total_departments,
            COUNT(DISTINCT p.position) as unique_positions
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        WHERE u.country = ?
        GROUP BY u.country
        """
        
        cursor = conn.execute(stats_query, (country_name,))
        stats_row = cursor.fetchone()
        
        if not stats_row:
            conn.close()
            return None
        
        # Get top universities in the country
        unis_query = """
        SELECT 
            u.university_code,
            u.name,
            u.city,
            u.province_state,
            COUNT(p.id) as faculty_count
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        WHERE u.country = ?
        GROUP BY u.university_code, u.name, u.city, u.province_state
        ORDER BY faculty_count DESC
        LIMIT 10
        """
        
        cursor = conn.execute(unis_query, (country_name,))
        universities = []
        for row in cursor.fetchall():
            universities.append({
                "code": row[0],
                "name": row[1], 
                "city": row[2],
                "province_state": row[3],
                "faculty_count": row[4]
            })
        
        # Get top departments
        dept_query = """
        SELECT 
            p.department,
            COUNT(p.id) as faculty_count
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        WHERE u.country = ? AND p.department IS NOT NULL AND p.department != ''
        GROUP BY p.department
        ORDER BY faculty_count DESC
        LIMIT 10
        """
        
        cursor = conn.execute(dept_query, (country_name,))
        departments = []
        for row in cursor.fetchall():
            departments.append({
                "name": row[0],
                "faculty_count": row[1]
            })
        
        conn.close()
        
        return {
            "name": country_name,
            "code": country_code,
            "total_faculty": stats_row[1],
            "total_universities": stats_row[2], 
            "total_departments": stats_row[3],
            "unique_positions": stats_row[4],
            "universities": universities,
            "departments": departments
        }
        
    except Exception as e:
        logger.error(f"Error getting country statistics for {country_code}: {e}")
        return None

# API endpoint for dynamic university loading based on country
@app.route('/api/universities/<country>')
@monitor_performance
def api_universities_by_country(country):
    """Get universities for a specific country"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return jsonify({"universities": []})
        
        query = """
        SELECT u.university_code as code, u.name, COUNT(p.id) as count
        FROM professors p 
        JOIN universities u ON p.university_code = u.university_code
        WHERE u.country = ?
        GROUP BY u.university_code, u.name
        ORDER BY u.name
        """
        cursor = conn.execute(query, (country,))
        universities = [{"code": row[0], "name": row[1], "count": row[2]} for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({"universities": universities})
        
    except Exception as e:
        logger.error(f"Error getting universities for country {country}: {e}")
        return jsonify({"universities": []}), 500

# API endpoint for dynamic department loading based on university
@app.route('/api/departments/<university_code>')
@monitor_performance
def api_departments_by_university(university_code):
    """Get departments for a specific university"""
    try:
        conn = get_optimized_connection()
        if not conn:
            return jsonify({"departments": []})
        
        query = """
        SELECT DISTINCT p.department, COUNT(p.id) as count
        FROM professors p 
        WHERE p.university_code = ? AND p.department IS NOT NULL AND p.department != ''
        GROUP BY p.department
        ORDER BY p.department
        """
        cursor = conn.execute(query, (university_code,))
        departments = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({"departments": departments})
        
    except Exception as e:
        logger.error(f"Error getting departments for university {university_code}: {e}")
        return jsonify({"departments": []}), 500

# Add alias route for v1 API calls
@app.route('/api/v1/faculty/load-more')
@monitor_performance 
def api_v1_load_more_faculty():
    """API v1 endpoint for loading more faculty (alias)"""
    return api_load_more_faculty()

# Enhanced caching system for query results
class QueryResultCache:
    def __init__(self, max_size=1000, default_timeout=300):
        self.cache = {}
        self.timeouts = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_timeout = default_timeout
        self.lock = threading.Lock()
    
    def _generate_key(self, query, params=None):
        """Generate cache key from query and parameters"""
        import hashlib
        key_string = query
        if params:
            key_string += str(sorted(params) if isinstance(params, dict) else str(params))
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query, params=None):
        """Get cached query result"""
        key = self._generate_key(query, params)
        current_time = time.time()
        
        with self.lock:
            if key in self.cache and current_time < self.timeouts.get(key, 0):
                self.access_times[key] = current_time
                return self.cache[key]
            
            # Remove expired entry
            if key in self.cache:
                del self.cache[key]
                del self.timeouts[key]
                self.access_times.pop(key, None)
        
        return None
    
    def set(self, query, params, result, timeout=None):
        """Cache query result"""
        key = self._generate_key(query, params)
        current_time = time.time()
        timeout = timeout or self.default_timeout
        
        with self.lock:
            # Cleanup if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_least_recently_used()
            
            self.cache[key] = result
            self.timeouts[key] = current_time + timeout
            self.access_times[key] = current_time
    
    def _evict_least_recently_used(self):
        """Remove least recently used entries"""
        if not self.access_times:
            return
        
        # Remove 20% of entries (LRU)
        remove_count = max(1, len(self.cache) // 5)
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])
        
        for key, _ in sorted_items[:remove_count]:
            self.cache.pop(key, None)
            self.timeouts.pop(key, None)
            self.access_times.pop(key, None)
    
    def clear(self):
        """Clear all cached results"""
        with self.lock:
            self.cache.clear()
            self.timeouts.clear()
            self.access_times.clear()
    
    def get_stats(self):
        """Get cache statistics"""
        current_time = time.time()
        valid_entries = sum(1 for timeout in self.timeouts.values() if timeout > current_time)
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'max_size': self.max_size,
            'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
        }

# Initialize query cache
query_cache = QueryResultCache(max_size=500, default_timeout=600)

def test_database_connection():
    """Test database connection and log basic info"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed!")
            return False
        
        # Test basic queries
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"✅ Database connected. Tables: {tables}")
        
        # Count data
        if 'universities' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM universities")
            uni_count = cursor.fetchone()[0]
            logger.info(f"Universities in DB: {uni_count}")
        
        if 'professors' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM professors")
            prof_count = cursor.fetchone()[0]
            logger.info(f"Professors in DB: {prof_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

# Test database connection at startup
test_database_connection()

def get_simple_db_connection():
    """Get a simple, direct database connection for critical operations"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Basic optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-32000")  # 32MB cache
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        return conn
    except Exception as e:
        logger.error(f"Failed to create simple database connection: {e}")
        return None

if __name__ == '__main__':
    # Run the application
    app.run(host='127.0.0.1', port=8080, debug=True, threaded=True) 