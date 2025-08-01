# Granular Admin Permissions System

## Overview
The FacultyFinder admin system now supports **Django-style granular permissions**, allowing different admin users to access specific sections based on their assigned roles. This provides fine-grained access control for different administrative functions.

## 🔐 Permission Types

### Core Admin Permissions
- **`can_manage_ai_requests`**: Access to [AI Requests Management](https://facultyfinder.io/admin/ai-requests)
- **`can_manage_database`**: Access to [Database Management](https://facultyfinder.io/admin/database)
- **`can_manage_users`**: Access to User Management (future)
- **`is_superuser`**: Full access to all admin features

## 👥 Pre-defined Admin Roles

### 1. **SUPERUSER** 
- **Description**: Full access to all admin features
- **Permissions**: AI Requests ✅ | Database ✅ | Users ✅ | Superuser ✅
- **Use Case**: System administrators, full admin access

### 2. **AI_ADMIN**
- **Description**: Can manage AI requests and payments only
- **Permissions**: AI Requests ✅ | Database ❌ | Users ❌ | Superuser ❌
- **Use Case**: AI service managers, payment processors

### 3. **DATABASE_ADMIN**
- **Description**: Can manage universities, professors, and database only
- **Permissions**: AI Requests ❌ | Database ✅ | Users ❌ | Superuser ❌
- **Use Case**: Academic data managers, university coordinators

### 4. **USER_MANAGER**
- **Description**: Can manage users only
- **Permissions**: AI Requests ❌ | Database ❌ | Users ✅ | Superuser ❌
- **Use Case**: User account administrators

### 5. **AI_DATABASE_ADMIN**
- **Description**: Can manage both AI requests and database
- **Permissions**: AI Requests ✅ | Database ✅ | Users ❌ | Superuser ❌
- **Use Case**: Technical administrators managing both AI and data

## 🚀 Implementation Features

### ✅ Route Protection
**AI Requests Routes** (require `can_manage_ai_requests`):
- `/admin/ai-requests` - AI requests management page
- `/api/v1/admin/ai-requests` - Get AI requests
- `/api/v1/admin/ai-requests/{id}/update-status` - Update request status
- `/api/v1/admin/ai-requests/stats` - AI requests statistics

**Database Routes** (require `can_manage_database`):
- `/admin/database` - Database management page
- `/api/v1/admin/universities` - University management
- `/api/v1/admin/professors` - Professor management
- `/api/v1/admin/countries` - Country data
- `/api/v1/admin/database/stats` - Database statistics

### ✅ Dynamic Navigation
The admin navigation adapts based on user permissions:

**Main Navigation Menu**:
```html
{% if current_user.is_admin() %}
    <li><a href="/admin/dashboard">Admin Dashboard</a></li>
    {% if current_user.has_permission('ai_requests') %}
        <li><a href="/admin/ai-requests">AI Requests</a></li>
    {% endif %}
    {% if current_user.has_permission('database') %}
        <li><a href="/admin/database">Database</a></li>
    {% endif %}
{% endif %}
```

**Admin Dashboard Buttons**:
- Only shows buttons for sections the user has access to
- Graceful handling when permissions are missing

### ✅ Permission Checking
**User Model Methods**:
```python
user.has_permission('ai_requests')      # Check specific permission
user.has_permission('database')         # Check database access
user.get_admin_permissions()            # Get list of all permissions
user.is_admin()                         # Check any admin access
```

## 🛠️ Setting Up Admin Users

### Method 1: Interactive Permission Setup
Use the new granular permission script:

```bash
# Upload to your server
scp create_admin_user_with_permissions.py your-server:/path/to/facultyfinder/

# Run on your server
cd /path/to/facultyfinder/
python3 create_admin_user_with_permissions.py
```

**Interactive Flow**:
1. Enter user details (username, email, password, name)
2. Select from pre-defined admin roles
3. Confirm permission assignment
4. User created with specific access levels

### Method 2: Database Setup
**Add Permission Columns** (automatically handled by scripts):
```sql
ALTER TABLE users ADD COLUMN can_manage_ai_requests BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN can_manage_database BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN can_manage_users BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE;
```

**Manual Permission Assignment**:
```sql
-- Make user an AI admin
UPDATE users SET 
    can_manage_ai_requests = TRUE,
    role = 'admin',
    is_admin = TRUE
WHERE username = 'ai_admin_user';

-- Make user a database admin  
UPDATE users SET 
    can_manage_database = TRUE,
    role = 'admin', 
    is_admin = TRUE
WHERE username = 'db_admin_user';

-- Make user a superuser
UPDATE users SET 
    can_manage_ai_requests = TRUE,
    can_manage_database = TRUE,
    can_manage_users = TRUE,
    is_superuser = TRUE,
    role = 'admin',
    is_admin = TRUE  
WHERE username = 'super_admin';
```

## 🔍 Access Control Examples

### Example 1: AI Admin User
**User**: `ai_manager`
**Role**: `AI_ADMIN`
**Access**:
- ✅ Can access https://facultyfinder.io/admin/dashboard
- ✅ Can access https://facultyfinder.io/admin/ai-requests
- ❌ Cannot access https://facultyfinder.io/admin/database
- ❌ Gets 403 Forbidden on database routes

### Example 2: Database Admin User  
**User**: `data_manager`
**Role**: `DATABASE_ADMIN`
**Access**:
- ✅ Can access https://facultyfinder.io/admin/dashboard
- ❌ Cannot access https://facultyfinder.io/admin/ai-requests  
- ✅ Can access https://facultyfinder.io/admin/database
- ❌ Gets 403 Forbidden on AI request routes

### Example 3: Superuser
**User**: `super_admin`
**Role**: `SUPERUSER`
**Access**:
- ✅ Can access all admin areas
- ✅ Sees all navigation options
- ✅ Has full administrative control

## 🎯 Use Cases

### Academic Institution Setup
**Scenario**: University wants to manage their own data
```bash
# Create database admin for university
Role: DATABASE_ADMIN
Access: Can add/edit professors and university info
Cannot: Access AI payment data or user accounts
```

### AI Service Management
**Scenario**: Separate team manages AI features and billing
```bash
# Create AI admin for AI team
Role: AI_ADMIN  
Access: Can monitor AI requests, manage payments
Cannot: Modify professor/university data
```

### Multi-tenant Administration
**Scenario**: Different teams manage different aspects
```bash
# Academic team
Role: DATABASE_ADMIN
Access: University and professor data only

# AI team  
Role: AI_ADMIN
Access: AI requests and payments only

# System admin
Role: SUPERUSER
Access: Everything
```

## 🔧 Technical Implementation

### FastAPI Dependencies
```python
async def require_ai_requests_permission(request: Request) -> User:
    """Require AI requests management permission"""
    user = await require_auth(request)
    if not user.has_permission('ai_requests'):
        raise HTTPException(status_code=403, detail="AI requests permission required")
    return user

async def require_database_permission(request: Request) -> User:
    """Require database management permission"""  
    user = await require_auth(request)
    if not user.has_permission('database'):
        raise HTTPException(status_code=403, detail="Database permission required")
    return user
```

### Route Protection
```python
@app.get("/admin/ai-requests")
async def admin_ai_requests(user: User = Depends(require_ai_requests_permission)):
    # Only users with can_manage_ai_requests=True can access
    
@app.get("/admin/database")  
async def admin_database(user: User = Depends(require_database_permission)):
    # Only users with can_manage_database=True can access
```

## 🛡️ Security Features

### ✅ Principle of Least Privilege
- Users only get minimum required permissions
- No unnecessary access to sensitive areas
- Clear separation of concerns

### ✅ Fail-Safe Defaults
- New users have no admin permissions by default
- Permission checks fail closed (deny by default)
- Explicit permission grants required

### ✅ Audit Trail Ready
- All permission checks are logged
- Clear user role assignments in database
- Ready for audit logging implementation

## 📊 Permission Matrix

| Role | Dashboard | AI Requests | Database | Users | Superuser |
|------|-----------|-------------|----------|-------|-----------|
| **SUPERUSER** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AI_ADMIN** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **DATABASE_ADMIN** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **USER_MANAGER** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **AI_DATABASE_ADMIN** | ✅ | ✅ | ✅ | ❌ | ❌ |

## 🔄 Migration from Simple Admin

### Existing Admin Users
If you have existing admin users, run the permission script to update them:

```bash
python3 create_admin_user_with_permissions.py
# Select existing username
# Choose appropriate role
# Script will update permissions
```

### Backward Compatibility
- Existing `role = 'admin'` users maintain access
- `is_admin = TRUE` users maintain access  
- No breaking changes to existing functionality

---

## 🎉 Benefits

✅ **Separation of Concerns**: Different teams can manage different areas
✅ **Security**: Reduced attack surface through limited permissions  
✅ **Compliance**: Better audit trails and access controls
✅ **Scalability**: Easy to add new admin roles as needed
✅ **Flexibility**: Fine-grained control over admin access
✅ **User Experience**: Clean navigation showing only relevant options

The granular admin permission system provides enterprise-level access control while maintaining the simplicity of the original admin system! 🚀 