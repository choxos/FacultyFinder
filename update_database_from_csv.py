#!/usr/bin/env python3
"""
FacultyFinder Database Update Script
Easy way to update the database when CSV files are modified
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
import argparse
from datetime import datetime
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_db_config():
    """Load database configuration"""
    # Try multiple .env file locations
    env_files = ['/var/www/ff/.env', '.env', '.env.production']
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            break
    
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

def connect_database():
    """Connect to PostgreSQL database"""
    config = load_db_config()
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        logger.info("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("Please check your .env file and database credentials")
        return None

def generate_professor_id(university_code, sequence_id):
    """Generate professor_id from university_code and sequence_id"""
    return f"{university_code}-{sequence_id:05d}"

def incremental_update_universities(csv_file='data/university_codes.csv'):
    """Perform incremental update of university data including new address fields"""
    logger.info("🔄 Starting incremental university update...")
    
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSV file not found: {csv_file}")
        return False
    
    conn = connect_database()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Read CSV data
        df = pd.read_csv(csv_file)
        logger.info(f"📊 Loaded {len(df)} university records from CSV")
        
        # Check if address columns exist in database
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'universities' AND column_name IN ('building_number', 'street', 'postal_code')
        """)
        address_columns = [row[0] for row in cursor.fetchall()]
        has_address_columns = len(address_columns) == 3
        
        if not has_address_columns:
            logger.info("⚠️ Address columns not found. Run update_university_address_schema.py first")
        
        updated_count = 0
        
        # Process each row in CSV
        for index, row in df.iterrows():
            university_code = row.get('university_code')
            university_name = row.get('university_name')
            
            if pd.isna(university_code) or pd.isna(university_name):
                continue
            
            # Check if university exists
            cursor.execute("SELECT id FROM universities WHERE university_code = %s", (university_code,))
            existing_uni = cursor.fetchone()
            
            if existing_uni:
                # Update existing university
                if has_address_columns:
                    update_sql = """
                        UPDATE universities 
                        SET name = %s, country = %s, province_state = %s, city = %s,
                            building_number = %s, street = %s, postal_code = %s,
                            website = %s, university_type = %s, languages = %s, year_established = %s
                        WHERE university_code = %s
                    """
                    cursor.execute(update_sql, (
                        university_name, row.get('country'), row.get('province_state'), row.get('city'),
                        row.get('building_number'), row.get('street'), row.get('postal_code'),
                        row.get('website'), row.get('type'), row.get('language'), 
                        row.get('established') if not pd.isna(row.get('established')) else None,
                        university_code
                    ))
                else:
                    update_sql = """
                        UPDATE universities 
                        SET name = %s, country = %s, province_state = %s, city = %s,
                            website = %s, university_type = %s, languages = %s, year_established = %s
                        WHERE university_code = %s
                    """
                    cursor.execute(update_sql, (
                        university_name, row.get('country'), row.get('province_state'), row.get('city'),
                        row.get('website'), row.get('type'), row.get('language'), 
                        row.get('established') if not pd.isna(row.get('established')) else None,
                        university_code
                    ))
                
                updated_count += 1
                logger.info(f"🔄 Updated: {university_name}")
            else:
                # Insert new university
                if has_address_columns:
                    insert_sql = """
                        INSERT INTO universities (
                            university_code, name, country, province_state, city,
                            building_number, street, postal_code,
                            website, university_type, languages, year_established
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        university_code, university_name, row.get('country'), 
                        row.get('province_state'), row.get('city'),
                        row.get('building_number'), row.get('street'), row.get('postal_code'),
                        row.get('website'), row.get('type'), row.get('language'), 
                        row.get('established') if not pd.isna(row.get('established')) else None
                    ))
                else:
                    insert_sql = """
                        INSERT INTO universities (
                            university_code, name, country, province_state, city,
                            website, university_type, languages, year_established
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        university_code, university_name, row.get('country'), 
                        row.get('province_state'), row.get('city'),
                        row.get('website'), row.get('type'), row.get('language'), 
                        row.get('established') if not pd.isna(row.get('established')) else None
                    ))
                
                updated_count += 1
                logger.info(f"➕ Added: {university_name}")
        
        conn.commit()
        logger.info(f"✅ University update complete! Updated/Added: {updated_count}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ University update failed: {e}")
        return False
    finally:
        conn.close()

def incremental_update_faculty(csv_file='data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv'):
    """Perform incremental update of faculty data"""
    logger.info("🔄 Starting incremental faculty update...")
    
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSV file not found: {csv_file}")
        return False
    
    conn = connect_database()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Read CSV data
        df = pd.read_csv(csv_file)
        logger.info(f"📊 Loaded {len(df)} records from CSV")
        
        # Get existing professors from database
        cursor.execute("SELECT university_code, professor_id, name FROM professors")
        existing_profs = {(row['university_code'], row['professor_id']): row for row in cursor.fetchall()}
        
        updated_count = 0
        added_count = 0
        
        # Process each row in CSV
        for index, row in df.iterrows():
            university_code = row.get('university_code')
            name = row.get('name')
            
            if pd.isna(university_code) or pd.isna(name):
                continue
            
            # Find or assign professor_id
            professor_id = None
            for (uc, pid), prof in existing_profs.items():
                if uc == university_code and prof['name'] == name:
                    professor_id = pid
                    break
            
            if professor_id is None:
                # New professor - find next available ID
                cursor.execute("""
                    SELECT COALESCE(MAX(professor_id), 0) + 1 
                    FROM professors 
                    WHERE university_code = %s
                """, (university_code,))
                professor_id = cursor.fetchone()[0]
                
                # Insert new professor
                insert_query = """
                    INSERT INTO professors (
                        professor_id, name, first_name, last_name, middle_names, other_name,
                        research_areas, university_code, department, position, full_time, adjunct,
                        uni_email, other_email, uni_page, website, twitter, linkedin
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                cursor.execute(insert_query, (
                    professor_id, name, row.get('first_name'), row.get('last_name'),
                    row.get('middle_names'), row.get('other_name'), str(row.get('research_areas', '')),
                    university_code, row.get('department'), row.get('position'),
                    row.get('full_time', False), row.get('adjunct', False),
                    row.get('uni_email'), row.get('other_email'), row.get('uni_page'),
                    row.get('website'), row.get('twitter'), row.get('linkedin')
                ))
                added_count += 1
                logger.info(f"➕ Added: {name} (ID: {professor_id})")
            else:
                # Update existing professor
                update_query = """
                    UPDATE professors SET 
                        first_name = %s, last_name = %s, middle_names = %s, other_name = %s,
                        research_areas = %s, department = %s, position = %s, full_time = %s, adjunct = %s,
                        uni_email = %s, other_email = %s, uni_page = %s, website = %s, twitter = %s, linkedin = %s
                    WHERE university_code = %s AND professor_id = %s
                """
                cursor.execute(update_query, (
                    row.get('first_name'), row.get('last_name'), row.get('middle_names'),
                    row.get('other_name'), str(row.get('research_areas', '')), row.get('department'),
                    row.get('position'), row.get('full_time', False), row.get('adjunct', False),
                    row.get('uni_email'), row.get('other_email'), row.get('uni_page'),
                    row.get('website'), row.get('twitter'), row.get('linkedin'),
                    university_code, professor_id
                ))
                updated_count += 1
                logger.info(f"🔄 Updated: {name} (ID: {professor_id})")
        
        conn.commit()
        logger.info(f"✅ Update complete! Added: {added_count}, Updated: {updated_count}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Update failed: {e}")
        return False
    finally:
        conn.close()

def full_rebuild():
    """Perform complete database rebuild"""
    logger.info("🗑️ Starting full database rebuild...")
    
    # Use existing clean rebuild script
    import subprocess
    try:
        result = subprocess.run(['python3', 'clean_rebuild_database.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Full rebuild completed successfully!")
            return True
        else:
            logger.error(f"❌ Full rebuild failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to run rebuild script: {e}")
        return False

def check_database_status():
    """Check current database status"""
    logger.info("📊 Checking database status...")
    
    conn = connect_database()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get counts
        cursor.execute("SELECT COUNT(*) as count FROM professors")
        prof_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM universities")
        uni_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT university_code) as count FROM professors")
        active_unis = cursor.fetchone()['count']
        
        logger.info(f"📈 Database Status:")
        logger.info(f"   📋 Professors: {prof_count}")
        logger.info(f"   🏫 Universities: {uni_count}")
        logger.info(f"   🎯 Active Universities: {active_unis}")
        
        # Show recent updates
        cursor.execute("""
            SELECT name, university_code, professor_id, position
            FROM professors 
            ORDER BY id DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        logger.info(f"📋 Recent entries:")
        for prof in recent:
            prof_id = generate_professor_id(prof['university_code'], prof['professor_id'])
            logger.info(f"   • {prof['name']} ({prof_id}) - {prof['position']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return False
    finally:
        conn.close()

def restart_service():
    """Restart the FacultyFinder service"""
    logger.info("🔄 Restarting FacultyFinder service...")
    
    import subprocess
    try:
        # Try to restart the service
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'facultyfinder.service'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Service restarted successfully!")
            
            # Check service status
            result = subprocess.run(['sudo', 'systemctl', 'status', 'facultyfinder.service', '--no-pager'], 
                                  capture_output=True, text=True)
            if 'active (running)' in result.stdout:
                logger.info("✅ Service is running correctly!")
            else:
                logger.warning("⚠️ Service may have issues. Check with: sudo systemctl status facultyfinder.service")
            
            return True
        else:
            logger.error(f"❌ Failed to restart service: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Service restart failed: {e}")
        logger.info("💡 Try manually: sudo systemctl restart facultyfinder.service")
        return False

def main():
    parser = argparse.ArgumentParser(description='Update FacultyFinder database from CSV files')
    parser.add_argument('--mode', choices=['incremental', 'full', 'status', 'universities'], default='incremental',
                       help='Update mode: incremental (default), full rebuild, status check, or universities')
    parser.add_argument('--csv', default='data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv',
                       help='Path to CSV file (faculty or university)')
    parser.add_argument('--restart', action='store_true',
                       help='Restart the service after update')
    
    args = parser.parse_args()
    
    logger.info("🚀 FacultyFinder Database Update Tool")
    logger.info("=====================================")
    
    success = False
    
    if args.mode == 'status':
        success = check_database_status()
    elif args.mode == 'incremental':
        logger.info(f"📁 Using CSV file: {args.csv}")
        success = incremental_update_faculty(args.csv)
    elif args.mode == 'universities':
        csv_file = args.csv if args.csv != 'data/mcmaster_hei_faculty.csv' else 'data/university_codes.csv'
        logger.info(f"🏫 Updating universities from: {csv_file}")
        success = incremental_update_universities(csv_file)
    elif args.mode == 'full':
        success = full_rebuild()
    
    if success and args.restart:
        restart_service()
    
    if success:
        logger.info("🎉 Database update completed successfully!")
        logger.info("🌐 Your website should now reflect the changes")
    else:
        logger.error("❌ Database update failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
