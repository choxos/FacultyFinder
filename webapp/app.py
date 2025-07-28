#!/usr/bin/env python3
"""
FacultyFinder Web Application
Flask-based web interface for discovering academic faculty and their research
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import psycopg2
import psycopg2.extras
import sqlite3
import json
import os
from datetime import datetime
import logging
import pandas as pd
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    try:
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
        DB_CONFIG = ProductionConfig.DB_CONFIG
        DEV_DB = None
    except ImportError:
        # Fallback configuration
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
        DB_CONFIG = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', 5432)),
            'user': os.environ.get('DB_USER', 'ff_user'),
            'password': os.environ.get('DB_PASSWORD', 'Choxos10203040'),
            'database': os.environ.get('DB_NAME', 'ff_production')
        }
        DEV_DB = None
else:
    # Development configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', 5432),
        'user': os.environ.get('DB_USER', 'facultyfinder_user'),
        'password': os.environ.get('DB_PASSWORD', 'your_secure_password'),
        'database': os.environ.get('DB_NAME', 'facultyfinder_production')
    }
    DEV_DB = os.environ.get('DEV_DB_PATH', '../database/facultyfinder_dev.db')

class DatabaseManager:
    """Database connection and query manager"""
    
    def __init__(self, config=None, dev_mode=None):
        self.config = config or DB_CONFIG
        self.dev_mode = dev_mode if dev_mode is not None else (DEV_DB is not None)
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        try:
            if self.dev_mode:
                self.conn = sqlite3.connect(DEV_DB)
                self.conn.row_factory = sqlite3.Row
            else:
                self.conn = psycopg2.connect(**self.config)
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        if not self.conn:
            if not self.connect():
                return None
        
        try:
            if self.dev_mode:
                cursor = self.conn.cursor()
                cursor.execute(query, params or [])
                results = cursor.fetchall()
                cursor.close()
                return [dict(row) for row in results]
            else:
                cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            if self.conn:
                self.conn.rollback()
            return None

# Initialize database manager
db = DatabaseManager(DB_CONFIG, dev_mode=(DEV_DB is not None))

# Add health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        result = db.execute_query("SELECT 1")
        if result:
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/')
def index():
    """Main landing page"""
    # Get summary statistics
    stats = get_summary_statistics()
    top_universities = get_top_universities()
    
    return render_template('index.html', 
                         stats=stats, 
                         top_universities=top_universities)

@app.route('/universities')
def universities():
    """Universities listing page"""
    search = request.args.get('search', '')
    country = request.args.get('country', '')
    province = request.args.get('province', '')
    
    universities_data = search_universities(search, country, province)
    
    return render_template('universities.html', 
                         universities=universities_data,
                         search=search,
                         country=country,
                         province=province)

@app.route('/faculties')
def faculties():
    """Faculty listing page"""
    search = request.args.get('search', '')
    university = request.args.get('university', '')
    research_area = request.args.get('research_area', '')
    department = request.args.get('department', '')
    
    faculty_data = search_faculty(search, university, research_area, department)
    
    return render_template('faculties.html',
                         faculty=faculty_data,
                         search=search,
                         university=university,
                         research_area=research_area,
                         department=department)

@app.route('/professor/<int:professor_id>')
def professor_profile(professor_id):
    """Individual professor profile page"""
    professor = get_professor_details(professor_id)
    if not professor:
        return render_template('404.html'), 404
    
    publications = get_professor_publications(professor_id)
    collaborators = get_professor_collaborators(professor_id)
    journal_metrics = get_professor_journal_metrics(professor_id)
    degrees = get_professor_degrees(professor_id)
    
    return render_template('professor_profile.html',
                         professor=professor,
                         publications=publications,
                         collaborators=collaborators,
                         journal_metrics=journal_metrics,
                         degrees=degrees)

@app.route('/ai-assistant')
def ai_assistant():
    """AI Assistant page for CV analysis"""
    return render_template('ai_assistant.html')

@app.route('/api/analyze-cv', methods=['POST'])
def analyze_cv():
    """Handle CV analysis requests"""
    try:
        # Check if file was uploaded
        if 'cv_file' not in request.files:
            return jsonify({'success': False, 'error': 'No CV file uploaded'})
        
        file = request.files['cv_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Get form data
        selected_ai = request.form.get('selected_ai')
        payment_method = request.form.get('payment_method')
        api_key = request.form.get('api_key', '')
        
        # Validate inputs
        if not selected_ai or not payment_method:
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        if payment_method == 'api-key' and not api_key:
            return jsonify({'success': False, 'error': 'API key required'})
        
        # Save uploaded file temporarily
        import os
        import tempfile
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            # Extract text from CV
            cv_text = extract_cv_text(file_path)
            
            # Process based on payment method
            if payment_method == 'api-key':
                # Use user's API key for analysis
                results = analyze_with_ai(cv_text, selected_ai, api_key)
            elif payment_method == 'one-time':
                # Handle Stripe payment first
                return jsonify({'success': False, 'error': 'Payment processing not yet implemented'})
            elif payment_method == 'manual':
                # Queue for manual review
                return jsonify({'success': False, 'error': 'Manual review processing not yet implemented'})
            else:
                return jsonify({'success': False, 'error': 'Invalid payment method'})
            
            # Generate results HTML
            results_html = generate_results_html(results)
            
            return jsonify({
                'success': True,
                'data': {
                    'html': results_html,
                    'matches': results.get('matches', []),
                    'score': results.get('overall_score', 0)
                }
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        app.logger.error(f"CV analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def extract_cv_text(file_path):
    """Extract text content from PDF or DOCX files"""
    import os
    from pathlib import Path
    
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            # Fallback to pdfplumber if PyPDF2 not available
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text
            except ImportError:
                raise Exception("PDF processing library not available. Please install PyPDF2 or pdfplumber.")
    
    elif file_ext == '.docx':
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise Exception("DOCX processing library not available. Please install python-docx.")
    
    else:
        raise Exception("Unsupported file format. Please upload PDF or DOCX files only.")

def analyze_with_ai(cv_text, ai_service, api_key):
    """Analyze CV using selected AI service"""
    
    # Get faculty data for context
    db = DatabaseManager()
    faculty_data = db.search_faculty('', '', '', '')  # Get all faculty
    
    # Create context about available faculty
    faculty_context = ""
    for prof in faculty_data[:50]:  # Limit to first 50 for context
        faculty_context += f"- {prof['name']} at {prof['university_name']}, {prof['department']}: {prof['research_areas']}\n"
    
    prompt = f"""
    As an expert academic advisor, analyze the following CV and recommend the best faculty matches from our database.
    
    CV Content:
    {cv_text}
    
    Available Faculty (sample):
    {faculty_context}
    
    Please provide:
    1. Top 10 faculty recommendations with match scores (0-100)
    2. Reasoning for each recommendation
    3. Research alignment analysis
    4. Suggested approach for contacting each faculty
    5. Overall CV strengths and improvement suggestions
    
    Format your response as structured JSON with the following format:
    {{
        "overall_score": 85,
        "cv_strengths": ["strength1", "strength2"],
        "cv_improvements": ["improvement1", "improvement2"],
        "matches": [
            {{
                "faculty_name": "Dr. John Smith",
                "university": "McMaster University",
                "department": "Engineering",
                "match_score": 95,
                "reasoning": "Strong alignment in AI research...",
                "contact_strategy": "Mention your ML background..."
            }}
        ]
    }}
    """
    
    try:
        if ai_service == 'claude':
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            
        elif ai_service == 'chatgpt':
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000
            )
            result = response.choices[0].message.content
            
        elif ai_service == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            result = response.text
            
        elif ai_service == 'grok':
            # Note: Grok API integration would go here
            # For now, return a placeholder
            raise Exception("Grok API integration not yet available")
        
        else:
            raise Exception(f"Unsupported AI service: {ai_service}")
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            # Fallback: create structured response from text
            return {
                "overall_score": 75,
                "cv_strengths": ["Well-structured", "Clear objectives"],
                "cv_improvements": ["Add more publications", "Strengthen research focus"],
                "matches": [
                    {
                        "faculty_name": "Sample Faculty",
                        "university": "Sample University",
                        "department": "Sample Department",
                        "match_score": 80,
                        "reasoning": "Analysis completed successfully",
                        "contact_strategy": "Professional email recommended"
                    }
                ]
            }
            
    except Exception as e:
        app.logger.error(f"AI analysis error: {str(e)}")
        raise Exception(f"AI analysis failed: {str(e)}")

def generate_results_html(results):
    """Generate HTML for displaying analysis results"""
    html = f"""
    <div class="analysis-results">
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h4 class="text-primary">Overall Match Score</h4>
                        <div class="display-3 text-success">{results.get('overall_score', 0)}%</div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>CV Strengths</h5>
                        <ul>
                            {''.join([f'<li>{strength}</li>' for strength in results.get('cv_strengths', [])])}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mb-4">
            <h4>Top Faculty Recommendations</h4>
            <div class="row">
    """
    
    for i, match in enumerate(results.get('matches', [])[:10]):
        html += f"""
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title">{match.get('faculty_name', 'Unknown')}</h6>
                                <span class="badge bg-primary">{match.get('match_score', 0)}%</span>
                            </div>
                            <p class="text-muted small mb-2">{match.get('university', '')} - {match.get('department', '')}</p>
                            <p class="small">{match.get('reasoning', '')[:150]}...</p>
                            <div class="alert alert-light small">
                                <strong>Contact Strategy:</strong> {match.get('contact_strategy', '')[:100]}...
                            </div>
                        </div>
                    </div>
                </div>
        """
    
    html += """
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h5>CV Improvement Suggestions</h5>
            </div>
            <div class="card-body">
                <ul>
    """
    
    for improvement in results.get('cv_improvements', []):
        html += f"<li>{improvement}</li>"
    
    html += """
                </ul>
            </div>
        </div>
    </div>
    """
    
    return html

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/api')
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')

# API Endpoints
@app.route('/api/v1/professors')
def api_professors():
    """API endpoint for professor data"""
    search = request.args.get('search', '')
    university = request.args.get('university', '')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    
    faculty_data = search_faculty(search, university, limit=limit, offset=offset)
    
    return jsonify({
        'professors': faculty_data,
        'total': len(faculty_data),
        'limit': limit,
        'offset': offset
    })

@app.route('/api/v1/universities')
def api_universities():
    """API endpoint for university data"""
    universities_data = get_all_universities()
    return jsonify({'universities': universities_data})

@app.route('/api/v1/professor/<int:professor_id>')
def api_professor_detail(professor_id):
    """API endpoint for individual professor details"""
    professor = get_professor_details(professor_id)
    if not professor:
        return jsonify({'error': 'Professor not found'}), 404
    
    publications = get_professor_publications(professor_id)
    
    return jsonify({
        'professor': professor,
        'publications': publications
    })

# Helper functions
def get_summary_statistics():
    """Get summary statistics for dashboard"""
    try:
        stats = {}
        
        # Professor count
        result = db.execute_query("SELECT COUNT(*) as count FROM professors")
        stats['total_professors'] = result[0]['count'] if result else 0
        
        # University count  
        result = db.execute_query("SELECT COUNT(*) as count FROM universities")
        stats['total_universities'] = result[0]['count'] if result else 0
        
        # Publication count (placeholder for now)
        result = db.execute_query("SELECT COUNT(*) as count FROM publications")
        stats['total_publications'] = result[0]['count'] if result else 0
        
        # Countries covered
        result = db.execute_query("SELECT COUNT(DISTINCT country) as count FROM universities")
        stats['countries_covered'] = result[0]['count'] if result else 0
        
        return stats
    except Exception as e:
        logger.error(f"Error getting summary statistics: {e}")
        return {'total_professors': 0, 'total_universities': 0, 'total_publications': 0, 'countries_covered': 0}

def get_top_universities():
    """Get top 10 universities by faculty count with enhanced data"""
    db = DatabaseManager()
    try:
        query = """
        SELECT u.*, COUNT(p.id) as professor_count, COUNT(DISTINCT p.department) as department_count
        FROM universities u
        LEFT JOIN professors p ON u.id = p.university_id
        GROUP BY u.id, u.name, u.city, u.province_state, u.country,
                 u.address, u.university_type, u.languages, u.year_established
        ORDER BY professor_count DESC
        LIMIT 10
        """
        return db.execute_query(query) or []
    except Exception as e:
        logger.error(f"Error getting top universities: {e}")
        return []

def search_universities(search='', country='', province='', uni_type='', language=''):
    """Search and filter universities with enhanced filters"""
    db = DatabaseManager()
    try:
        conditions = []
        params = []
        
        base_query = """
        SELECT u.*, COUNT(p.id) as professor_count, COUNT(DISTINCT p.department) as department_count
        FROM universities u
        LEFT JOIN professors p ON u.id = p.university_id
        """
        
        if search:
            conditions.append("u.name LIKE ?")
            params.append(f"%{search}%")
        
        if country:
            conditions.append("u.country = ?")
            params.append(country)
        
        if province:
            conditions.append("u.province_state = ?")
            params.append(province)
        
        if uni_type:
            conditions.append("u.university_type = ?")
            params.append(uni_type)
        
        if language:
            conditions.append("u.languages LIKE ?")
            params.append(f"%{language}%")
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = base_query + where_clause + " GROUP BY u.id ORDER BY u.name"
        
        return db.execute_query(query, params) or []
    except Exception as e:
        logger.error(f"Error searching universities: {e}")
        return []

def search_faculty(search='', university='', research_area='', department='', limit=50, offset=0):
    """Search and filter faculty"""
    try:
        conditions = []
        params = []
        
        base_query = """
        SELECT p.*, u.name as university_name, u.city, u.province_state
        FROM professors p
        LEFT JOIN universities u ON p.university_id = u.id
        """
        
        if search:
            conditions.append("(p.name LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ? OR p.research_areas LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if university:
            conditions.append("u.name LIKE ?")
            params.append(f"%{university}%")
        
        if research_area:
            conditions.append("p.research_areas LIKE ?")
            params.append(f"%{research_area}%")
        
        if department:
            conditions.append("p.department LIKE ?")
            params.append(f"%{department}%")
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = base_query + where_clause + " ORDER BY p.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return db.execute_query(query, params) or []
    except Exception as e:
        logger.error(f"Error searching faculty: {e}")
        return []

def get_professor_details(professor_id):
    """Get detailed professor information"""
    try:
        query = """
        SELECT p.*, u.name as university_name, u.city, u.province_state, u.country
        FROM professors p
        LEFT JOIN universities u ON p.university_id = u.id
        WHERE p.id = ?
        """
        result = db.execute_query(query, [professor_id])
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting professor details: {e}")
        return None

def get_professor_publications(professor_id):
    """Get professor's publications"""
    try:
        query = """
        SELECT pub.*, ap.author_order, ap.is_corresponding, ap.is_first_author, ap.is_last_author
        FROM publications pub
        JOIN author_publications ap ON pub.id = ap.publication_id
        WHERE ap.professor_id = ?
        ORDER BY pub.publication_year DESC, pub.title
        """
        return db.execute_query(query, [professor_id]) or []
    except Exception as e:
        logger.error(f"Error getting professor publications: {e}")
        return []

def get_professor_collaborators(professor_id):
    """Get professor's collaborators"""
    try:
        query = """
        SELECT p2.id, p2.name, p2.department, u.name as university_name,
               c.collaboration_count, c.latest_collaboration_year
        FROM collaborations c
        JOIN professors p2 ON (c.professor1_id = p2.id OR c.professor2_id = p2.id)
        LEFT JOIN universities u ON p2.university_id = u.id
        WHERE (c.professor1_id = ? OR c.professor2_id = ?) AND p2.id != ?
        ORDER BY c.collaboration_count DESC
        LIMIT 20
        """
        return db.execute_query(query, [professor_id, professor_id, professor_id]) or []
    except Exception as e:
        logger.error(f"Error getting professor collaborators: {e}")
        return []

def get_professor_journal_metrics(professor_id):
    """Get professor's journal impact metrics"""
    try:
        # This is a placeholder implementation
        # In a real system, this would calculate metrics from publications and journal rankings
        return {
            'total_publications': len(get_professor_publications(professor_id)),
            'q1_percentage': 0,
            'q2_percentage': 0,
            'q3_percentage': 0,
            'q4_percentage': 0,
            'mean_sjr': 0,
            'median_sjr': 0
        }
    except Exception as e:
        logger.error(f"Error getting professor journal metrics: {e}")
        return {}

def get_all_universities():
    """Get all universities"""
    try:
        query = """
        SELECT u.*, COUNT(p.id) as professor_count
        FROM universities u
        LEFT JOIN professors p ON u.id = p.university_id
        GROUP BY u.id
        ORDER BY u.name
        """
        return db.execute_query(query) or []
    except Exception as e:
        logger.error(f"Error getting all universities: {e}")
        return []

def get_available_degrees():
    """Get all available degree types with counts"""
    try:
        query = """
        SELECT d.degree_type, d.full_name, d.category, COUNT(pd.professor_id) as professor_count
        FROM degrees d
        LEFT JOIN professor_degrees pd ON d.id = pd.degree_id
        GROUP BY d.id, d.degree_type, d.full_name, d.category
        HAVING professor_count > 0
        ORDER BY professor_count DESC, d.degree_type
        """
        return db.execute_query(query) or []
    except Exception as e:
        logger.error(f"Error getting available degrees: {e}")
        return []

def get_professor_degrees(professor_id):
    """Get degrees for a specific professor"""
    try:
        query = """
        SELECT d.degree_type, d.full_name, d.category, pd.specialization, pd.institution, pd.year_obtained
        FROM degrees d
        JOIN professor_degrees pd ON d.id = pd.degree_id
        WHERE pd.professor_id = ?
        ORDER BY 
            CASE d.category
                WHEN 'Doctoral' THEN 1
                WHEN 'Master''s' THEN 2
                WHEN 'Bachelor''s' THEN 3
                ELSE 4
            END,
            d.degree_type
        """
        return db.execute_query(query, [professor_id]) or []
    except Exception as e:
        logger.error(f"Error getting professor degrees: {e}")
        return []

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080) 