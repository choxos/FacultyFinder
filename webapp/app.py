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
    """Notify support team of new contact"""
    if not mail:
        logger.warning("Email not configured. Cannot notify support team.")
        return False
    
    try:
        msg = Message(
            subject=f"New Contact Form: {subject}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['SUPPORT_EMAIL']]
        )
        
        msg.body = f"""New contact form submission:

From: {user_name} <{user_email}>
Subject: {subject}

Message:
{message}

---
Sent from FacultyFinder Contact Form
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        mail.send(msg)
        logger.info(f"Support notification sent for contact from {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending support notification: {e}")
        return False

def get_summary_statistics():
    """Get summary statistics for the platform"""
    try:
        conn = get_db_connection()
        if not conn:
            return {
                'total_professors': 0,
                'total_universities': 0,
                'total_publications': 0,
                'countries_covered': 0
            }
        
        # Get professor count
        cursor = conn.execute("SELECT COUNT(*) FROM professors")
        total_professors = cursor.fetchone()[0]
        
        # Get university count
        cursor = conn.execute("SELECT COUNT(DISTINCT id) FROM universities WHERE id IN (SELECT DISTINCT university_id FROM professors)")
        total_universities = cursor.fetchone()[0]
        
        # Get publication count (approximate from CSV data)
        cursor = conn.execute("SELECT COUNT(*) FROM professors")
        total_publications = cursor.fetchone()[0] * 15  # Rough estimate
        
        # Get countries covered
        cursor = conn.execute("SELECT COUNT(DISTINCT country) FROM universities WHERE id IN (SELECT DISTINCT university_id FROM professors)")
        countries_covered = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_professors': total_professors,
            'total_universities': total_universities,
            'total_publications': total_publications,
            'countries_covered': countries_covered
        }
        
    except Exception as e:
        logger.error(f"Error getting summary statistics: {e}")
        return {
            'total_professors': 0,
            'total_universities': 0,
            'total_publications': 0,
            'countries_covered': 0
        }

def get_top_universities():
    """Get top universities by faculty count"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        query = """
        SELECT u.name, u.city, u.province_state, u.country, u.address,
               u.university_type, u.languages, u.year_established,
               COUNT(p.id) as professor_count
        FROM universities u
        INNER JOIN professors p ON u.id = p.university_id
        GROUP BY u.id, u.name, u.city, u.province_state, u.country, u.address,
                 u.university_type, u.languages, u.year_established
        ORDER BY professor_count DESC
        LIMIT 9
        """
        
        cursor = conn.execute(query)
        universities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return universities
        
    except Exception as e:
        logger.error(f"Error getting top universities: {e}")
        return []

@app.route('/')
def index():
    """Home page with statistics and top universities"""
    try:
        # Get summary statistics
        stats = get_summary_statistics()
        
        # Get top universities
        top_universities = get_top_universities()
        
        return render_template('index.html', 
                             stats=stats,
                             top_universities=top_universities)
    
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # Provide fallback data
        stats = {
            'total_professors': 0,
            'total_universities': 0,
            'total_publications': 0,
            'countries_covered': 0
        }
        return render_template('index.html', 
                             stats=stats,
                             top_universities=[])

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
    """Contact us page with form and email functionality"""
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
        
        # Email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return render_template('contact.html',
                                 error="Please enter a valid email address.",
                                 form_data=request.form)
        
        # Try to send emails
        confirmation_sent = send_contact_confirmation(email, name, subject, message)
        support_notified = notify_support_team(email, name, subject, message)
        
        # Prepare success message
        if confirmation_sent:
            success_message = f"Thank you {name}! Your message has been received. We'll get back to you at {email} within 24 hours."
        else:
            success_message = f"Thank you {name}! Your message has been received. We'll get back to you within 24 hours."
            
        if not support_notified:
            logger.warning(f"Support team not notified for contact from {email}")
        
        return render_template('contact.html', success=success_message)
    
    return render_template('contact.html')

@app.route('/api')
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.execute("SELECT COUNT(*) FROM professors")
            count = cursor.fetchone()[0]
            conn.close()
            
            health_status = {
                'status': 'healthy',
                'database': 'connected',
                'professors_count': count,
                'email_configured': mail is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(health_status)
        else:
            return jsonify({
                'status': 'unhealthy', 
                'database': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'unhealthy', 
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080) 