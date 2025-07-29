#!/usr/bin/env python3
"""
Clean Database Rebuild for FacultyFinder
Completely removes all data and recreates database from CSV files
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
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

def generate_faculty_id(university_code, index):
    """Generate unique faculty ID: university_code-F-XXXX"""
    return f"{university_code}-F-{index:04d}"

def add_faculty_id_to_csv():
    """Add faculty_id column to CSV if it doesn't exist"""
    logger.info("📝 Checking/adding faculty_id column to CSV...")
    
    csv_file = 'data/mcmaster_hei_faculty.csv'
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Read the CSV
    df = pd.read_csv(csv_file)
    
    # Check if faculty_id already exists
    if 'faculty_id' in df.columns:
        logger.info("ℹ️ faculty_id column already exists")
        return True
    
    # Generate faculty IDs
    faculty_ids = []
    university_counters = {}
    
    for _, row in df.iterrows():
        university_code = row.get('university_code', 'UNKNOWN')
        
        if university_code not in university_counters:
            university_counters[university_code] = 1
        
        faculty_id = generate_faculty_id(university_code, university_counters[university_code])
        faculty_ids.append(faculty_id)
        university_counters[university_code] += 1
    
    # Add faculty_id as the second column
    df.insert(1, 'faculty_id', faculty_ids)
    
    # Save updated CSV
    df.to_csv(csv_file, index=False)
    
    logger.info(f"✅ Added {len(faculty_ids)} faculty IDs")
    logger.info(f"📊 Faculty distribution: {dict(university_counters)}")
    return True

def wipe_database(conn):
    """Completely wipe all tables and data"""
    cursor = conn.cursor()
    
    logger.info("🗑️ Wiping database - removing all tables...")
    
    try:
        # Drop all tables in the correct order (handle foreign keys)
        tables_to_drop = [
            'professors',
            'universities',
            'publications',
            'author_publications', 
            'journals',
            'journal_rankings',
            'professor_degrees',
            'degrees'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            logger.info(f"   Dropped table: {table}")
        
        # Drop any views that might exist
        views_to_drop = [
            'professor_summary',
            'university_summary'
        ]
        
        for view in views_to_drop:
            cursor.execute(f"DROP VIEW IF EXISTS {view} CASCADE;")
        
        conn.commit()
        logger.info("✅ Database completely wiped")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to wipe database: {e}")
        conn.rollback()
        return False

def create_fresh_schema(conn):
    """Create fresh PostgreSQL schema optimized for faculty_id"""
    cursor = conn.cursor()
    
    logger.info("🏗️ Creating fresh database schema...")
    
    try:
        # Universities table
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
                university_type VARCHAR(50) DEFAULT 'Public',
                languages VARCHAR(200),
                year_established INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Professors table with faculty_id as primary identifier
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
                university_code VARCHAR(20) NOT NULL REFERENCES universities(university_code),
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
        
        # Create performance indexes
        cursor.execute("""
            -- University indexes
            CREATE INDEX idx_universities_code ON universities(university_code);
            CREATE INDEX idx_universities_country ON universities(country);
            CREATE INDEX idx_universities_name ON universities(name);
            
            -- Professor indexes  
            CREATE INDEX idx_professors_faculty_id ON professors(faculty_id);
            CREATE INDEX idx_professors_university_code ON professors(university_code);
            CREATE INDEX idx_professors_name ON professors(name);
            CREATE INDEX idx_professors_department ON professors(department);
            CREATE INDEX idx_professors_research_areas ON professors(research_areas);
            CREATE INDEX idx_professors_position ON professors(position);
            
            -- Composite indexes for common queries
            CREATE INDEX idx_professors_uni_dept ON professors(university_code, department);
            CREATE INDEX idx_professors_name_uni ON professors(name, university_code);
        """)
        
        conn.commit()
        logger.info("✅ Fresh schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create schema: {e}")
        conn.rollback()
        return False

def import_universities(conn):
    """Import universities from CSV"""
    cursor = conn.cursor()
    
    logger.info("🏫 Importing universities...")
    
    universities_file = 'data/university_codes.csv'
    if not os.path.exists(universities_file):
        logger.error(f"❌ Universities file not found: {universities_file}")
        return False
    
    try:
        df = pd.read_csv(universities_file)
        imported_count = 0
        
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO universities (
                    university_code, name, country, province_state, city, 
                    address, website, university_type, languages, year_established
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['university_code'],
                row['university_name'], 
                row['country'],
                row.get('province_state'),
                row.get('city'),
                row.get('address'),
                row.get('website'),
                row.get('type', 'Public'),
                row.get('language'),
                row.get('established')
            ))
            imported_count += 1
        
        conn.commit()
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM universities")
        count = cursor.fetchone()[0]
        
        logger.info(f"✅ Imported {imported_count} universities (verified: {count})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to import universities: {e}")
        conn.rollback()
        return False

def import_faculty_with_ids(conn):
    """Import faculty with faculty_id from CSV"""
    cursor = conn.cursor()
    
    logger.info("👨‍🏫 Importing faculty with faculty_id...")
    
    faculty_file = 'data/mcmaster_hei_faculty.csv'
    if not os.path.exists(faculty_file):
        logger.error(f"❌ Faculty file not found: {faculty_file}")
        return False
    
    try:
        df = pd.read_csv(faculty_file)
        
        if 'faculty_id' not in df.columns:
            logger.error("❌ faculty_id column not found in CSV")
            return False
        
        imported_count = 0
        
        for _, row in df.iterrows():
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
            """, (
                row.get('faculty_id'),
                row.get('name'),
                row.get('first_name'),
                row.get('last_name'),
                row.get('middle_names'),
                row.get('other_name'),
                row.get('degree'),
                row.get('all_degrees_and_inst'),
                row.get('all_degrees_only'),
                row.get('research_areas'),
                row.get('university_code'),
                row.get('university'),
                row.get('faculty'),
                row.get('department'),
                row.get('other_depts'),
                row.get('primary_aff'),
                row.get('membership'),
                row.get('canada_research_chair'),
                row.get('director'),
                row.get('position'),
                row.get('full_time') == 'TRUE',
                row.get('adjunct') == 'TRUE',
                row.get('uni_email'),
                row.get('other_email'),
                row.get('uni_page'),
                row.get('website'),
                row.get('misc'),
                row.get('twitter'),
                row.get('linkedin'),
                row.get('phone'),
                row.get('fax'),
                row.get('gscholar'),
                row.get('scopus'),
                row.get('wos'),
                row.get('orcid'),
                row.get('researchgate'),
                row.get('academicedu')
            ))
            imported_count += 1
        
        conn.commit()
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM professors")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT faculty_id) FROM professors")
        unique_ids = cursor.fetchone()[0]
        
        logger.info(f"✅ Imported {imported_count} faculty members (verified: {count}, unique IDs: {unique_ids})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to import faculty: {e}")
        conn.rollback()
        return False

def verify_rebuild(conn):
    """Verify the database rebuild was successful"""
    cursor = conn.cursor()
    
    logger.info("🔍 Verifying database rebuild...")
    
    try:
        # Check basic counts
        cursor.execute("SELECT COUNT(*) FROM universities")
        uni_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM professors")
        prof_count = cursor.fetchone()[0]
        
        # Check data integrity
        cursor.execute("""
            SELECT COUNT(*) FROM professors p 
            INNER JOIN universities u ON p.university_code = u.university_code
        """)
        linked_count = cursor.fetchone()[0]
        
        # Check faculty_id patterns
        cursor.execute("""
            SELECT 
                LEFT(faculty_id, POSITION('-F-' IN faculty_id) - 1) as university_prefix,
                COUNT(*) as faculty_count
            FROM professors 
            WHERE faculty_id IS NOT NULL
            GROUP BY LEFT(faculty_id, POSITION('-F-' IN faculty_id) - 1)
            ORDER BY faculty_count DESC
        """)
        faculty_distribution = cursor.fetchall()
        
        # Sample data
        cursor.execute("SELECT faculty_id, name FROM professors LIMIT 5")
        sample_faculty = cursor.fetchall()
        
        logger.info("📊 Verification Results:")
        logger.info(f"   Universities: {uni_count}")
        logger.info(f"   Faculty: {prof_count}")
        logger.info(f"   Properly linked: {linked_count}")
        
        if linked_count == prof_count:
            logger.info("✅ All faculty properly linked to universities")
        else:
            logger.warning(f"⚠️ {prof_count - linked_count} faculty not properly linked")
        
        logger.info("📊 Faculty ID Distribution:")
        for prefix, count in faculty_distribution:
            logger.info(f"   {prefix}: {count} faculty")
        
        logger.info("🎯 Sample Faculty:")
        for faculty_id, name in sample_faculty:
            logger.info(f"   {faculty_id} → {name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Clean Database Rebuild for FacultyFinder")
    logger.info("=" * 50)
    
    # Step 1: Ensure faculty_id exists in CSV
    if not add_faculty_id_to_csv():
        logger.error("❌ Failed to prepare CSV file")
        return False
    
    # Step 2: Connect to database
    config = load_db_config()
    if not all(config.values()):
        logger.error("❌ Missing database configuration in .env file")
        return False
    
    conn = connect_database(config)
    if not conn:
        return False
    
    try:
        # Step 3: Wipe existing database
        if not wipe_database(conn):
            return False
        
        # Step 4: Create fresh schema
        if not create_fresh_schema(conn):
            return False
        
        # Step 5: Import universities
        if not import_universities(conn):
            return False
        
        # Step 6: Import faculty
        if not import_faculty_with_ids(conn):
            return False
        
        # Step 7: Verify everything
        if not verify_rebuild(conn):
            return False
        
        logger.info("🎉 Database rebuild completed successfully!")
        logger.info("🌐 Ready to restart FastAPI service")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database rebuild failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 