#!/usr/bin/env python3
"""
Add Faculty ID System to FacultyFinder
- Adds faculty_id column to CSV file
- Updates PostgreSQL schema 
- Generates unique faculty IDs based on university code
"""

import os
import sys
import csv
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_db_config():
    """Load database configuration"""
    load_dotenv('.env')
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

def generate_faculty_id(university_code, index):
    """Generate unique faculty ID: university_code-F-XXXX"""
    return f"{university_code}-F-{index:04d}"

def add_faculty_id_to_csv():
    """Add faculty_id column to the CSV file"""
    logger.info("📝 Adding faculty_id column to CSV file...")
    
    csv_file = 'data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv'
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Read the CSV
    df = pd.read_csv(csv_file)
    
    # Check if faculty_id already exists
    if 'faculty_id' in df.columns:
        logger.info("ℹ️ faculty_id column already exists")
        return True
    
    # Generate faculty IDs based on university_code
    faculty_ids = []
    university_counters = {}
    
    for _, row in df.iterrows():
        university_code = row.get('university_code', 'UNKNOWN')
        
        # Initialize counter for this university
        if university_code not in university_counters:
            university_counters[university_code] = 1
        
        # Generate faculty ID
        faculty_id = generate_faculty_id(university_code, university_counters[university_code])
        faculty_ids.append(faculty_id)
        
        # Increment counter
        university_counters[university_code] += 1
    
    # Add faculty_id as the second column (after name)
    df.insert(1, 'faculty_id', faculty_ids)
    
    # Save updated CSV
    df.to_csv(csv_file, index=False)
    
    logger.info(f"✅ Added faculty_id column with {len(faculty_ids)} unique IDs")
    logger.info(f"📊 Faculty IDs by university: {dict(university_counters)}")
    
    return True

def create_postgresql_schema_with_faculty_id(conn):
    """Create PostgreSQL schema with faculty_id support"""
    cursor = conn.cursor()
    
    logger.info("🗄️ Creating PostgreSQL schema with faculty_id...")
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS professors CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS universities CASCADE;")
    
    # Universities table (unchanged)
    cursor.execute("""
        CREATE TABLE universities (
            id SERIAL PRIMARY KEY,
            university_code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(500) NOT NULL,
            country VARCHAR(100) NOT NULL,
            province_state VARCHAR(100),
            city VARCHAR(200),
            address TEXT,
            website VARCHAR(500),
            university_type VARCHAR(50),
            languages VARCHAR(200),
            year_established INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Professors table with faculty_id as unique identifier
    cursor.execute("""
        CREATE TABLE professors (
            id SERIAL PRIMARY KEY,
            faculty_id VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(500) NOT NULL,
            first_name VARCHAR(200),
            last_name VARCHAR(200),
            middle_names VARCHAR(300),
            other_name VARCHAR(300),
            degrees TEXT,
            all_degrees_and_inst TEXT,
            all_degrees_only TEXT,
            research_areas TEXT,
            university_code VARCHAR(20) REFERENCES universities(university_code),
            university VARCHAR(500),
            faculty VARCHAR(300),
            department VARCHAR(500),
            other_departments TEXT,
            primary_affiliation VARCHAR(500),
            memberships TEXT,
            canada_research_chair VARCHAR(500),
            director TEXT,
            position VARCHAR(200),
            full_time BOOLEAN DEFAULT FALSE,
            adjunct BOOLEAN DEFAULT FALSE,
            uni_email VARCHAR(200),
            other_email TEXT,
            uni_page TEXT,
            website TEXT,
            misc TEXT,
            twitter VARCHAR(100),
            linkedin VARCHAR(100),
            phone VARCHAR(50),
            fax VARCHAR(50),
            google_scholar VARCHAR(100),
            scopus VARCHAR(100),
            web_of_science VARCHAR(100),
            orcid VARCHAR(50),
            researchgate VARCHAR(100),
            academicedu VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX idx_professors_faculty_id ON professors(faculty_id);
        CREATE INDEX idx_professors_university_code ON professors(university_code);
        CREATE INDEX idx_professors_name ON professors(name);
        CREATE INDEX idx_professors_department ON professors(department);
        CREATE INDEX idx_universities_code ON universities(university_code);
        CREATE INDEX idx_universities_country ON universities(country);
    """)
    
    conn.commit()
    logger.info("✅ PostgreSQL schema with faculty_id created successfully")
    return True

def import_data_with_faculty_id(conn):
    """Import data including faculty_id values"""
    cursor = conn.cursor()
    
    # Import universities first
    logger.info("📊 Importing universities...")
    universities_file = 'data/university_codes.csv'
    if os.path.exists(universities_file):
        df_uni = pd.read_csv(universities_file)
        for _, row in df_uni.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO universities (
                        university_code, name, country, province_state, city, 
                        address, website, university_type, languages, year_established
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (university_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        country = EXCLUDED.country,
                        province_state = EXCLUDED.province_state,
                        city = EXCLUDED.city,
                        address = EXCLUDED.address,
                        website = EXCLUDED.website,
                        university_type = EXCLUDED.university_type,
                        languages = EXCLUDED.languages,
                        year_established = EXCLUDED.year_established,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    row['university_code'], row['university_name'], row['country'],
                    row.get('province_state'), row.get('city'), row.get('address'),
                    row.get('website'), row.get('type'), row.get('language'),
                    row.get('established')
                ))
            except Exception as e:
                logger.error(f"❌ Error importing university {row.get('university_code')}: {e}")
        
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM universities")
        uni_count = cursor.fetchone()[0]
        logger.info(f"✅ Imported {uni_count} universities")
    
    # Import professors with faculty_id
    logger.info("👨‍🏫 Importing professors with faculty_id...")
    faculty_file = 'data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv'
    if os.path.exists(faculty_file):
        df_prof = pd.read_csv(faculty_file)
        
        if 'faculty_id' not in df_prof.columns:
            logger.error("❌ faculty_id column not found in CSV. Run add_faculty_id_to_csv() first.")
            return False
        
        for _, row in df_prof.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO professors (
                        faculty_id, name, first_name, last_name, middle_names, other_name,
                        degrees, all_degrees_and_inst, all_degrees_only, research_areas,
                        university_code, university, faculty, department, other_departments,
                        primary_affiliation, memberships, canada_research_chair, director,
                        position, full_time, adjunct, uni_email, other_email,
                        uni_page, website, misc, twitter, linkedin, phone, fax,
                        google_scholar, scopus, web_of_science, orcid, researchgate, academicedu
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (faculty_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        department = EXCLUDED.department,
                        position = EXCLUDED.position,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    row.get('faculty_id'), row.get('name'), row.get('first_name'), row.get('last_name'),
                    row.get('middle_names'), row.get('other_name'), row.get('degree'),
                    row.get('all_degrees_and_inst'), row.get('all_degrees_only'),
                    row.get('research_areas'), row.get('university_code'), row.get('university'),
                    row.get('faculty'), row.get('department'), row.get('other_depts'),
                    row.get('primary_aff'), row.get('membership'), row.get('canada_research_chair'),
                    row.get('director'), row.get('position'), 
                    row.get('full_time') == 'TRUE', row.get('adjunct') == 'TRUE',
                    row.get('uni_email'), row.get('other_email'), row.get('uni_page'),
                    row.get('website'), row.get('misc'), row.get('twitter'), row.get('linkedin'),
                    row.get('phone'), row.get('fax'), row.get('gscholar'), row.get('scopus'),
                    row.get('wos'), row.get('orcid'), row.get('researchgate'), row.get('academicedu')
                ))
            except Exception as e:
                logger.error(f"❌ Error importing professor {row.get('name')} ({row.get('faculty_id')}): {e}")
        
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM professors")
        prof_count = cursor.fetchone()[0]
        logger.info(f"✅ Imported {prof_count} professors with faculty_id")
    
    return True

def verify_faculty_id_system(conn):
    """Verify the faculty_id system is working"""
    cursor = conn.cursor()
    
    logger.info("🔍 Verifying faculty_id system...")
    
    # Check basic counts
    cursor.execute("SELECT COUNT(*) FROM universities")
    uni_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM professors")
    prof_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT faculty_id) FROM professors")
    unique_faculty_ids = cursor.fetchone()[0]
    
    # Check faculty_id pattern distribution
    cursor.execute("""
        SELECT 
            LEFT(faculty_id, POSITION('-F-' IN faculty_id) - 1) as university_prefix,
            COUNT(*) as count
        FROM professors 
        WHERE faculty_id IS NOT NULL
        GROUP BY LEFT(faculty_id, POSITION('-F-' IN faculty_id) - 1)
        ORDER BY count DESC
    """)
    
    faculty_distribution = cursor.fetchall()
    
    logger.info(f"📊 Verification Results:")
    logger.info(f"   Universities: {uni_count}")
    logger.info(f"   Professors: {prof_count}")
    logger.info(f"   Unique Faculty IDs: {unique_faculty_ids}")
    logger.info(f"   Faculty ID Distribution:")
    
    for prefix, count in faculty_distribution:
        logger.info(f"     {prefix}: {count} faculty")
    
    if unique_faculty_ids == prof_count:
        logger.info("✅ All faculty have unique faculty_id values")
    else:
        logger.warning(f"⚠️ {prof_count - unique_faculty_ids} professors without unique faculty_id")
    
    # Test faculty_id lookup
    cursor.execute("SELECT faculty_id, name FROM professors LIMIT 3")
    sample_faculty = cursor.fetchall()
    logger.info("🎯 Sample faculty for testing:")
    for faculty_id, name in sample_faculty:
        logger.info(f"   {faculty_id} → {name}")
    
    return True

def main():
    """Main function"""
    logger.info("🚀 Adding Faculty ID System to FacultyFinder")
    logger.info("=" * 50)
    
    # Step 1: Add faculty_id to CSV
    if not add_faculty_id_to_csv():
        logger.error("❌ Failed to add faculty_id to CSV")
        return False
    
    # Step 2: Connect to database
    config = load_db_config()
    if not all(config.values()):
        logger.error("❌ Missing database configuration in .env file")
        return False
    
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        logger.info("✅ Connected to PostgreSQL database")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    try:
        # Step 3: Create schema with faculty_id
        if not create_postgresql_schema_with_faculty_id(conn):
            return False
        
        # Step 4: Import data with faculty_id
        if not import_data_with_faculty_id(conn):
            return False
        
        # Step 5: Verify system
        verify_faculty_id_system(conn)
        
        logger.info("🎉 Faculty ID system successfully implemented!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Faculty ID system setup failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 