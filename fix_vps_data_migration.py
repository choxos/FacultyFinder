#!/usr/bin/env python3
"""
Fix data migration issues on VPS
Diagnoses and fixes foreign key constraint violations and data mismatches
"""

import psycopg2
import csv
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/var/www/ff/.env')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def diagnose_database():
    """Diagnose current database state"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("🔍 Diagnosing database state...")
    
    # Check current record counts
    tables = ['universities', 'professors', 'publications', 'journals']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"   {table}: {count} records")
        except Exception as e:
            logger.warning(f"   {table}: Error - {e}")
    
    # Check for CA-ON-002 specifically
    cursor.execute("SELECT code, name FROM universities WHERE code = 'CA-ON-002'")
    result = cursor.fetchone()
    if result:
        logger.info(f"✅ Found CA-ON-002: {result[1]}")
    else:
        logger.error("❌ CA-ON-002 not found in universities table!")
    
    # Check first 5 universities
    cursor.execute("SELECT code, name FROM universities LIMIT 5")
    results = cursor.fetchall()
    logger.info("📋 First 5 universities in database:")
    for code, name in results:
        logger.info(f"   {code}: {name}")
    
    conn.close()

def clear_and_reimport_universities():
    """Clear universities table and reimport from CSV"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("🗑️ Clearing universities table...")
    cursor.execute("TRUNCATE TABLE universities CASCADE")
    conn.commit()
    
    logger.info("📚 Re-importing universities from CSV...")
    
    # Try different possible CSV files and column names
    csv_files = [
        '/var/www/ff/data_import/university_codes.csv',
        '/var/www/ff/data/university_codes.csv'
    ]
    
    csv_file = None
    for file_path in csv_files:
        if os.path.exists(file_path):
            csv_file = file_path
            break
    
    if not csv_file:
        logger.error("❌ No university CSV file found!")
        return False
    
    logger.info(f"📖 Reading from: {csv_file}")
    
    # Read and inspect CSV structure
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        logger.info(f"📊 CSV columns: {fieldnames}")
        
        # Determine column mappings
        code_col = None
        name_col = None
        country_col = None
        
        for col in fieldnames:
            if 'code' in col.lower():
                code_col = col
            elif 'name' in col.lower() or 'university' in col.lower():
                name_col = col
            elif 'country' in col.lower():
                country_col = col
        
        logger.info(f"🗂️ Using columns - Code: {code_col}, Name: {name_col}, Country: {country_col}")
        
        # Import universities
        count = 0
        for row in reader:
            try:
                code = row.get(code_col, '').strip()
                name = row.get(name_col, '').strip()
                country = row.get(country_col, 'Unknown').strip()
                
                if code and name:
                    cursor.execute("""
                        INSERT INTO universities (code, name, country, website, type, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (code) DO NOTHING
                    """, (code, name, country, '', 'public', 'active'))
                    count += 1
                    
                    if code == 'CA-ON-002':
                        logger.info(f"✅ Found and importing CA-ON-002: {name}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Error importing row {row}: {e}")
        
        conn.commit()
        logger.info(f"✅ Imported {count} universities")
    
    conn.close()
    return True

def reimport_professors():
    """Re-import professors after fixing universities"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("👥 Re-importing professors...")
    
    # Clear professors table
    cursor.execute("TRUNCATE TABLE professors CASCADE")
    conn.commit()
    
    # Try different possible CSV files
    csv_files = [
        '/var/www/ff/data_import/mcmaster_experts_summary.csv',
        '/var/www/ff/data/mcmaster_experts_summary.csv'
    ]
    
    csv_file = None
    for file_path in csv_files:
        if os.path.exists(file_path):
            csv_file = file_path
            break
    
    if not csv_file:
        logger.error("❌ No professor CSV file found!")
        return False
    
    logger.info(f"📖 Reading professors from: {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        logger.info(f"📊 Professor CSV columns: {fieldnames}")
        
        count = 0
        for row in reader:
            try:
                # Map common column variations
                name = (row.get('name') or row.get('Name') or row.get('full_name') or '').strip()
                university_code = (row.get('university_code') or row.get('University_Code') or 'CA-ON-002').strip()
                department = (row.get('department') or row.get('Department') or '').strip()
                position = (row.get('position') or row.get('Position') or row.get('title') or '').strip()
                email = (row.get('email') or row.get('Email') or '').strip()
                
                if name:
                    cursor.execute("""
                        INSERT INTO professors (name, university_code, department, position, email, employment_type, research_areas)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name, university_code) DO NOTHING
                    """, (name, university_code, department, position, email, 'full_time', ''))
                    count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Error importing professor {row}: {e}")
        
        conn.commit()
        logger.info(f"✅ Imported {count} professors")
    
    conn.close()
    return True

def main():
    """Main function to fix data migration issues"""
    logger.info("🔧 Starting data migration fix...")
    
    try:
        # Step 1: Diagnose current state
        diagnose_database()
        
        # Step 2: Fix universities
        if clear_and_reimport_universities():
            logger.info("✅ Universities fixed")
        else:
            logger.error("❌ Failed to fix universities")
            return
        
        # Step 3: Verify CA-ON-002 exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM universities WHERE code = 'CA-ON-002'")
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Verified CA-ON-002 exists: {result[0]}")
        else:
            logger.error("❌ CA-ON-002 still missing after reimport!")
            conn.close()
            return
        conn.close()
        
        # Step 4: Re-import professors
        if reimport_professors():
            logger.info("✅ Professors imported successfully")
        else:
            logger.error("❌ Failed to import professors")
            return
        
        # Step 5: Final verification
        logger.info("📊 Final verification:")
        diagnose_database()
        
        logger.info("🎉 Data migration fix completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")

if __name__ == "__main__":
    main() 