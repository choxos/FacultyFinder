#!/usr/bin/env python3
"""
User Authentication Routes and User Dashboard for FacultyFinder
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import json
import logging
from auth import AuthManager
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
user_bp = Blueprint('user', __name__, url_prefix='/user')

class UserManager:
    """Handles user-specific operations"""
    
    def __init__(self, db_manager, auth_manager):
        self.db = db_manager
        self.auth = auth_manager
    
    def get_user_favorites(self, user_id, item_type=None, limit=50, offset=0):
        """Get user's favorites with optional filtering"""
        try:
            conditions = ['uf.user_id = ?']
            params = [user_id]
            
            if item_type:
                conditions.append('uf.item_type = ?')
                params.append(item_type)
            
            where_clause = ' WHERE ' + ' AND '.join(conditions)
            
            # Count total favorites
            count_query = f"SELECT COUNT(*) as total FROM user_favorites uf{where_clause}"
            count_result = self.db.execute_query(count_query, params, fetch_one=True)
            total = count_result['total'] if count_result else 0
            
            # Get paginated favorites
            if item_type == 'professor':
                query = f"""
                SELECT uf.*, p.name as item_name, p.department, u.name as university_name,
                       p.research_areas, p.position
                FROM user_favorites uf
                JOIN professors p ON uf.item_id = p.id
                LEFT JOIN universities u ON p.university_id = u.id
                {where_clause}
                ORDER BY uf.created_at DESC
                LIMIT ? OFFSET ?
                """
            elif item_type == 'university':
                query = f"""
                SELECT uf.*, u.name as item_name, u.city, u.province_state, u.country,
                       COUNT(p.id) as faculty_count
                FROM user_favorites uf
                JOIN universities u ON uf.item_id = u.id
                LEFT JOIN professors p ON u.id = p.university_id
                {where_clause}
                GROUP BY uf.id, u.id
                ORDER BY uf.created_at DESC
                LIMIT ? OFFSET ?
                """
            else:
                # Mixed favorites
                query = f"""
                SELECT uf.*, 
                       CASE 
                           WHEN uf.item_type = 'professor' THEN p.name
                           WHEN uf.item_type = 'university' THEN u.name
                       END as item_name,
                       CASE
                           WHEN uf.item_type = 'professor' THEN p.department
                           WHEN uf.item_type = 'university' THEN u.city
                       END as detail1,
                       CASE
                           WHEN uf.item_type = 'professor' THEN uni.name
                           WHEN uf.item_type = 'university' THEN u.country
                       END as detail2
                FROM user_favorites uf
                LEFT JOIN professors p ON uf.item_type = 'professor' AND uf.item_id = p.id
                LEFT JOIN universities u ON uf.item_type = 'university' AND uf.item_id = u.id
                LEFT JOIN universities uni ON p.university_id = uni.id
                {where_clause}
                ORDER BY uf.created_at DESC
                LIMIT ? OFFSET ?
                """
            
            params.extend([limit, offset])
            favorites = self.db.execute_query(query, params) or []
            
            return {
                'favorites': favorites,
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
            
        except Exception as e:
            logger.error(f"Error getting user favorites: {e}")
            return {'favorites': [], 'total': 0, 'limit': limit, 'offset': offset, 'has_more': False}
    
    def add_favorite(self, user_id, item_type, item_id, notes='', tags=None):
        """Add item to user's favorites"""
        try:
            # Check if already favorited
            check_query = """
            SELECT id FROM user_favorites 
            WHERE user_id = ? AND item_type = ? AND item_id = ?
            """
            existing = self.db.execute_query(check_query, [user_id, item_type, item_id], fetch_one=True)
            
            if existing:
                return False, "Item is already in your favorites"
            
            # Add favorite
            insert_query = """
            INSERT INTO user_favorites (user_id, item_type, item_id, notes, tags)
            VALUES (?, ?, ?, ?, ?)
            """
            
            params = [
                user_id,
                item_type,
                item_id,
                notes,
                json.dumps(tags) if tags else None
            ]
            
            self.db.execute_query(insert_query, params)
            
            # Log activity
            self.auth.log_user_activity(user_id, 'favorite_add', {
                'item_type': item_type,
                'item_id': item_id
            })
            
            return True, "Added to favorites successfully"
            
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            return False, "Failed to add to favorites"
    
    def remove_favorite(self, user_id, favorite_id):
        """Remove item from user's favorites"""
        try:
            # Get favorite details for logging
            favorite = self.db.execute_query(
                "SELECT * FROM user_favorites WHERE id = ? AND user_id = ?",
                [favorite_id, user_id],
                fetch_one=True
            )
            
            if not favorite:
                return False, "Favorite not found"
            
            # Remove favorite
            delete_query = "DELETE FROM user_favorites WHERE id = ? AND user_id = ?"
            self.db.execute_query(delete_query, [favorite_id, user_id])
            
            # Log activity
            self.auth.log_user_activity(user_id, 'favorite_remove', {
                'item_type': favorite['item_type'],
                'item_id': favorite['item_id']
            })
            
            return True, "Removed from favorites"
            
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            return False, "Failed to remove from favorites"
    
    def get_user_activity(self, user_id, limit=50, offset=0, activity_type=None):
        """Get user's activity history"""
        try:
            conditions = ['user_id = ?']
            params = [user_id]
            
            if activity_type:
                conditions.append('activity_type = ?')
                params.append(activity_type)
            
            where_clause = ' WHERE ' + ' AND '.join(conditions)
            
            # Count total activities
            count_query = f"SELECT COUNT(*) as total FROM user_activity_log{where_clause}"
            count_result = self.db.execute_query(count_query, params, fetch_one=True)
            total = count_result['total'] if count_result else 0
            
            # Get paginated activities
            query = f"""
            SELECT * FROM user_activity_log
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            
            params.extend([limit, offset])
            activities = self.db.execute_query(query, params) or []
            
            # Parse JSON activity data
            for activity in activities:
                if activity['activity_data']:
                    try:
                        activity['activity_data'] = json.loads(activity['activity_data'])
                    except:
                        activity['activity_data'] = {}
                else:
                    activity['activity_data'] = {}
            
            return {
                'activities': activities,
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return {'activities': [], 'total': 0, 'limit': limit, 'offset': offset, 'has_more': False}
    
    def get_user_search_history(self, user_id, limit=50, offset=0):
        """Get user's search history"""
        try:
            count_query = "SELECT COUNT(*) as total FROM user_search_history WHERE user_id = ?"
            count_result = self.db.execute_query(count_query, [user_id], fetch_one=True)
            total = count_result['total'] if count_result else 0
            
            query = """
            SELECT * FROM user_search_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            
            searches = self.db.execute_query(query, [user_id, limit, offset]) or []
            
            # Parse JSON filters
            for search in searches:
                if search['search_filters']:
                    try:
                        search['search_filters'] = json.loads(search['search_filters'])
                    except:
                        search['search_filters'] = {}
                else:
                    search['search_filters'] = {}
                
                if search['clicked_results']:
                    try:
                        search['clicked_results'] = json.loads(search['clicked_results'])
                    except:
                        search['clicked_results'] = []
                else:
                    search['clicked_results'] = []
            
            return {
                'searches': searches,
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
            
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return {'searches': [], 'total': 0, 'limit': limit, 'offset': offset, 'has_more': False}
    
    def get_user_payments(self, user_id, limit=50, offset=0):
        """Get user's payment history"""
        try:
            count_query = "SELECT COUNT(*) as total FROM user_payments WHERE user_id = ?"
            count_result = self.db.execute_query(count_query, [user_id], fetch_one=True)
            total = count_result['total'] if count_result else 0
            
            query = """
            SELECT * FROM user_payments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            
            payments = self.db.execute_query(query, [user_id, limit, offset]) or []
            
            # Parse JSON service details
            for payment in payments:
                if payment['service_details']:
                    try:
                        payment['service_details'] = json.loads(payment['service_details'])
                    except:
                        payment['service_details'] = {}
                else:
                    payment['service_details'] = {}
            
            return {
                'payments': payments,
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
            
        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return {'payments': [], 'total': 0, 'limit': limit, 'offset': offset, 'has_more': False}
    
    def get_user_collections(self, user_id):
        """Get user's collections"""
        try:
            query = """
            SELECT c.*, COUNT(ci.id) as item_count
            FROM user_collections c
            LEFT JOIN user_collection_items ci ON c.id = ci.collection_id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """
            
            return self.db.execute_query(query, [user_id]) or []
            
        except Exception as e:
            logger.error(f"Error getting user collections: {e}")
            return []
    
    def create_collection(self, user_id, name, description='', is_public=False, color=None, icon=None):
        """Create a new collection"""
        try:
            query = """
            INSERT INTO user_collections (user_id, name, description, is_public, color, icon)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            params = [user_id, name, description, is_public, color, icon]
            self.db.execute_query(query, params)
            
            # Log activity
            self.auth.log_user_activity(user_id, 'collection_create', {
                'collection_name': name
            })
            
            return True, "Collection created successfully"
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False, "Failed to create collection"

# Initialize user manager
user_manager = None

def init_user_manager(db_manager, auth_manager):
    """Initialize user manager"""
    global user_manager
    user_manager = UserManager(db_manager, auth_manager)

# Authentication Routes
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            user_data = {
                'username': request.form.get('username', '').strip(),
                'email': request.form.get('email', '').strip(),
                'password': request.form.get('password', ''),
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'institution': request.form.get('institution', '').strip(),
                'field_of_study': request.form.get('field_of_study', '').strip(),
                'academic_level': request.form.get('academic_level', '').strip(),
                'bio': request.form.get('bio', '').strip(),
                'website': request.form.get('website', '').strip(),
                'orcid': request.form.get('orcid', '').strip()
            }
            
            success, message, user = user_manager.auth.create_user(user_data)
            
            if success:
                login_user(user)
                flash('Registration successful! Welcome to FacultyFinder.', 'success')
                return redirect(url_for('user.dashboard'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username_or_email = request.form.get('username_or_email', '').strip()
            password = request.form.get('password', '')
            remember_me = request.form.get('remember_me') == 'on'
            
            success, message, user = user_manager.auth.authenticate_user(username_or_email, password)
            
            if success:
                login_user(user, remember=remember_me)
                flash(f'Welcome back, {user.get_full_name()}!', 'success')
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('user.dashboard'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('An error occurred during login.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# User Dashboard Routes
@user_bp.route('/')
@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user's recent activity
    activity = user_manager.get_user_activity(current_user.id, limit=10)
    
    # Get recent favorites
    favorites = user_manager.get_user_favorites(current_user.id, limit=5)
    
    # Get recent searches
    searches = user_manager.get_user_search_history(current_user.id, limit=5)
    
    # Get collections
    collections = user_manager.get_user_collections(current_user.id)
    
    # Get payment history
    payments = user_manager.get_user_payments(current_user.id, limit=5)
    
    return render_template('user/dashboard.html',
                         activity=activity,
                         favorites=favorites,
                         searches=searches,
                         collections=collections,
                         payments=payments)

@user_bp.route('/favorites')
@login_required
def favorites():
    """User favorites page"""
    item_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    favorites_data = user_manager.get_user_favorites(
        current_user.id, 
        item_type=item_type if item_type else None,
        limit=per_page, 
        offset=offset
    )
    
    return render_template('user/favorites.html', 
                         **favorites_data,
                         item_type=item_type,
                         page=page)

@user_bp.route('/activity')
@login_required
def activity():
    """User activity history"""
    activity_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    activity_data = user_manager.get_user_activity(
        current_user.id,
        limit=per_page,
        offset=offset,
        activity_type=activity_type if activity_type else None
    )
    
    return render_template('user/activity.html',
                         **activity_data,
                         activity_type=activity_type,
                         page=page)

@user_bp.route('/searches')
@login_required
def searches():
    """User search history"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search_data = user_manager.get_user_search_history(
        current_user.id,
        limit=per_page,
        offset=offset
    )
    
    return render_template('user/searches.html',
                         **search_data,
                         page=page)

@user_bp.route('/payments')
@login_required
def payments():
    """User payment history"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    payment_data = user_manager.get_user_payments(
        current_user.id,
        limit=per_page,
        offset=offset
    )
    
    return render_template('user/payments.html',
                         **payment_data,
                         page=page)

# API Routes for user actions
@user_bp.route('/api/favorite', methods=['POST'])
@login_required
def api_add_favorite():
    """Add item to favorites via API"""
    try:
        data = request.get_json()
        item_type = data.get('item_type')
        item_id = data.get('item_id')
        notes = data.get('notes', '')
        tags = data.get('tags', [])
        
        if not item_type or not item_id:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        success, message = user_manager.add_favorite(current_user.id, item_type, item_id, notes, tags)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        return jsonify({'success': False, 'error': 'Failed to add favorite'}), 500

@user_bp.route('/api/favorite/<int:favorite_id>', methods=['DELETE'])
@login_required
def api_remove_favorite(favorite_id):
    """Remove favorite via API"""
    try:
        success, message = user_manager.remove_favorite(current_user.id, favorite_id)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        return jsonify({'success': False, 'error': 'Failed to remove favorite'}), 500 