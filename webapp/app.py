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
from flask import Flask, render_template, request, jsonify, g, make_response, redirect, url_for
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional

# Authentication imports
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import re
from email_validator import validate_email, EmailNotValidError

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
app.config['SECRET_KEY'] = 'development-key-change-in-production'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

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
DEV_DB = 'database/facultyfinder_dev.db'

# Connection pool implementation for SQLite
class SQLiteConnectionPool:
    def __init__(self, database_path, max_connections=20):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connections = []
        self.in_use = set()
        self.lock = threading.Lock()
        
        # Pre-create connections
        for _ in range(5):  # Start with 5 connections
            conn = self._create_connection()
            if conn:
                self.connections.append(conn)
    
    def _create_connection(self):
        try:
            conn = sqlite3.connect(self.database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # SQLite optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    def get_connection(self):
        with self.lock:
            # Return existing connection if available
            if self.connections:
                conn = self.connections.pop()
                self.in_use.add(conn)
                return conn
            
            # Create new connection if under limit
            if len(self.in_use) < self.max_connections:
                conn = self._create_connection()
                if conn:
                    self.in_use.add(conn)
                    return conn
        
        # Return None if no connections available
        return None
    
    def return_connection(self, conn):
        with self.lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
                self.connections.append(conn)

# Global connection pool
db_pool = SQLiteConnectionPool(DEV_DB)

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
        db_pool.return_connection(g.db_conn)

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
    """Compress response if client accepts gzip"""
    if (response.status_code < 200 or 
        response.status_code >= 300 or 
        'gzip' not in request.headers.get('Accept-Encoding', '') or
        len(response.get_data()) < 500):
        return response
    
    gzipped = gzip.compress(response.get_data())
    response.set_data(gzipped)
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(gzipped)
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
    
    # Compression
    if response.mimetype.startswith('text/') or response.mimetype == 'application/json':
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

@cached(timeout=300)  # Cache for 5 minutes (shorter than before)
@monitor_performance
def get_summary_statistics():
    """Get summary statistics for the homepage (cached)"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"professors": 0, "universities": 0, "publications": 0, "countries": 0}
        
        # Use a single query with subqueries for better performance
        query = """
        SELECT 
            (SELECT COUNT(*) FROM professors) as professors,
            (SELECT COUNT(DISTINCT id) FROM universities WHERE id IN (SELECT DISTINCT university_id FROM professors)) as universities,
            (SELECT COUNT(*) FROM publications) as publications,
            (SELECT COUNT(DISTINCT country) FROM universities WHERE id IN (SELECT DISTINCT university_id FROM professors)) as countries
        """
        
        cursor = conn.execute(query)
        row = cursor.fetchone()
        
        return {
            "professors": row['professors'],
            "universities": row['universities'], 
            "publications": row['publications'],
            "countries": row['countries']
        }
        
    except Exception as e:
        logger.error(f"Error getting summary statistics: {e}")
        return {"professors": 0, "universities": 0, "publications": 0, "countries": 0}

@cached(timeout=1800)  # Cache for 30 minutes
@monitor_performance
def get_top_universities():
    """Get top universities by professor count (cached)"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        # Optimized query with proper joins
        query = """
        SELECT u.id, u.name, u.city, u.province_state, u.country, u.address, u.website,
               u.university_type, u.languages, u.year_established,
               COUNT(p.id) as professor_count
        FROM universities u
        INNER JOIN professors p ON u.id = p.university_id
        GROUP BY u.id, u.name, u.city, u.province_state, u.country, u.address, u.website,
                 u.university_type, u.languages, u.year_established
        ORDER BY professor_count DESC
        LIMIT 9
        """
        
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Error getting top universities: {e}")
        return []

@cached(timeout=1800)  # Cache for 30 minutes
@monitor_performance
def get_available_university_filters():
    """Get available filter options from universities with faculty (cached)"""
    try:
        conn = get_db_connection()
        if not conn:
            return {
                'countries': [],
                'provinces_by_country': {},
                'types': [],
                'languages': []
            }
        
        # Batch all filter queries for efficiency
        queries = {
            'countries': """
                SELECT DISTINCT u.country 
                FROM universities u 
                INNER JOIN professors p ON u.id = p.university_id 
                WHERE u.country IS NOT NULL AND u.country != ''
                ORDER BY u.country
            """,
            'provinces': """
                SELECT DISTINCT u.country, u.province_state 
                FROM universities u 
                INNER JOIN professors p ON u.id = p.university_id 
                WHERE u.country IS NOT NULL AND u.country != ''
                AND u.province_state IS NOT NULL AND u.province_state != ''
                ORDER BY u.country, u.province_state
            """,
            'types': """
                SELECT DISTINCT u.university_type 
                FROM universities u 
                INNER JOIN professors p ON u.id = p.university_id 
                WHERE u.university_type IS NOT NULL AND u.university_type != ''
                ORDER BY u.university_type
            """,
            'languages': """
                SELECT DISTINCT u.languages 
                FROM universities u 
                INNER JOIN professors p ON u.id = p.university_id 
                WHERE u.languages IS NOT NULL AND u.languages != ''
            """
        }
        
        results = {}
        for key, query in queries.items():
            cursor = conn.execute(query)
            results[key] = cursor.fetchall()
        
        # Process results
        countries = [row[0] for row in results['countries']]
        
        provinces_by_country = {}
        for row in results['provinces']:
            country, province = row
            if country not in provinces_by_country:
                provinces_by_country[country] = []
            if province not in provinces_by_country[country]:
                provinces_by_country[country].append(province)
        
        types = [row[0] for row in results['types']]
        
        languages = set()
        for row in results['languages']:
            language_string = row[0]
            if language_string:
                for lang in language_string.split(';'):
                    lang = lang.strip()
                    if lang:
                        languages.add(lang)
        languages = sorted(list(languages))
        
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
        conn = get_db_connection()
        if not conn:
            return []
        
        # Optimized query with better structure
        base_query = """
        SELECT u.id, u.name, u.city, u.province_state, u.country, u.address, u.website,
               u.university_type, u.languages, u.year_established,
               COUNT(p.id) as professor_count
        FROM universities u
        INNER JOIN professors p ON u.id = p.university_id
        """
        
        conditions = []
        params = []
        
        # Add filters dynamically
        if search:
            conditions.append("(u.name LIKE ? OR u.city LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if country:
            conditions.append("u.country = ?")
            params.append(country)
        
        if province:
            conditions.append("u.province_state LIKE ?")
            params.append(f'%{province}%')
        
        if uni_type:
            conditions.append("u.university_type = ?")
            params.append(uni_type)
        
        if language:
            conditions.append("u.languages LIKE ?")
            params.append(f'%{language}%')
        
        # Construct final query
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        group_clause = """
        GROUP BY u.id, u.name, u.city, u.province_state, u.country, u.address, u.website,
                 u.university_type, u.languages, u.year_established
        """
        
        # Optimize sorting
        order_clause = {
            'name': 'ORDER BY u.name',
            'location': 'ORDER BY u.country, u.province_state, u.city',
            'year_established': 'ORDER BY u.year_established DESC NULLS LAST',
            'faculty_count': 'ORDER BY professor_count DESC'
        }.get(sort_by, 'ORDER BY professor_count DESC')
        
        final_query = base_query + where_clause + group_clause + order_clause
        
        cursor = conn.execute(final_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Cache results for 15 minutes
        cache.set(cache_key, results, 900)
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
        top_universities = get_top_universities()
        
        return render_template('index.html', 
                             stats=stats,
                             top_universities=top_universities)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('index.html', 
                             stats={"professors": 0, "universities": 0, "publications": 0, "countries": 0},
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

def generate_faculty_cache_key(search, university, department, research_area, degree, sort_by):
    """Generate cache key for faculty search"""
    params = f"{search}:{university}:{department}:{research_area}:{degree}:{sort_by}"
    return f"faculty_search:{hashlib.md5(params.encode()).hexdigest()}"

@monitor_performance
def search_faculty_optimized(search='', university='', department='', research_area='', degree='', sort_by='name'):
    """Optimized faculty search with caching"""
    # Check cache first
    cache_key = generate_faculty_cache_key(search, university, department, research_area, degree, sort_by)
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        # Base query with optimized joins
        base_query = """
        SELECT p.id, p.name, p.position, p.department, p.research_areas, 
               p.uni_email as email, p.website, u.name as university_name,
               u.address, u.city, u.province_state, u.country
        FROM professors p
        LEFT JOIN universities u ON p.university_id = u.id
        """
        
        conditions = []
        params = []
        
        # Add search filters
        if search:
            conditions.append("(p.name LIKE ? OR p.research_areas LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if university:
            conditions.append("u.name LIKE ?")
            params.append(f'%{university}%')
        
        if department:
            conditions.append("p.department LIKE ?")
            params.append(f'%{department}%')
        
        if research_area:
            conditions.append("p.research_areas LIKE ?")
            params.append(f'%{research_area}%')
        
        # Handle degree filtering (would need professor_degrees table)
        if degree:
            # This would require the professor_degrees relationship table
            # For now, we'll skip this filter
            pass
        
        # Construct final query
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Optimize sorting
        order_clause = {
            'name': 'ORDER BY p.name',
            'university': 'ORDER BY u.name, p.name',
            'department': 'ORDER BY p.department, p.name',
            'position': 'ORDER BY p.position, p.name'
        }.get(sort_by, 'ORDER BY p.name')
        
        final_query = base_query + where_clause + order_clause + " LIMIT 100"  # Limit for performance
        
        cursor = conn.execute(final_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Cache results for 10 minutes
        cache.set(cache_key, results, 600)
        return results
        
    except Exception as e:
        logger.error(f"Error searching faculty: {e}")
        return []

@app.route('/faculties')
@monitor_performance
def faculties():
    """Faculty listing page with search and filters"""
    try:
        # Get search parameters
        search = request.args.get('search', '').strip()
        university = request.args.get('university', '').strip()
        department = request.args.get('department', '').strip()
        research_area = request.args.get('research_area', '').strip()
        degree = request.args.get('degree', '').strip()
        sort_by = request.args.get('sort_by', 'name')
        
        # Get faculty results (with caching)
        faculty = search_faculty_optimized(
            search=search,
            university=university,
            department=department,
            research_area=research_area,
            degree=degree,
            sort_by=sort_by
        )
        
        # Get available filters (this would need to be implemented)
        available_degrees = []  # Placeholder
        
        return render_template('faculties.html',
                             faculty=faculty,
                             search=search,
                             university=university,
                             department=department,
                             research_area=research_area,
                             degree=degree,
                             sort_by=sort_by,
                             available_degrees=available_degrees)
    
    except Exception as e:
        logger.error(f"Error in faculties route: {e}")
        return render_template('faculties.html',
                             faculty=[],
                             search='', university='', department='',
                             research_area='', degree='', sort_by='name',
                             available_degrees=[])

@app.route('/professor/<int:professor_id>')
@monitor_performance
def professor_profile(professor_id):
    """Professor profile page with caching"""
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
               p.university_id, p.faculty, p.department, p.other_departments,
               p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
               p.position, p.full_time, p.adjunct, p.uni_email as email, p.other_email,
               p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
               p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
               p.academicedu, p.created_at, p.updated_at,
               u.name as university_name, u.city, u.province_state, u.country, u.address, u.website as university_website
        FROM professors p
        LEFT JOIN universities u ON p.university_id = u.id
        WHERE p.id = ?
        """
        
        cursor = conn.execute(query, (professor_id,))
        professor = cursor.fetchone()
        
        if not professor:
            return "Professor not found", 404
        
        professor_dict = dict(professor)
        
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

@app.route('/ai-assistant')
@monitor_performance
def ai_assistant():
    """AI assistant page"""
    return render_template('ai_assistant.html')

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

@app.route('/api')
@monitor_performance
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')

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
    response = send_from_directory('static/css', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    response.headers['Content-Type'] = 'text/css'
    return response

@app.route('/static/js/<path:filename>')
def static_js(filename):
    """Serve JavaScript with optimization headers"""
    response = send_from_directory('static/js', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    response.headers['Content-Type'] = 'application/javascript'
    return response

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
def warm_cache():
    """Warm up the cache with frequently accessed data"""
    try:
        logger.info("Warming up cache...")
        get_summary_statistics()
        get_top_universities()
        get_available_university_filters()
        logger.info("Cache warmed successfully")
    except Exception as e:
        logger.error(f"Error warming cache: {e}")

# Performance monitoring middleware
@app.before_request
def before_request():
    """Track request start time"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """Log request performance and add headers"""
    if hasattr(g, 'start_time'):
        duration = (time.time() - g.start_time) * 1000
        
        # Log slow requests
        if duration > 1000:  # > 1 second
            logger.warning(f"Slow request: {request.endpoint} took {duration:.2f}ms")
        
        # Add performance header
        response.headers['X-Response-Time'] = f"{duration:.2f}ms"
    
    return response

# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            institution = request.form.get('institution', '').strip()
            field_of_study = request.form.get('field_of_study', '').strip()
            academic_level = request.form.get('academic_level', '').strip()
            bio = request.form.get('bio', '').strip()
            website = request.form.get('website', '').strip()
            orcid = request.form.get('orcid', '').strip()
            
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters long")
            
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                errors.append("Username can only contain letters, numbers, and underscores")
            
            try:
                validate_email(email)
            except EmailNotValidError:
                errors.append("Invalid email address")
            
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters long")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if errors:
                return render_template('auth/register.html', errors=errors, **request.form)
            
            # Check if username or email already exists
            conn = get_db_connection()
            if not conn:
                return render_template('auth/register.html', 
                                     errors=["Database connection error"], **request.form)
            
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?", 
                (username, email)
            )
            
            if cursor.fetchone():
                return render_template('auth/register.html', 
                                     errors=["Username or email already exists"], **request.form)
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            # Create user
            cursor = conn.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name,
                                 institution, field_of_study, academic_level, bio, website, orcid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, email, password_hash, first_name, last_name,
                  institution, field_of_study, academic_level, bio, website, orcid))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Log in the user
            user = load_user(user_id)
            login_user(user)
            
            logger.info(f"New user registered: {username} ({email})")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return render_template('auth/register.html', 
                                 errors=["Registration failed. Please try again."], **request.form)
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        try:
            username_or_email = request.form.get('username_or_email', '').strip()
            password = request.form.get('password', '')
            remember = bool(request.form.get('remember'))
            
            if not username_or_email or not password:
                return render_template('auth/login.html', 
                                     error="Please provide both username/email and password",
                                     username_or_email=username_or_email)
            
            # Find user by username or email
            conn = get_db_connection()
            if not conn:
                return render_template('auth/login.html', 
                                     error="Database connection error",
                                     username_or_email=username_or_email)
            
            cursor = conn.execute("""
                SELECT * FROM users 
                WHERE (username = ? OR email = ?) AND is_active = 1
            """, (username_or_email, username_or_email.lower()))
            
            user_data = cursor.fetchone()
            
            if not user_data or not check_password_hash(user_data['password_hash'], password):
                return render_template('auth/login.html', 
                                     error="Invalid username/email or password",
                                     username_or_email=username_or_email)
            
            # Create user object and log in
            user = User(
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
            
            login_user(user, remember=remember)
            
            # Update login stats
            conn.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE id = ?
            """, (user.id,))
            conn.commit()
            
            logger.info(f"User logged in: {user.username}")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return render_template('auth/login.html', 
                                 error="Login failed. Please try again.",
                                 username_or_email=username_or_email)
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('user/dashboard.html', error="Database connection error")
        
        # Get user's saved items
        cursor = conn.execute("""
            SELECT item_type, item_id, saved_at
            FROM user_saved_items 
            WHERE user_id = ?
            ORDER BY saved_at DESC
        """, (current_user.id,))
        saved_items = cursor.fetchall()
        
        # Get user's activity history  
        cursor = conn.execute("""
            SELECT activity_type, description, created_at
            FROM user_activities 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (current_user.id,))
        activities = cursor.fetchall()
        
        # Get payment history
        cursor = conn.execute("""
            SELECT amount, currency, payment_method, status, created_at, description
            FROM payments 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (current_user.id,))
        payments = cursor.fetchall()
        
        return render_template('user/dashboard.html', 
                             saved_items=saved_items,
                             activities=activities,
                             payments=payments)
                             
    except Exception as e:
        logger.error(f"Dashboard error for user {current_user.id}: {e}")
        return render_template('user/dashboard.html', error="Error loading dashboard")

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        try:
            # Update profile
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            institution = request.form.get('institution', '').strip()
            field_of_study = request.form.get('field_of_study', '').strip()
            academic_level = request.form.get('academic_level', '').strip()
            bio = request.form.get('bio', '').strip()
            website = request.form.get('website', '').strip()
            orcid = request.form.get('orcid', '').strip()
            
            conn = get_db_connection()
            if conn:
                conn.execute("""
                    UPDATE users 
                    SET first_name=?, last_name=?, institution=?, field_of_study=?,
                        academic_level=?, bio=?, website=?, orcid=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (first_name, last_name, institution, field_of_study,
                      academic_level, bio, website, orcid, current_user.id))
                conn.commit()
                
                logger.info(f"Profile updated for user {current_user.username}")
                return render_template('user/profile.html', success="Profile updated successfully")
        
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return render_template('user/profile.html', error="Failed to update profile")
    
    return render_template('user/profile.html')

if __name__ == '__main__':
    # Warm cache on startup
    warm_cache()
    
    # Run the application
    app.run(host='127.0.0.1', port=8080, debug=True, threaded=True) 