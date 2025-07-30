# PostgreSQL Schema Migration Guide

## 🚨 **Issue Encountered**

The original `database/schema.sql` file was designed for **SQLite** but you're deploying to **PostgreSQL**. This causes multiple syntax errors:

```
ERROR: syntax error at or near "AUTOINCREMENT"
```

## 🔧 **Root Cause**

PostgreSQL uses different syntax compared to SQLite:

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Auto-increment | `AUTOINCREMENT` | `SERIAL` or `GENERATED ALWAYS AS IDENTITY` |
| Boolean | `BOOLEAN` | `BOOLEAN` (same) |
| Text search | Limited | Full GIN indexes with `to_tsvector` |
| Conflict handling | `INSERT OR IGNORE` | `ON CONFLICT DO NOTHING` |

## ✅ **Solution Provided**

I've created **PostgreSQL-compatible** versions:

### **1. New PostgreSQL Schema**
- **File**: `database/schema_postgresql.sql`
- **Features**:
  - ✅ Uses `SERIAL` instead of `AUTOINCREMENT`
  - ✅ Proper foreign key relationships
  - ✅ Full-text search indexes with GIN
  - ✅ PostgreSQL-optimized data types
  - ✅ Includes all tables for full functionality

### **2. Deployment Script**
- **File**: `deploy_postgresql_schema.sh`
- **Features**:
  - ✅ Automatic environment loading
  - ✅ Error handling and verification
  - ✅ Post-deployment testing
  - ✅ Clear status reporting

## 🚀 **How to Deploy**

### **Option 1: Use the New Deployment Script (Recommended)**

```bash
# On your VPS
cd /var/www/ff
./deploy_postgresql_schema.sh
```

### **Option 2: Manual Deployment**

```bash
# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Run PostgreSQL schema
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -f database/schema_postgresql.sql
```

## 📊 **What Gets Created**

### **Core Tables**
- ✅ `universities` - University information with address fields
- ✅ `professors` - Faculty data with research areas
- ✅ `publications` - Publication metadata
- ✅ `author_publications` - Author-publication relationships

### **Advanced Features**
- ✅ `journals` - Journal metrics and rankings
- ✅ `citation_networks` - Citation analysis
- ✅ `research_areas` - Taxonomy for research fields
- ✅ `users` - Authentication system
- ✅ `crypto_payments` - Payment processing

### **Performance Optimizations**
- ✅ **GIN indexes** for full-text search
- ✅ **B-tree indexes** for common queries
- ✅ **Partial indexes** for active records
- ✅ **Compound indexes** for complex queries

## 🔄 **Data Migration**

After schema deployment, migrate your existing data:

### **1. Export from SQLite (if applicable)**
```bash
sqlite3 database/facultyfinder_dev.db .dump > sqlite_export.sql
```

### **2. Use Data Migration Scripts**
```bash
# Use existing migration tools
python data_migration_system.py --target postgresql
```

### **3. Verify Data**
```bash
# Check record counts
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
SELECT 
    (SELECT COUNT(*) FROM universities) as universities,
    (SELECT COUNT(*) FROM professors) as professors,
    (SELECT COUNT(*) FROM publications) as publications;
"
```

## 🎯 **Expected Results**

After successful deployment:
- ✅ **No more AUTOINCREMENT errors**
- ✅ **All tables created successfully**
- ✅ **Foreign key constraints working**
- ✅ **Indexes optimized for performance**
- ✅ **Ready for PubMed integration**
- ✅ **Full API functionality available**

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Permission Denied**
```bash
chmod +x deploy_postgresql_schema.sh
```

#### **2. Environment Variables Not Loaded**
```bash
# Check .env file exists and has correct format
cat .env | grep DB_
```

#### **3. Connection Refused**
```bash
# Test PostgreSQL connection
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "SELECT version();"
```

#### **4. Tables Already Exist**
The schema uses `CREATE TABLE IF NOT EXISTS` so it's safe to re-run.

## 📞 **Support**

If you encounter issues:
1. **Check logs**: Look for specific error messages
2. **Verify credentials**: Ensure database connection works
3. **Test step-by-step**: Run individual queries to isolate issues

## 🎉 **Success!**

Once deployed, your PostgreSQL database will be fully compatible with:
- ✅ **FastAPI application**
- ✅ **PubMed integration** 
- ✅ **Homepage and all pages**
- ✅ **Publication search and analysis**
- ✅ **User authentication**
- ✅ **Payment processing**

Your FacultyFinder application is now ready for production deployment! 🚀 