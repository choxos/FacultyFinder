#!/usr/bin/env python3
"""
Simple FacultyFinder Data Import
Simplified version for quick data import to production database
"""

import os
import csv
import json
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/var/www/ff/.env')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'ff_user'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'ff_production')
}

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_tables(conn):
    """Create basic tables"""
    cursor = conn.cursor()
    
    print("🗄️  Creating database tables...")
    
    # Universities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS universities (
            id SERIAL PRIMARY KEY,
            university_code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(500) NOT NULL,
            city VARCHAR(200),
            province_state VARCHAR(200),
            country VARCHAR(100),
            website VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Professors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professors (
            id SERIAL PRIMARY KEY,
            professor_code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(300) NOT NULL,
            university_code VARCHAR(20) REFERENCES universities(university_code),
            department VARCHAR(300),
            position VARCHAR(200),
            email VARCHAR(200),
            research_interests TEXT,
            profile_url VARCHAR(500),
            google_scholar_url VARCHAR(500),
            orcid VARCHAR(100),
            publication_count INTEGER DEFAULT 0,
            citation_count INTEGER DEFAULT 0,
            h_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Publications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publications (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            journal VARCHAR(500),
            year INTEGER,
            doi VARCHAR(200),
            pmid VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Professor-Publications relationship
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_publications (
            id SERIAL PRIMARY KEY,
            professor_code VARCHAR(50) REFERENCES professors(professor_code),
            publication_id INTEGER REFERENCES publications(id),
            UNIQUE(professor_code, publication_id)
        );
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_universities_code ON universities(university_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_professors_code ON professors(professor_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_professors_university ON professors(university_code);")
    
    conn.commit()
    print("✅ Tables created")

def import_universities(conn, csv_file):
    """Import universities from CSV"""
    if not os.path.exists(csv_file):
        print(f"⚠️  University file not found: {csv_file}")
        return
    
    print(f"📚 Importing universities from {csv_file}...")
    
    cursor = conn.cursor()
    df = pd.read_csv(csv_file)
    
    universities_data = []
    for _, row in df.iterrows():
        universities_data.append((
            row.get('Code', ''),
            row.get('University', ''),
            row.get('City', ''),
            row.get('State/Province', ''),
            row.get('Country', ''),
            row.get('Website', '')
        ))
    
    insert_query = """
        INSERT INTO universities (university_code, name, city, province_state, country, website)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (university_code) DO NOTHING;
    """
    
    execute_batch(cursor, insert_query, universities_data)
    conn.commit()
    
    print(f"✅ Imported {len(universities_data)} universities")

def import_professors(conn, csv_file):
    """Import professors from CSV"""
    if not os.path.exists(csv_file):
        print(f"⚠️  Professors file not found: {csv_file}")
        return
    
    print(f"👥 Importing professors from {csv_file}...")
    
    cursor = conn.cursor()
    df = pd.read_csv(csv_file)
    
    professors_data = []
    for idx, row in df.iterrows():
        professor_code = f"CA-ON-002-{str(idx+1).zfill(4)}"
        
        professors_data.append((
            professor_code,
            row.get('Name', ''),
            'CA-ON-002',  # McMaster University code
            row.get('Department', ''),
            row.get('Position', 'Faculty Member'),
            row.get('Email', ''),
            row.get('Research Interests', ''),
            row.get('Profile URL', ''),
            row.get('Google Scholar', ''),
            row.get('ORCID', ''),
            row.get('Publication Count', 0) if pd.notna(row.get('Publication Count')) else 0,
            row.get('Citation Count', 0) if pd.notna(row.get('Citation Count')) else 0,
            row.get('H-Index', 0) if pd.notna(row.get('H-Index')) else 0
        ))
    
    insert_query = """
        INSERT INTO professors (professor_code, name, university_code, department, position, 
                              email, research_interests, profile_url, google_scholar_url, orcid,
                              publication_count, citation_count, h_index)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (professor_code) DO NOTHING;
    """
    
    execute_batch(cursor, insert_query, professors_data)
    conn.commit()
    
    print(f"✅ Imported {len(professors_data)} professors")

def import_publications(conn, json_file):
    """Import publications from detailed JSON"""
    if not os.path.exists(json_file):
        print(f"⚠️  Publications file not found: {json_file}")
        return
    
    print(f"📄 Importing publications from {json_file}...")
    
    cursor = conn.cursor()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)
    
    publication_count = 0
    
    for idx, faculty in enumerate(faculty_data):
        professor_code = f"CA-ON-002-{str(idx+1).zfill(4)}"
        publications = faculty.get('publications', [])
        
        for pub in publications[:10]:  # Limit to 10 publications per faculty for speed
            try:
                # Insert publication
                cursor.execute("""
                    INSERT INTO publications (title, authors, journal, year, doi, pmid)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id;
                """, (
                    pub.get('title', '')[:500],  # Limit title length
                    pub.get('authors', '')[:1000],  # Limit authors length
                    pub.get('journal', ''),
                    pub.get('year', None),
                    pub.get('doi', ''),
                    pub.get('pmid', '')
                ))
                
                result = cursor.fetchone()
                if result:
                    publication_id = result[0]
                    
                    # Link to professor
                    cursor.execute("""
                        INSERT INTO professor_publications (professor_code, publication_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (professor_code, publication_id))
                    
                    publication_count += 1
            
            except Exception as e:
                print(f"⚠️  Skipping publication: {e}")
                continue
    
    conn.commit()
    print(f"✅ Imported {publication_count} publications")

def verify_import(conn):
    """Verify the import was successful"""
    cursor = conn.cursor()
    
    print("📊 Verifying import...")
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM universities")
    uni_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM professors")
    prof_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM publications")
    pub_count = cursor.fetchone()[0]
    
    # Sample data
    cursor.execute("SELECT name FROM universities LIMIT 3")
    unis = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM professors LIMIT 3")
    profs = [row[0] for row in cursor.fetchall()]
    
    print(f"✅ Universities: {uni_count}")
    print(f"✅ Professors: {prof_count}")
    print(f"✅ Publications: {pub_count}")
    print(f"✅ Sample universities: {unis}")
    print(f"✅ Sample professors: {profs}")

def main():
    """Main import function"""
    print("🚀 FacultyFinder Simple Data Import")
    print("===================================")
    
    # Check if we're in the right directory
    data_dir = '/var/www/ff/data_import'
    if not os.path.exists(data_dir):
        data_dir = '.'
        print(f"Using current directory: {os.getcwd()}")
    else:
        print(f"Using data directory: {data_dir}")
    
    # Connect to database
    conn = connect_db()
    if not conn:
        return False
    
    try:
        # Create tables
        create_tables(conn)
        
        # Import data
        import_universities(conn, os.path.join(data_dir, 'university_codes.csv'))
        import_professors(conn, os.path.join(data_dir, 'mcmaster_experts_summary.csv'))
        import_publications(conn, os.path.join(data_dir, 'mcmaster_experts_detailed.json'))
        
        # Verify
        verify_import(conn)
        
        print("🎉 Data import completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 