#!/usr/bin/env python3
"""
Admin Dashboard System for FacultyFinder
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict
from auth import admin_required, moderator_required
import psutil
import os

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

class AdminDashboard:
    """Admin dashboard functionality"""
    
    def __init__(self, db_manager, auth_manager):
        self.db = db_manager
        self.auth = auth_manager
    
    def get_system_stats(self):
        """Get comprehensive system statistics"""
        try:
            stats = {}
            
            # Database statistics
            db_stats = self.get_database_stats()
            stats['database'] = db_stats
            
            # User statistics
            user_stats = self.get_user_stats()
            stats['users'] = user_stats
            
            # Activity statistics
            activity_stats = self.get_activity_stats()
            stats['activity'] = activity_stats
            
            # System performance
            system_stats = self.get_system_performance()
            stats['system'] = system_stats
            
            # Revenue statistics
            revenue_stats = self.get_revenue_stats()
            stats['revenue'] = revenue_stats
            
            # API usage statistics
            api_stats = self.get_api_usage_stats()
            stats['api'] = api_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def get_database_stats(self):
        """Get database-related statistics"""
        try:
            stats = {}
            
            # Core entity counts
            entities = [
                ('universities', 'Universities'),
                ('professors', 'Professors'),
                ('publications', 'Publications'),
                ('users', 'Users'),
                ('user_favorites', 'User Favorites'),
                ('user_search_history', 'Searches'),
                ('user_payments', 'Payments')
            ]
            
            for table, label in entities:
                result = self.db.execute_query(f"SELECT COUNT(*) as count FROM {table}", fetch_one=True)
                stats[table] = {
                    'count': result['count'] if result else 0,
                    'label': label
                }
            
            # Growth statistics (last 30 days)
            growth_query = """
            SELECT 
                COUNT(CASE WHEN created_at >= datetime('now', '-30 days') THEN 1 END) as last_30_days,
                COUNT(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 END) as last_7_days,
                COUNT(CASE WHEN created_at >= datetime('now', '-1 day') THEN 1 END) as last_24_hours
            FROM users
            """
            
            growth_result = self.db.execute_query(growth_query, fetch_one=True)
            stats['growth'] = growth_result if growth_result else {}
            
            # Database size (SQLite only)
            if self.db.dev_mode:
                try:
                    db_size = os.path.getsize(self.db._local.conn.execute('PRAGMA database_list').fetchone()[2])
                    stats['database_size'] = {
                        'bytes': db_size,
                        'mb': round(db_size / (1024 * 1024), 2)
                    }
                except:
                    stats['database_size'] = {'bytes': 0, 'mb': 0}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_user_stats(self):
        """Get user-related statistics"""
        try:
            stats = {}
            
            # User counts by role
            role_query = """
            SELECT role, COUNT(*) as count 
            FROM users 
            WHERE is_active = TRUE 
            GROUP BY role
            """
            role_results = self.db.execute_query(role_query)
            stats['by_role'] = {row['role']: row['count'] for row in role_results or []}
            
            # User registration trends (last 12 months)
            registration_query = """
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as registrations
            FROM users 
            WHERE created_at >= datetime('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
            """
            registration_results = self.db.execute_query(registration_query)
            stats['registration_trend'] = registration_results or []
            
            # Active users (last 30 days)
            active_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM user_activity_log 
            WHERE created_at >= datetime('now', '-30 days')
            """
            active_result = self.db.execute_query(active_query, fetch_one=True)
            stats['active_users_30d'] = active_result['active_users'] if active_result else 0
            
            # Top users by activity
            top_users_query = """
            SELECT u.username, u.email, u.first_name, u.last_name, 
                   COUNT(ual.id) as activity_count,
                   MAX(ual.created_at) as last_activity
            FROM users u
            LEFT JOIN user_activity_log ual ON u.id = ual.user_id
            WHERE u.is_active = TRUE
            GROUP BY u.id
            ORDER BY activity_count DESC
            LIMIT 10
            """
            top_users_results = self.db.execute_query(top_users_query)
            stats['top_users'] = top_users_results or []
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    def get_activity_stats(self):
        """Get activity and usage statistics"""
        try:
            stats = {}
            
            # Activity by type (last 30 days)
            activity_query = """
            SELECT activity_type, COUNT(*) as count
            FROM user_activity_log 
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY activity_type
            ORDER BY count DESC
            """
            activity_results = self.db.execute_query(activity_query)
            stats['by_type'] = activity_results or []
            
            # Daily activity trend (last 30 days)
            daily_activity_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as activities,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_activity_log 
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            daily_results = self.db.execute_query(daily_activity_query)
            stats['daily_trend'] = daily_results or []
            
            # Search statistics
            search_query = """
            SELECT 
                search_type,
                COUNT(*) as total_searches,
                AVG(results_count) as avg_results,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_search_history 
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY search_type
            """
            search_results = self.db.execute_query(search_query)
            stats['searches'] = search_results or []
            
            # Popular search terms
            popular_terms_query = """
            SELECT search_query, COUNT(*) as frequency
            FROM user_search_history 
            WHERE created_at >= datetime('now', '-7 days') 
            AND search_query IS NOT NULL
            AND search_query != ''
            GROUP BY search_query
            ORDER BY frequency DESC
            LIMIT 20
            """
            popular_results = self.db.execute_query(popular_terms_query)
            stats['popular_searches'] = popular_results or []
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting activity stats: {e}")
            return {}
    
    def get_system_performance(self):
        """Get system performance metrics"""
        try:
            stats = {}
            
            # System resource usage
            stats['cpu_percent'] = psutil.cpu_percent(interval=1)
            stats['memory'] = {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            }
            stats['disk'] = {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
            
            # Application metrics
            stats['uptime'] = datetime.now() - datetime.fromtimestamp(psutil.Process().create_time())
            
            # Database connection info
            if hasattr(self.db, 'connection_pool') and self.db.connection_pool:
                stats['db_connections'] = {
                    'minconn': self.db.connection_pool.minconn,
                    'maxconn': self.db.connection_pool.maxconn,
                    # Note: getting current connections requires more complex pool inspection
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system performance: {e}")
            return {}
    
    def get_revenue_stats(self):
        """Get revenue and payment statistics"""
        try:
            stats = {}
            
            # Total revenue
            revenue_query = """
            SELECT 
                SUM(amount) as total_revenue,
                COUNT(*) as total_transactions,
                AVG(amount) as avg_transaction
            FROM user_payments 
            WHERE status = 'completed'
            """
            revenue_result = self.db.execute_query(revenue_query, fetch_one=True)
            if revenue_result:
                stats['total'] = {
                    'revenue': revenue_result['total_revenue'] or 0,
                    'transactions': revenue_result['total_transactions'] or 0,
                    'avg_transaction': revenue_result['avg_transaction'] or 0
                }
            
            # Revenue by service type
            service_query = """
            SELECT 
                service_type,
                SUM(amount) as revenue,
                COUNT(*) as transactions
            FROM user_payments 
            WHERE status = 'completed'
            GROUP BY service_type
            ORDER BY revenue DESC
            """
            service_results = self.db.execute_query(service_query)
            stats['by_service'] = service_results or []
            
            # Monthly revenue trend
            monthly_query = """
            SELECT 
                strftime('%Y-%m', created_at) as month,
                SUM(amount) as revenue,
                COUNT(*) as transactions
            FROM user_payments 
            WHERE status = 'completed' 
            AND created_at >= datetime('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
            """
            monthly_results = self.db.execute_query(monthly_query)
            stats['monthly_trend'] = monthly_results or []
            
            # Failed payments
            failed_query = """
            SELECT COUNT(*) as failed_count
            FROM user_payments 
            WHERE status = 'failed'
            AND created_at >= datetime('now', '-30 days')
            """
            failed_result = self.db.execute_query(failed_query, fetch_one=True)
            stats['failed_payments'] = failed_result['failed_count'] if failed_result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting revenue stats: {e}")
            return {}
    
    def get_api_usage_stats(self):
        """Get API usage statistics"""
        try:
            stats = {}
            
            # API calls by endpoint (last 30 days)
            endpoint_query = """
            SELECT 
                endpoint,
                COUNT(*) as requests,
                AVG(response_time) as avg_response_time,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors
            FROM api_usage_detailed 
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY endpoint
            ORDER BY requests DESC
            LIMIT 20
            """
            endpoint_results = self.db.execute_query(endpoint_query)
            stats['by_endpoint'] = endpoint_results or []
            
            # Daily API usage trend
            daily_api_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as requests,
                AVG(response_time) as avg_response_time
            FROM api_usage_detailed 
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            daily_results = self.db.execute_query(daily_api_query)
            stats['daily_trend'] = daily_results or []
            
            # Rate limiting stats
            rate_limit_query = """
            SELECT COUNT(*) as rate_limited_requests
            FROM api_usage_detailed 
            WHERE rate_limited = TRUE
            AND created_at >= datetime('now', '-30 days')
            """
            rate_limit_result = self.db.execute_query(rate_limit_query, fetch_one=True)
            stats['rate_limited'] = rate_limit_result['rate_limited_requests'] if rate_limit_result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            return {}
    
    def get_user_list(self, page=1, per_page=50, search='', role='', status=''):
        """Get paginated user list with filters"""
        try:
            conditions = ['1=1']  # Base condition
            params = []
            
            if search:
                conditions.append("(username LIKE ? OR email LIKE ? OR first_name LIKE ? OR last_name LIKE ?)")
                search_param = f"%{search}%"
                params.extend([search_param] * 4)
            
            if role:
                conditions.append("role = ?")
                params.append(role)
            
            if status == 'active':
                conditions.append("is_active = TRUE")
            elif status == 'inactive':
                conditions.append("is_active = FALSE")
            
            where_clause = " WHERE " + " AND ".join(conditions)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM users{where_clause}"
            count_result = self.db.execute_query(count_query, params, fetch_one=True)
            total = count_result['total'] if count_result else 0
            
            # Get paginated results
            offset = (page - 1) * per_page
            list_query = f"""
            SELECT id, username, email, first_name, last_name, role, is_active, 
                   email_verified, created_at, last_login, login_count
            FROM users{where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])
            
            users = self.db.execute_query(list_query, params) or []
            
            return {
                'users': users,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting user list: {e}")
            return {'users': [], 'total': 0, 'page': 1, 'per_page': per_page, 'pages': 0}
    
    def get_system_notifications(self, limit=50):
        """Get recent system notifications"""
        try:
            query = """
            SELECT * FROM system_notifications 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            return self.db.execute_query(query, [limit]) or []
        except Exception as e:
            logger.error(f"Error getting system notifications: {e}")
            return []
    
    def create_system_notification(self, notification_type, title, message, metadata=None):
        """Create a system notification"""
        try:
            query = """
            INSERT INTO system_notifications (notification_type, title, message, metadata, created_by)
            VALUES (?, ?, ?, ?, ?)
            """
            params = [
                notification_type,
                title,
                message,
                json.dumps(metadata) if metadata else None,
                current_user.id if current_user.is_authenticated else None
            ]
            self.db.execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Error creating system notification: {e}")
            return False

# Initialize admin dashboard
admin_dashboard = None

def init_admin_dashboard(db_manager, auth_manager):
    """Initialize admin dashboard"""
    global admin_dashboard
    admin_dashboard = AdminDashboard(db_manager, auth_manager)

# Routes
@admin_bp.route('/')
@admin_required
def dashboard():
    """Main admin dashboard"""
    stats = admin_dashboard.get_system_stats()
    notifications = admin_dashboard.get_system_notifications(limit=10)
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         notifications=notifications)

@admin_bp.route('/users')
@admin_required
def users():
    """User management page"""
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    user_data = admin_dashboard.get_user_list(
        page=page, 
        search=search, 
        role=role, 
        status=status
    )
    
    return render_template('admin/users.html', **user_data)

@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = admin_dashboard.get_system_stats()
    return jsonify(stats)

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        query = "UPDATE users SET is_active = NOT is_active WHERE id = ?"
        admin_dashboard.db.execute_query(query, [user_id])
        
        # Log the action
        admin_dashboard.auth.log_user_activity(current_user.id, 'admin_user_status_toggle', {
            'target_user_id': user_id,
            'action': 'toggle_status'
        })
        
        return jsonify({'success': True, 'message': 'User status updated'})
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>/change-role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    """Change user role"""
    try:
        new_role = request.json.get('role')
        if new_role not in ['user', 'moderator', 'admin']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        query = "UPDATE users SET role = ? WHERE id = ?"
        admin_dashboard.db.execute_query(query, [new_role, user_id])
        
        # Log the action
        admin_dashboard.auth.log_user_activity(current_user.id, 'admin_user_role_change', {
            'target_user_id': user_id,
            'new_role': new_role
        })
        
        return jsonify({'success': True, 'message': 'User role updated'})
    except Exception as e:
        logger.error(f"Error changing user role: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 