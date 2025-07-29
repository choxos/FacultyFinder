#!/usr/bin/env python3
"""
FacultyFinder Data Migration System
Comprehensive system to transfer and import data from local computer to VPS PostgreSQL database
"""

import os
import sys
import json
import csv
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FacultyFinderDataMigrator:
    """Handles data migration for FacultyFinder"""
    
    def __init__(self, db_config: Dict[str, Any] = None):
        """Initialize the data migrator"""
        self.db_config = db_config or self._load_db_config()
        self.conn = None
        self.data_stats = {
            'universities': 0,
            'professors': 0,
            'publications': 0,
            'journals': 0,
            'errors': []
        }
    
    def _load_db_config(self) -> Dict[str, Any]:
        """Load database configuration from environment"""
        # Try to load from .env file
        env_path = '/var/www/ff/.env'
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'ff_user'),
            'password': os.getenv('DB_PASSWORD', 'Choxos10203040'),
            'database': os.getenv('DB_NAME', 'ff_production')
        }
    
    def connect_database(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def close_database(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def create_database_schema(self) -> bool:
        """Create or update database schema for FacultyFinder"""
        try:
            cursor = self.conn.cursor()
            
            logger.info("🗄️  Creating database schema...")
            
            # Universities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS universities (
                    id SERIAL PRIMARY KEY,
                    university_code VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(500) NOT NULL,
                    city VARCHAR(200),
                    province_state VARCHAR(200),
                    country VARCHAR(100),
                    address TEXT,
                    website VARCHAR(500),
                    university_type VARCHAR(100),
                    languages VARCHAR(200),
                    year_established INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Professors table (updated schema)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS professors (
                    id SERIAL PRIMARY KEY,
                    professor_code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(300) NOT NULL,
                    university_code VARCHAR(20) REFERENCES universities(university_code),
                    department VARCHAR(300),
                    position VARCHAR(200),
                    rank VARCHAR(100),
                    email VARCHAR(200),
                    phone VARCHAR(50),
                    office VARCHAR(200),
                    biography TEXT,
                    research_interests TEXT,
                    research_areas JSONB,
                    education JSONB,
                    experience JSONB,
                    awards_honors JSONB,
                    memberships JSONB,
                    profile_url VARCHAR(500),
                    photo_url VARCHAR(500),
                    google_scholar_url VARCHAR(500),
                    orcid VARCHAR(100),
                    linkedin_url VARCHAR(500),
                    full_time BOOLEAN DEFAULT TRUE,
                    adjunct BOOLEAN DEFAULT FALSE,
                    publication_count INTEGER DEFAULT 0,
                    citation_count INTEGER DEFAULT 0,
                    h_index INTEGER DEFAULT 0,
                    i10_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    volume VARCHAR(50),
                    issue VARCHAR(50),
                    pages VARCHAR(100),
                    doi VARCHAR(200),
                    pmid VARCHAR(50),
                    abstract TEXT,
                    keywords TEXT,
                    publication_type VARCHAR(100),
                    citation_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Professor-Publications relationship table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS professor_publications (
                    id SERIAL PRIMARY KEY,
                    professor_code VARCHAR(50) REFERENCES professors(professor_code),
                    publication_id INTEGER REFERENCES publications(id),
                    author_position INTEGER,
                    is_corresponding_author BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(professor_code, publication_id)
                );
            """)
            
            # Journals table (for Scimago data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journals (
                    id SERIAL PRIMARY KEY,
                    source_id INTEGER UNIQUE,
                    title VARCHAR(500) NOT NULL,
                    issn VARCHAR(100),
                    e_issn VARCHAR(100),
                    publisher VARCHAR(300),
                    categories TEXT,
                    areas TEXT,
                    type VARCHAR(100),
                    country VARCHAR(100),
                    region VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Journal metrics table (yearly data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_metrics (
                    id SERIAL PRIMARY KEY,
                    journal_id INTEGER REFERENCES journals(id),
                    year INTEGER,
                    sjr DECIMAL(10,6),
                    rank INTEGER,
                    rank_percentile DECIMAL(5,2),
                    h_index INTEGER,
                    total_docs INTEGER,
                    total_cites INTEGER,
                    cites_per_doc DECIMAL(10,6),
                    ref_per_doc DECIMAL(10,6),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(journal_id, year)
                );
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_universities_code ON universities(university_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_professors_code ON professors(professor_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_professors_university ON professors(university_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_publications_doi ON publications(doi);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_publications_pmid ON publications(pmid);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(year);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_issn ON journals(issn);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_metrics_year ON journal_metrics(year);")
            
            self.conn.commit()
            logger.info("✅ Database schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            self.conn.rollback()
            return False
    
    def import_universities(self, csv_file: str) -> bool:
        """Import universities from university_codes.csv"""
        try:
            logger.info(f"📚 Importing universities from {csv_file}...")
            
            df = pd.read_csv(csv_file)
            cursor = self.conn.cursor()
            
            # Prepare data for batch insert
            universities_data = []
            for _, row in df.iterrows():
                universities_data.append((
                    row.get('Code', ''),
                    row.get('University', ''),
                    row.get('City', ''),
                    row.get('State/Province', ''),
                    row.get('Country', ''),
                    row.get('Address', ''),
                    row.get('Website', ''),
                    row.get('Type', ''),
                    row.get('Languages', ''),
                    row.get('Year Established', None) if pd.notna(row.get('Year Established')) else None
                ))
            
            # Batch insert universities
            insert_query = """
                INSERT INTO universities (university_code, name, city, province_state, country, 
                                        address, website, university_type, languages, year_established)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (university_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    city = EXCLUDED.city,
                    province_state = EXCLUDED.province_state,
                    country = EXCLUDED.country,
                    address = EXCLUDED.address,
                    website = EXCLUDED.website,
                    university_type = EXCLUDED.university_type,
                    languages = EXCLUDED.languages,
                    year_established = EXCLUDED.year_established,
                    updated_at = CURRENT_TIMESTAMP;
            """
            
            execute_batch(cursor, insert_query, universities_data, page_size=100)
            self.conn.commit()
            
            self.data_stats['universities'] = len(universities_data)
            logger.info(f"✅ Imported {len(universities_data)} universities")
            return True
            
        except Exception as e:
            logger.error(f"❌ University import failed: {e}")
            self.conn.rollback()
            self.data_stats['errors'].append(f"University import: {e}")
            return False
    
    def import_professors_summary(self, csv_file: str) -> bool:
        """Import professors from mcmaster_experts_summary.csv"""
        try:
            logger.info(f"👥 Importing professors from {csv_file}...")
            
            df = pd.read_csv(csv_file)
            cursor = self.conn.cursor()
            
            professors_data = []
            for idx, row in df.iterrows():
                # Generate professor code (university code + sequential number)
                professor_code = f"CA-ON-002-{str(idx+1).zfill(4)}"
                
                professors_data.append((
                    professor_code,
                    row.get('Name', ''),
                    'CA-ON-002',  # McMaster University code
                    row.get('Department', ''),
                    row.get('Position', 'Faculty Member'),
                    row.get('Rank', ''),
                    row.get('Email', ''),
                    None,  # phone
                    None,  # office
                    None,  # biography
                    row.get('Research Interests', ''),
                    None,  # research_areas (JSON)
                    None,  # education (JSON)
                    None,  # experience (JSON)
                    None,  # awards_honors (JSON)
                    None,  # memberships (JSON)
                    row.get('Profile URL', ''),
                    row.get('Photo URL', ''),
                    row.get('Google Scholar', ''),
                    row.get('ORCID', ''),
                    row.get('LinkedIn', ''),
                    True,  # full_time
                    False,  # adjunct
                    row.get('Publication Count', 0) if pd.notna(row.get('Publication Count')) else 0,
                    row.get('Citation Count', 0) if pd.notna(row.get('Citation Count')) else 0,
                    row.get('H-Index', 0) if pd.notna(row.get('H-Index')) else 0,
                    row.get('i10-Index', 0) if pd.notna(row.get('i10-Index')) else 0
                ))
            
            insert_query = """
                INSERT INTO professors (professor_code, name, university_code, department, position, 
                                      rank, email, phone, office, biography, research_interests,
                                      research_areas, education, experience, awards_honors, memberships,
                                      profile_url, photo_url, google_scholar_url, orcid, linkedin_url,
                                      full_time, adjunct, publication_count, citation_count, h_index, i10_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (professor_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    department = EXCLUDED.department,
                    position = EXCLUDED.position,
                    rank = EXCLUDED.rank,
                    email = EXCLUDED.email,
                    research_interests = EXCLUDED.research_interests,
                    profile_url = EXCLUDED.profile_url,
                    photo_url = EXCLUDED.photo_url,
                    google_scholar_url = EXCLUDED.google_scholar_url,
                    orcid = EXCLUDED.orcid,
                    linkedin_url = EXCLUDED.linkedin_url,
                    publication_count = EXCLUDED.publication_count,
                    citation_count = EXCLUDED.citation_count,
                    h_index = EXCLUDED.h_index,
                    i10_index = EXCLUDED.i10_index,
                    updated_at = CURRENT_TIMESTAMP;
            """
            
            execute_batch(cursor, insert_query, professors_data, page_size=50)
            self.conn.commit()
            
            self.data_stats['professors'] = len(professors_data)
            logger.info(f"✅ Imported {len(professors_data)} professors")
            return True
            
        except Exception as e:
            logger.error(f"❌ Professor import failed: {e}")
            self.conn.rollback()
            self.data_stats['errors'].append(f"Professor import: {e}")
            return False
    
    def import_detailed_faculty_data(self, json_file: str) -> bool:
        """Import detailed faculty data from mcmaster_experts_detailed.json"""
        try:
            logger.info(f"📖 Importing detailed faculty data from {json_file}...")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                faculty_data = json.load(f)
            
            cursor = self.conn.cursor()
            publication_count = 0
            
            for idx, faculty in enumerate(faculty_data):
                professor_code = f"CA-ON-002-{str(idx+1).zfill(4)}"
                
                # Import publications for this faculty member
                publications = faculty.get('publications', [])
                
                for pub in publications:
                    try:
                        # Insert publication
                        pub_insert_query = """
                            INSERT INTO publications (title, authors, journal, year, volume, issue, pages, 
                                                    doi, pmid, abstract, keywords, publication_type, citation_count)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (doi) DO NOTHING
                            RETURNING id;
                        """
                        
                        cursor.execute(pub_insert_query, (
                            pub.get('title', ''),
                            pub.get('authors', ''),
                            pub.get('journal', ''),
                            pub.get('year', None),
                            pub.get('volume', ''),
                            pub.get('issue', ''),
                            pub.get('pages', ''),
                            pub.get('doi', ''),
                            pub.get('pmid', ''),
                            pub.get('abstract', ''),
                            pub.get('keywords', ''),
                            pub.get('type', 'Article'),
                            pub.get('citation_count', 0)
                        ))
                        
                        result = cursor.fetchone()
                        if result:
                            publication_id = result[0]
                            
                            # Link publication to professor
                            link_query = """
                                INSERT INTO professor_publications (professor_code, publication_id)
                                VALUES (%s, %s)
                                ON CONFLICT (professor_code, publication_id) DO NOTHING;
                            """
                            cursor.execute(link_query, (professor_code, publication_id))
                            publication_count += 1
                    
                    except Exception as e:
                        logger.warning(f"Failed to import publication: {e}")
                        continue
            
            self.conn.commit()
            self.data_stats['publications'] = publication_count
            logger.info(f"✅ Imported {publication_count} publications")
            return True
            
        except Exception as e:
            logger.error(f"❌ Detailed faculty data import failed: {e}")
            self.conn.rollback()
            self.data_stats['errors'].append(f"Detailed faculty import: {e}")
            return False
    
    def import_scimago_journals(self, csv_file: str) -> bool:
        """Import Scimago journal data"""
        try:
            logger.info(f"📊 Importing Scimago journal data from {csv_file}...")
            
            # Read in chunks due to large file size
            chunk_size = 1000
            journal_count = 0
            
            cursor = self.conn.cursor()
            
            for chunk in pd.read_csv(csv_file, chunksize=chunk_size):
                journals_data = []
                metrics_data = []
                
                for _, row in chunk.iterrows():
                    source_id = row.get('Source Id', None)
                    if pd.isna(source_id):
                        continue
                    
                    # Journal basic info
                    journals_data.append((
                        int(source_id),
                        row.get('Title', ''),
                        row.get('Issn', ''),
                        row.get('E-Issn', ''),
                        row.get('Publisher', ''),
                        row.get('Categories', ''),
                        row.get('Areas', ''),
                        row.get('Type', ''),
                        row.get('Country', ''),
                        row.get('Region', '')
                    ))
                    
                    # Extract metrics for different years
                    for year in range(1999, 2026):  # Adjust range as needed
                        sjr_col = f'SJR {year}'
                        rank_col = f'Rank {year}'
                        h_index_col = f'H index {year}'
                        
                        if sjr_col in row and pd.notna(row[sjr_col]):
                            metrics_data.append((
                                source_id,
                                year,
                                row.get(sjr_col, None),
                                row.get(rank_col, None),
                                None,  # rank_percentile
                                row.get(h_index_col, None),
                                None,  # total_docs
                                None,  # total_cites
                                None,  # cites_per_doc
                                None   # ref_per_doc
                            ))
                
                # Batch insert journals
                if journals_data:
                    journal_insert_query = """
                        INSERT INTO journals (source_id, title, issn, e_issn, publisher, categories, 
                                            areas, type, country, region)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            issn = EXCLUDED.issn,
                            e_issn = EXCLUDED.e_issn,
                            publisher = EXCLUDED.publisher,
                            categories = EXCLUDED.categories,
                            areas = EXCLUDED.areas,
                            type = EXCLUDED.type,
                            country = EXCLUDED.country,
                            region = EXCLUDED.region;
                    """
                    execute_batch(cursor, journal_insert_query, journals_data, page_size=100)
                
                # Batch insert metrics
                if metrics_data:
                    # First, get journal IDs
                    metrics_with_ids = []
                    for metric in metrics_data:
                        cursor.execute("SELECT id FROM journals WHERE source_id = %s", (metric[0],))
                        result = cursor.fetchone()
                        if result:
                            journal_id = result[0]
                            metrics_with_ids.append((journal_id,) + metric[1:])
                    
                    if metrics_with_ids:
                        metrics_insert_query = """
                            INSERT INTO journal_metrics (journal_id, year, sjr, rank, rank_percentile, 
                                                        h_index, total_docs, total_cites, cites_per_doc, ref_per_doc)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (journal_id, year) DO UPDATE SET
                                sjr = EXCLUDED.sjr,
                                rank = EXCLUDED.rank,
                                h_index = EXCLUDED.h_index;
                        """
                        execute_batch(cursor, metrics_insert_query, metrics_with_ids, page_size=100)
                
                journal_count += len(journals_data)
                self.conn.commit()
                logger.info(f"Processed {journal_count} journals...")
            
            self.data_stats['journals'] = journal_count
            logger.info(f"✅ Imported {journal_count} journals")
            return True
            
        except Exception as e:
            logger.error(f"❌ Scimago journal import failed: {e}")
            self.conn.rollback()
            self.data_stats['errors'].append(f"Scimago import: {e}")
            return False
    
    def verify_import(self) -> Dict[str, Any]:
        """Verify the data import was successful"""
        try:
            cursor = self.conn.cursor()
            
            verification = {}
            
            # Count records in each table
            tables = ['universities', 'professors', 'publications', 'professor_publications', 'journals', 'journal_metrics']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                verification[table] = count
            
            # Sample data checks
            cursor.execute("SELECT name FROM universities LIMIT 5")
            verification['sample_universities'] = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT name FROM professors LIMIT 5")
            verification['sample_professors'] = [row[0] for row in cursor.fetchall()]
            
            return verification
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return {'error': str(e)}
    
    def run_full_migration(self, data_directory: str) -> bool:
        """Run the complete data migration process"""
        try:
            logger.info("🚀 Starting FacultyFinder data migration...")
            
            if not self.connect_database():
                return False
            
            # Create database schema
            if not self.create_database_schema():
                return False
            
            # Import universities
            university_file = os.path.join(data_directory, 'university_codes.csv')
            if os.path.exists(university_file):
                self.import_universities(university_file)
            
            # Import professors summary
            professors_file = os.path.join(data_directory, 'mcmaster_experts_summary.csv')
            if os.path.exists(professors_file):
                self.import_professors_summary(professors_file)
            
            # Import detailed faculty data
            detailed_file = os.path.join(data_directory, 'mcmaster_experts_detailed.json')
            if os.path.exists(detailed_file):
                self.import_detailed_faculty_data(detailed_file)
            
            # Import Scimago journals (optional, large file)
            scimago_file = os.path.join(data_directory, 'scimago_journals_comprehensive.csv')
            if os.path.exists(scimago_file):
                logger.info("📊 Scimago file found. This is a large file and may take several minutes...")
                self.import_scimago_journals(scimago_file)
            
            # Verify import
            verification = self.verify_import()
            
            logger.info("🎉 Data migration completed!")
            logger.info(f"📊 Migration Statistics:")
            for key, value in self.data_stats.items():
                if key != 'errors':
                    logger.info(f"   {key}: {value}")
            
            if self.data_stats['errors']:
                logger.warning(f"⚠️  Errors encountered: {len(self.data_stats['errors'])}")
                for error in self.data_stats['errors']:
                    logger.warning(f"   - {error}")
            
            logger.info("📋 Database verification:")
            for table, count in verification.items():
                if table not in ['sample_universities', 'sample_professors', 'error']:
                    logger.info(f"   {table}: {count} records")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            self.close_database()


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='FacultyFinder Data Migration System')
    parser.add_argument('--data-dir', '-d', default='/tmp/facultyfinder_data',
                        help='Directory containing data files')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--user', default='ff_user', help='Database user')
    parser.add_argument('--password', default='Choxos10203040', help='Database password')
    parser.add_argument('--database', default='ff_production', help='Database name')
    
    args = parser.parse_args()
    
    # Database configuration
    db_config = {
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password,
        'database': args.database
    }
    
    # Run migration
    migrator = FacultyFinderDataMigrator(db_config)
    success = migrator.run_full_migration(args.data_dir)
    
    if success:
        print("✅ Data migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Data migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 