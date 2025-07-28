#!/usr/bin/env python3
"""
FacultyFinder Web Application
Flask-based web interface for discovering academic faculty and their research
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'development-key-change-in-production'

# Database configuration
DEV_DB = '../database/facultyfinder_dev.db'

# Simple user context for templates
@app.context_processor
def inject_user():
    """Inject current_user context for templates"""
    class AnonymousUser:
        is_authenticated = False
        def is_admin(self):
            return False
        def is_moderator(self):
            return False
        def get_full_name(self):
            return "Guest"
    
    return dict(current_user=AnonymousUser())

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DEV_DB)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/faculties')
def faculties():
    """Faculty listing page - simplified version"""
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection error", 500
        
        # Simple query to get faculty with university names
        query = """
        SELECT p.id, p.name, p.department, p.research_areas, u.name as university_name
        FROM professors p
        LEFT JOIN universities u ON p.university_id = u.id
        ORDER BY p.name
        LIMIT 50
        """
        
        cursor = conn.execute(query)
        faculty_data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return render_template('faculties.html',
                             faculty=faculty_data,
                             search='', university='', department='',
                             research_area='', degree='', sort_by='name',
                             available_universities=[],
                             available_departments=[],
                             available_degrees=[],
                             pagination={'has_more': False, 'total': len(faculty_data)})
    
    except Exception as e:
        logger.error(f"Error in faculties route: {e}")
        return f"Error loading faculties: {str(e)}", 500

@app.route('/universities')
def universities():
    """Universities listing page"""
    return render_template('universities.html', universities=[])

@app.route('/ai-assistant')
def ai_assistant():
    """AI Assistant page"""
    return render_template('ai_assistant.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact us page with form"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            return render_template('contact.html', 
                                 error="Please fill in all required fields.",
                                 form_data=request.form)
        
        # Here you would typically:
        # 1. Send email notification
        # 2. Store in database
        # 3. Send confirmation email
        
        # For now, just show success message
        success_message = f"Thank you {name}! Your message has been received. We'll get back to you at {email} within 24 hours."
        return render_template('contact.html', success=success_message)
    
    return render_template('contact.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.execute("SELECT COUNT(*) FROM professors")
            count = cursor.fetchone()[0]
            conn.close()
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'professors_count': count
            })
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api')
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080) 