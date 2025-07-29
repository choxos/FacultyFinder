#!/usr/bin/env python3
"""
Fix Data Migration Issues for FacultyFinder
Diagnoses and fixes university code mismatches and data import problems
"""

import os
import csv
import json
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/var/www/ff/.env')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'ff_user'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'ff_production'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def diagnose_university_issue(data_dir):
    """Diagnose university import and foreign key issues"""
    logger.info("🔍 Diagnosing university data issues...")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Check what's actually in the universities table
    logger.info("📋 Current universities in database:")
    cursor.execute("SELECT university_code, name, country FROM universities LIMIT 10;")
    universities_in_db = cursor.fetchall()
    
    for uni in universities_in_db:
        logger.info(f"   - {uni[0]}: {uni[1]} ({uni[2]})")
    
    cursor.execute("SELECT COUNT(*) FROM universities;")
    total_unis = cursor.fetchone()[0]
    logger.info(f"📊 Total universities in database: {total_unis}")
    
    # Check university_codes.csv
    uni_file = os.path.join(data_dir, 'university_codes.csv')
    if os.path.exists(uni_file):
        logger.info(f"📁 Checking {uni_file}...")
        
        with open(uni_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            uni_codes_from_file = []
            
            for i, row in enumerate(reader):
                if i < 5:  # Show first 5
                    logger.info(f"   - File row {i+1}: {row}")
                uni_codes_from_file.append(row.get('university_code', row.get('code', '')))
        
        logger.info(f"📊 Total university codes in file: {len(uni_codes_from_file)}")
        
        # Check if CA-ON-002 exists in file
        if 'CA-ON-002' in uni_codes_from_file:
            logger.info("✅ CA-ON-002 found in university_codes.csv")
        else:
            logger.error("❌ CA-ON-002 NOT found in university_codes.csv")
            logger.info("🔍 Looking for McMaster-related codes...")
            mcmaster_codes = [code for code in uni_codes_from_file if 'mcmaster' in str(code).lower() or 'CA-ON' in str(code)]
            for code in mcmaster_codes[:5]:
                logger.info(f"   - Possible McMaster code: {code}")
    
    # Check mcmaster_experts_summary.csv
    experts_file = os.path.join(data_dir, 'mcmaster_experts_summary.csv')
    if os.path.exists(experts_file):
        logger.info(f"📁 Checking {experts_file}...")
        
        with open(experts_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            university_codes_in_experts = set()
            
            for i, row in enumerate(reader):
                if i < 3:  # Show first 3
                    logger.info(f"   - Experts row {i+1}: {row}")
                
                # Check different possible column names
                uni_code = row.get('university_code') or row.get('University_Code') or row.get('university') or row.get('University')
                if uni_code:
                    university_codes_in_experts.add(uni_code)
                
                if i >= 100:  # Don't process too many
                    break
        
        logger.info(f"📊 Unique university codes in experts file: {list(university_codes_in_experts)}")
    
    conn.close()

def fix_university_import(data_dir):
    """Fix university import issues"""
    logger.info("🔧 Fixing university import...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Clear existing data
    logger.info("🗑️  Clearing existing data...")
    cursor.execute("TRUNCATE TABLE professors, universities CASCADE;")
    
    # Import universities with proper error handling
    uni_file = os.path.join(data_dir, 'university_codes.csv')
    if not os.path.exists(uni_file):
        logger.error(f"❌ University file not found: {uni_file}")
        conn.close()
        return False
    
    logger.info(f"📚 Re-importing universities from {uni_file}...")
    imported_count = 0
    
    with open(uni_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Handle different possible column names
                university_code = row.get('university_code') or row.get('code') or row.get('Code')
                name = row.get('name') or row.get('Name') or row.get('university_name')
                city = row.get('city') or row.get('City') or ''
                country = row.get('country') or row.get('Country') or ''
                website = row.get('website') or row.get('Website') or ''
                
                if not university_code or not name:
                    logger.warning(f"⚠️  Skipping row with missing data: {row}")
                    continue
                
                cursor.execute("""
                    INSERT INTO universities (university_code, name, city, country, website)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (university_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        city = EXCLUDED.city,
                        country = EXCLUDED.country,
                        website = EXCLUDED.website
                """, (university_code, name, city, country, website))
                
                imported_count += 1
                
                if imported_count <= 5:
                    logger.info(f"   ✅ Imported: {university_code} - {name}")
                
            except Exception as e:
                logger.error(f"❌ Error importing university {row}: {e}")
    
    conn.commit()
    logger.info(f"✅ Imported {imported_count} universities")
    
    # Verify CA-ON-002 exists
    cursor.execute("SELECT name FROM universities WHERE university_code = 'CA-ON-002';")
    mcmaster = cursor.fetchone()
    
    if mcmaster:
        logger.info(f"✅ CA-ON-002 verified: {mcmaster[0]}")
    else:
        logger.warning("⚠️  CA-ON-002 still not found. Creating McMaster entry...")
        cursor.execute("""
            INSERT INTO universities (university_code, name, city, country, website)
            VALUES ('CA-ON-002', 'McMaster University', 'Hamilton', 'Canada', 'https://www.mcmaster.ca')
            ON CONFLICT (university_code) DO NOTHING
        """)
        conn.commit()
        logger.info("✅ Created CA-ON-002 (McMaster University)")
    
    conn.close()
    return True

def fix_professor_import(data_dir):
    """Fix professor import after university fix"""
    logger.info("👥 Re-importing professors...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    experts_file = os.path.join(data_dir, 'mcmaster_experts_summary.csv')
    if not os.path.exists(experts_file):
        logger.error(f"❌ Experts file not found: {experts_file}")
        conn.close()
        return False
    
    imported_count = 0
    
    with open(experts_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Handle different possible column names
                name = row.get('name') or row.get('Name') or row.get('professor_name') or ''
                university_code = row.get('university_code') or row.get('University_Code') or 'CA-ON-002'  # Default to McMaster
                department = row.get('department') or row.get('Department') or ''
                position = row.get('position') or row.get('Position') or row.get('rank') or ''
                email = row.get('email') or row.get('Email') or ''
                
                if not name:
                    continue
                
                # Create professor_code from name
                professor_code = name.lower().replace(' ', '_').replace('.', '').replace(',', '')
                
                cursor.execute("""
                    INSERT INTO professors (professor_code, name, university_code, department, position, email)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (professor_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        university_code = EXCLUDED.university_code,
                        department = EXCLUDED.department,
                        position = EXCLUDED.position,
                        email = EXCLUDED.email
                """, (professor_code, name, university_code, department, position, email))
                
                imported_count += 1
                
                if imported_count <= 5:
                    logger.info(f"   ✅ Imported: {name} ({university_code})")
                
            except Exception as e:
                logger.error(f"❌ Error importing professor {row}: {e}")
    
    conn.commit()
    logger.info(f"✅ Imported {imported_count} professors")
    
    conn.close()
    return True

def main():
    """Main function to diagnose and fix data migration issues"""
    logger.info("🚀 Starting Data Migration Issue Diagnosis and Fix")
    logger.info("=" * 60)
    
    data_dir = '/var/www/ff/data_import'
    
    # Step 1: Diagnose issues
    diagnose_university_issue(data_dir)
    
    print("\n" + "=" * 60)
    response = input("🔧 Do you want to proceed with fixing the issues? (y/n): ")
    
    if response.lower() == 'y':
        # Step 2: Fix university import
        if fix_university_import(data_dir):
            logger.info("✅ University import fixed")
            
            # Step 3: Fix professor import
            if fix_professor_import(data_dir):
                logger.info("✅ Professor import fixed")
                
                # Step 4: Verify final state
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM universities;")
                    uni_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM professors;")
                    prof_count = cursor.fetchone()[0]
                    
                    logger.info("📊 Final Migration Statistics:")
                    logger.info(f"   Universities: {uni_count}")
                    logger.info(f"   Professors: {prof_count}")
                    
                    conn.close()
                    
                    logger.info("🎉 Data migration issues fixed!")
                    logger.info("💡 You can now run the full migration again or test the website")
            else:
                logger.error("❌ Professor import fix failed")
        else:
            logger.error("❌ University import fix failed")
    else:
        logger.info("🚫 Fix cancelled by user")

if __name__ == "__main__":
    main() 