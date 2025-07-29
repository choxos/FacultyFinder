#!/usr/bin/env python3
"""
Fix FacultyFinder PostgreSQL Database Schema and Data Import
Resolves schema inconsistencies and imports data from CSV files
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from dotenv import load_dotenv
import logging

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

def connect_database(config):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        logger.info("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def create_postgresql_schema(conn):
    """Create PostgreSQL-compatible schema"""
    cursor = conn.cursor()
    
    logger.info("🗄️ Creating PostgreSQL schema...")
    
    # Drop existing tables if they exist (to fix schema issues)
    cursor.execute("DROP TABLE IF EXISTS professors CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS universities CASCADE;")
    
    # Universities table (PostgreSQL compatible)
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
    
    # Professors table (PostgreSQL compatible with university_code reference)
    cursor.execute("""
        CREATE TABLE professors (
            id SERIAL PRIMARY KEY,
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
        CREATE INDEX idx_professors_university_code ON professors(university_code);
        CREATE INDEX idx_professors_name ON professors(name);
        CREATE INDEX idx_professors_department ON professors(department);
        CREATE INDEX idx_universities_code ON universities(university_code);
        CREATE INDEX idx_universities_country ON universities(country);
    """)
    
    conn.commit()
    logger.info("✅ PostgreSQL schema created successfully")

def import_universities(conn):
    """Import universities from CSV"""
    cursor = conn.cursor()
    
    logger.info("📊 Importing universities...")
    
    universities_file = 'data/university_codes.csv'
    if not os.path.exists(universities_file):
        logger.error(f"❌ Universities file not found: {universities_file}")
        return False
    
    df = pd.read_csv(universities_file)
    
    for _, row in df.iterrows():
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
    
    # Get count
    cursor.execute("SELECT COUNT(*) FROM universities")
    count = cursor.fetchone()[0]
    logger.info(f"✅ Imported {count} universities")
    return True

def import_professors(conn):
    """Import professors from CSV"""
    cursor = conn.cursor()
    
    logger.info("👨‍🏫 Importing professors...")
    
    faculty_file = 'data/mcmaster_hei_faculty.csv'
    if not os.path.exists(faculty_file):
        logger.error(f"❌ Faculty file not found: {faculty_file}")
        return False
    
    df = pd.read_csv(faculty_file)
    
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO professors (
                    name, first_name, last_name, middle_names, other_name,
                    degrees, all_degrees_and_inst, all_degrees_only, research_areas,
                    university_code, university, faculty, department, other_departments,
                    primary_affiliation, memberships, canada_research_chair, director,
                    position, full_time, adjunct, uni_email, other_email,
                    uni_page, website, misc, twitter, linkedin, phone, fax,
                    google_scholar, scopus, web_of_science, orcid, researchgate, academicedu
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                row.get('name'), row.get('first_name'), row.get('last_name'),
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
            logger.error(f"❌ Error importing professor {row.get('name')}: {e}")
    
    conn.commit()
    
    # Get count
    cursor.execute("SELECT COUNT(*) FROM professors")
    count = cursor.fetchone()[0]
    logger.info(f"✅ Imported {count} professors")
    return True

def verify_data(conn):
    """Verify imported data"""
    cursor = conn.cursor()
    
    logger.info("🔍 Verifying imported data...")
    
    # Check universities
    cursor.execute("SELECT COUNT(*) FROM universities")
    uni_count = cursor.fetchone()[0]
    
    # Check professors
    cursor.execute("SELECT COUNT(*) FROM professors")
    prof_count = cursor.fetchone()[0]
    
    # Check relationship
    cursor.execute("""
        SELECT COUNT(*) FROM professors p 
        INNER JOIN universities u ON p.university_code = u.university_code
    """)
    matched_count = cursor.fetchone()[0]
    
    logger.info(f"📊 Database Summary:")
    logger.info(f"   Universities: {uni_count}")
    logger.info(f"   Professors: {prof_count}")
    logger.info(f"   Matched Relations: {matched_count}")
    
    if matched_count == prof_count:
        logger.info("✅ All professors properly linked to universities")
    else:
        logger.warning(f"⚠️ {prof_count - matched_count} professors not linked to universities")
    
    return True

def main():
    """Main function"""
    logger.info("🚀 Starting FacultyFinder Database Fix")
    
    # Load configuration
    config = load_db_config()
    if not all(config.values()):
        logger.error("❌ Missing database configuration in .env file")
        return False
    
    # Connect to database
    conn = connect_database(config)
    if not conn:
        return False
    
    try:
        # Create schema
        create_postgresql_schema(conn)
        
        # Import data
        if not import_universities(conn):
            return False
        
        if not import_professors(conn):
            return False
        
        # Verify data
        verify_data(conn)
        
        logger.info("🎉 Database fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 