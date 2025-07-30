#!/usr/bin/env python3
"""
Database Connection and Universities API Diagnostic Tool
Helps identify why the universities page is showing 500 errors
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_db_config():
    """Load database configuration from .env files"""
    env_files = ['/var/www/ff/.env', '.env', '.env.production']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"✅ Loaded environment from: {env_file}")
            break
    else:
        logger.warning("⚠️ No .env file found")
    
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

def test_database_connection():
    """Test PostgreSQL database connection"""
    logger.info("🔌 Testing database connection...")
    
    config = load_db_config()
    
    # Check if credentials are loaded
    missing_creds = [k for k, v in config.items() if not v]
    if missing_creds:
        logger.error(f"❌ Missing database credentials: {missing_creds}")
        return False
    
    logger.info(f"📋 Connection details: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
    
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = True
        logger.info("✅ Database connection successful")
        
        # Test basic query
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        logger.info(f"📊 PostgreSQL version: {version['version']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_database_tables():
    """Check if required tables exist and have data"""
    logger.info("📊 Checking database tables and data...")
    
    config = load_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check tables existence
        tables_to_check = ['universities', 'professors']
        
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            
            exists = cursor.fetchone()['exists']
            
            if exists:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                logger.info(f"✅ Table '{table}': {count} records")
                
                if table == 'universities' and count > 0:
                    # Show sample universities
                    cursor.execute("SELECT name, university_code, country FROM universities LIMIT 3")
                    samples = cursor.fetchall()
                    for sample in samples:
                        logger.info(f"   📍 {sample['name']} ({sample['university_code']}) - {sample['country']}")
                        
                elif table == 'professors' and count > 0:
                    # Show sample professors
                    cursor.execute("SELECT name, university_code FROM professors LIMIT 3")
                    samples = cursor.fetchall()
                    for sample in samples:
                        logger.info(f"   👨‍🏫 {sample['name']} - {sample['university_code']}")
            else:
                logger.error(f"❌ Table '{table}' does not exist")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to check tables: {e}")
        return False

def test_universities_api():
    """Test the universities API endpoint"""
    logger.info("🌐 Testing universities API endpoint...")
    
    api_urls = [
        'http://localhost:8008/api/v1/universities?per_page=1',
        'http://127.0.0.1:8008/api/v1/universities?per_page=1'
    ]
    
    for url in api_urls:
        try:
            logger.info(f"📡 Testing: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ API working! Returned {len(data.get('universities', []))} universities")
                if data.get('universities'):
                    uni = data['universities'][0]
                    logger.info(f"   📍 Sample: {uni.get('name')} - {uni.get('faculty_count')} faculty")
                return True
            else:
                logger.error(f"❌ API returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️ Could not connect to {url} (service may not be running)")
        except Exception as e:
            logger.error(f"❌ API test failed: {e}")
    
    return False

def check_data_files():
    """Check if faculty data files exist in new location"""
    logger.info("📁 Checking data file locations...")
    
    files_to_check = [
        'data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv',
        'data/university_codes.csv'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / 1024  # KB
            logger.info(f"✅ Found: {file_path} ({size:.1f} KB)")
            
            # Check line count for CSV files
            if file_path.endswith('.csv'):
                with open(file_path, 'r') as f:
                    lines = sum(1 for _ in f)
                logger.info(f"   📊 {lines} lines in file")
        else:
            logger.error(f"❌ Missing: {file_path}")

def check_service_status():
    """Check if FastAPI service is running"""
    logger.info("🚀 Checking FastAPI service status...")
    
    try:
        response = requests.get('http://localhost:8008/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ FastAPI service is running: {data}")
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error("❌ FastAPI service is not running or not accessible")
    except Exception as e:
        logger.error(f"❌ Service check failed: {e}")

def main():
    """Run all diagnostic checks"""
    logger.info("🔍 FacultyFinder Database & API Diagnostic Tool")
    logger.info("=" * 50)
    
    checks = [
        ("Database Connection", test_database_connection),
        ("Database Tables & Data", check_database_tables),
        ("Data Files", check_data_files),
        ("FastAPI Service", check_service_status),
        ("Universities API", test_universities_api),
    ]
    
    results = {}
    
    for check_name, check_function in checks:
        logger.info(f"\n🔍 {check_name}")
        logger.info("-" * 30)
        try:
            results[check_name] = check_function()
        except Exception as e:
            logger.error(f"❌ {check_name} failed: {e}")
            results[check_name] = False
    
    # Summary
    logger.info("\n📋 DIAGNOSTIC SUMMARY")
    logger.info("=" * 30)
    
    for check_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {check_name}")
    
    # Recommendations
    logger.info("\n💡 RECOMMENDATIONS")
    logger.info("=" * 20)
    
    if not results.get("Database Connection"):
        logger.info("🔧 Database connection failed:")
        logger.info("   1. Check .env file exists and has correct credentials")
        logger.info("   2. Ensure PostgreSQL service is running")
        logger.info("   3. Verify database exists and user has permissions")
    
    if not results.get("Database Tables & Data"):
        logger.info("🔧 Database tables missing or empty:")
        logger.info("   1. Run: python3 update_database_from_csv.py --mode full")
        logger.info("   2. Or: ./update_db.sh full")
    
    if not results.get("FastAPI Service"):
        logger.info("🔧 FastAPI service not running:")
        logger.info("   1. Check: sudo systemctl status facultyfinder.service")
        logger.info("   2. Restart: sudo systemctl restart facultyfinder.service")
        logger.info("   3. Check logs: sudo journalctl -u facultyfinder.service -n 20")
    
    if not results.get("Universities API"):
        logger.info("🔧 Universities API failing:")
        logger.info("   1. Check database has university and professor data")
        logger.info("   2. Check FastAPI service logs for SQL errors")
        logger.info("   3. Test API directly: curl http://localhost:8008/api/v1/universities?per_page=1")

if __name__ == "__main__":
    main() 