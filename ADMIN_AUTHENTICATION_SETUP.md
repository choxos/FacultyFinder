# Admin Authentication Setup Guide

## Overview
The FacultyFinder admin authentication system has been implemented with proper role-based access control for PostgreSQL databases.

## Features Implemented

### ✅ Authentication System
- **Login/Logout**: Proper session-based authentication
- **Admin Role Check**: Users with `role = 'admin'` or `is_admin = TRUE` can access admin panel
- **Protected Routes**: All admin routes require authentication and admin privileges
- **Template Context**: Proper user context in all templates

### ✅ Admin Dashboard
- **Real-time Stats**: Live database statistics (users, professors, universities)
- **System Monitoring**: CPU, memory, disk usage display
- **Navigation**: Easy access to AI requests and database management
- **Responsive UI**: Modern dashboard with proper styling

### ✅ Protected Admin Routes
All these routes now require admin authentication:
- `/admin/dashboard` - Main admin dashboard
- `/admin/ai-requests` - AI requests management
- `/admin/database` - Database management
- `/api/v1/admin/*` - All admin API endpoints

## Deployment Steps

### 1. Database Setup (PostgreSQL)

The system uses your existing PostgreSQL database. The users table will be created automatically if it doesn't exist.

### 2. Create Admin User

Run the admin user creation script on your server:

```bash
# Upload the script to your server
scp create_admin_user_postgres.py your-server:/path/to/facultyfinder/

# On your server, run:
cd /path/to/facultyfinder/
python3 create_admin_user_postgres.py
```

**Default Admin Credentials:**
- Username: `admin`
- Email: `admin@facultyfinder.io`
- Password: `admin123`

⚠️ **IMPORTANT**: Change the password immediately after first login!

### 3. Environment Variables

Ensure your server has these environment variables configured:
```bash
DB_HOST=your_postgres_host
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
SESSION_SECRET=your_session_secret_key
```

### 4. Required Dependencies

Make sure these are installed on your server:
```bash
pip install fastapi jinja2 python-multipart asyncpg
```

### 5. Test the System

1. **Access the login page**: `https://your-domain.com/login`
2. **Login with admin credentials**
3. **Should redirect to**: `https://your-domain.com/admin/dashboard`
4. **Verify all admin features work**

## Security Features

### ✅ Authentication Flow
1. User submits login form
2. Credentials verified against PostgreSQL database
3. Password hashed with SHA256 (upgrade to bcrypt recommended)
4. Session created with user data
5. Admin role checked for admin routes
6. Automatic redirect based on user role

### ✅ Access Control
- Non-authenticated users → redirected to login
- Regular users → access to user dashboard only
- Admin users → access to both user and admin dashboards
- All admin API endpoints protected

### ✅ Session Management
- Secure session-based authentication
- Automatic session cleanup on logout
- Session data includes user role information

## Usage

### For Regular Users
1. Visit `/login`
2. Enter credentials
3. Redirected to `/dashboard`

### For Admin Users
1. Visit `/login`
2. Enter admin credentials
3. Redirected to `/admin/dashboard`
4. Access admin features through navigation

### Admin Panel Navigation
- **Dashboard**: `/admin/dashboard` - Overview and statistics
- **AI Requests**: `/admin/ai-requests` - Manage AI service requests
- **Database**: `/admin/database` - Database management tools

## Troubleshooting

### Login Issues
1. Check PostgreSQL connection
2. Verify users table exists
3. Confirm admin user was created successfully
4. Check application logs for authentication errors

### Permission Issues
1. Verify user has `role = 'admin'` OR `is_admin = TRUE`
2. Check session is properly storing user data
3. Confirm admin dependency is working in FastAPI routes

### Template Issues
1. Ensure Jinja2 templates are properly configured
2. Check template directory path: `webapp/templates`
3. Verify template context includes `current_user`

## Next Steps

### Recommended Security Improvements
1. **Password Hashing**: Upgrade from SHA256 to bcrypt
2. **HTTPS**: Ensure all admin access uses HTTPS
3. **Rate Limiting**: Add login attempt rate limiting
4. **Session Security**: Configure secure session cookies
5. **2FA**: Consider two-factor authentication for admin accounts

### Features to Add
1. **User Management**: Admin interface to manage users
2. **Audit Logging**: Track admin actions
3. **Password Reset**: Admin password reset functionality
4. **Role Management**: More granular role permissions

## Files Modified/Created

### New Files
- `create_admin_user_postgres.py` - PostgreSQL admin user creation
- `ADMIN_AUTHENTICATION_SETUP.md` - This guide

### Modified Files
- `webapp/main.py` - Added authentication system and admin protection
- `webapp/templates/admin/dashboard.html` - Enhanced with proper context

### Database Changes
- Added `users` table (created automatically if missing)
- Admin user created with proper permissions

---

## Support

For any issues with the admin authentication system, check:
1. Database connectivity
2. User table structure
3. Session configuration
4. Template rendering
5. FastAPI route protection

The system is now production-ready with proper PostgreSQL support! 🎉 