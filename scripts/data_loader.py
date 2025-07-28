#!/usr/bin/env python3
"""
Data Loader for FacultyFinder
Loads university codes and faculty data into the database
"""

import sqlite3
import pandas as pd
import json
import os
import sys
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'database/facultyfinder_dev.db'
SCHEMA_PATH = 'database/schema.sql'

class DataLoader:
    """Handles loading data into FacultyFinder database"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def initialize_database(self):
        """Initialize database with schema"""
        if not self.conn:
            self.connect()
        
        try:
            with open(SCHEMA_PATH, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema (split by semicolons to handle multiple statements)
            statements = schema_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    self.conn.execute(statement)
            
            self.conn.commit()
            logger.info("Database schema initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            return False
    
    def load_universities(self, csv_path='data/university_codes.csv'):
        """Load university data from CSV"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loading {len(df)} universities from {csv_path}")
            
            for _, row in df.iterrows():
                self.conn.execute("""
                    INSERT OR REPLACE INTO universities 
                    (university_code, name, country, province_state, city)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row['university_code'],
                    row['university_name'],
                    row['country'],
                    row['province_state'],
                    row['city']
                ))
            
            self.conn.commit()
            logger.info(f"Successfully loaded {len(df)} universities")
            return True
        except Exception as e:
            logger.error(f"Failed to load universities: {e}")
            return False
    
    def load_faculty(self, csv_path='data/mcmaster_hei_faculty.csv'):
        """Load faculty data from CSV"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loading {len(df)} faculty members from {csv_path}")
            
            for _, row in df.iterrows():
                # Get university ID from university_code
                university_id = self.get_university_id(row.get('university_code'))
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO professors 
                    (name, first_name, last_name, middle_names, other_name, degrees, 
                     all_degrees_and_inst, all_degrees_only, research_areas, university_id, 
                     faculty, department, other_departments, primary_affiliation, memberships, 
                     canada_research_chair, director, position, full_time, adjunct, 
                     uni_email, other_email, uni_page, website, misc, twitter, linkedin, 
                     phone, fax, google_scholar, scopus, web_of_science, orcid, 
                     researchgate, academicedu)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('name'),
                    row.get('first_name'),
                    row.get('last_name'),
                    row.get('middle_names'),
                    row.get('other_name'),
                    row.get('degree'),
                    row.get('all_degrees_and_inst'),
                    row.get('all_degrees_only'),
                    row.get('research_areas'),
                    university_id,
                    row.get('faculty'),
                    row.get('department'),
                    row.get('other_depts'),
                    row.get('primary_aff'),
                    row.get('membership'),
                    row.get('canada_research_chair'),
                    row.get('director'),
                    row.get('position'),
                    bool(row.get('full_time', False)),
                    bool(row.get('adjunct', False)),
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
            
            self.conn.commit()
            logger.info(f"Successfully loaded {len(df)} faculty members")
            return True
        except Exception as e:
            logger.error(f"Failed to load faculty: {e}")
            return False
    
    def get_university_id(self, university_code):
        """Get university ID from university code"""
        if not university_code:
            return None
        
        cursor = self.conn.execute(
            "SELECT id FROM universities WHERE university_code = ?",
            (university_code,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    
    def load_scimago_journals(self, csv_path='data/scimago_journals_comprehensive.csv', sample_size=1000):
        """Load journal data from Scimago CSV (with sampling for development)"""
        try:
            # Read in chunks to handle large file
            logger.info(f"Loading Scimago journal data from {csv_path}")
            
            chunk_size = 10000
            processed_count = 0
            
            for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size):
                # Take sample for development
                if sample_size and processed_count >= sample_size:
                    break
                
                for _, row in chunk_df.iterrows():
                    if sample_size and processed_count >= sample_size:
                        break
                    
                    # Insert journal
                    cursor = self.conn.execute("""
                        INSERT OR IGNORE INTO journals 
                        (source_id, title, type, issn, publisher, categories, areas, country, region, coverage)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('source_id'),
                        row.get('title'),
                        row.get('type'),
                        row.get('issn'),
                        row.get('publisher'),
                        row.get('categories'),
                        row.get('areas'),
                        row.get('country'),
                        row.get('region'),
                        row.get('coverage')
                    ))
                    
                    journal_id = cursor.lastrowid
                    
                    # Insert rankings for different years
                    for year in range(1999, 2025):
                        rank_col = f'rank_{year}'
                        sjr_col = f'sjr_{year}'
                        quartile_col = f'sjr_best_quartile_{year}'
                        h_index_col = f'h_index_{year}'
                        docs_col = f'total_docs_{year}'
                        citations_col = f'total_citations_{year}'
                        
                        if rank_col in row and pd.notna(row.get(rank_col)):
                            self.conn.execute("""
                                INSERT OR IGNORE INTO journal_rankings 
                                (journal_id, year, rank, sjr, sjr_best_quartile, h_index, total_docs, total_citations)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                journal_id,
                                year,
                                row.get(rank_col) if pd.notna(row.get(rank_col)) else None,
                                row.get(sjr_col) if pd.notna(row.get(sjr_col)) else None,
                                row.get(quartile_col) if pd.notna(row.get(quartile_col)) else None,
                                row.get(h_index_col) if pd.notna(row.get(h_index_col)) else None,
                                row.get(docs_col) if pd.notna(row.get(docs_col)) else None,
                                row.get(citations_col) if pd.notna(row.get(citations_col)) else None
                            ))
                    
                    processed_count += 1
                
                # Commit every chunk
                self.conn.commit()
                logger.info(f"Processed {processed_count} journals...")
            
            logger.info(f"Successfully loaded {processed_count} journals")
            return True
        except Exception as e:
            logger.error(f"Failed to load Scimago data: {e}")
            return False
    
    def extract_research_areas(self):
        """Extract and normalize research areas from faculty data"""
        try:
            cursor = self.conn.execute("SELECT DISTINCT research_areas FROM professors WHERE research_areas IS NOT NULL")
            research_areas_data = cursor.fetchall()
            
            research_areas_set = set()
            
            for row in research_areas_data:
                if row[0]:
                    # Split by semicolon and clean up
                    areas = [area.strip() for area in row[0].split(';') if area.strip()]
                    research_areas_set.update(areas)
            
            # Insert unique research areas
            for area in research_areas_set:
                self.conn.execute("""
                    INSERT OR IGNORE INTO research_areas (name) VALUES (?)
                """, (area,))
            
            self.conn.commit()
            logger.info(f"Extracted {len(research_areas_set)} unique research areas")
            return True
        except Exception as e:
            logger.error(f"Failed to extract research areas: {e}")
            return False
    
    def get_database_stats(self):
        """Get database statistics"""
        stats = {}
        
        # University count
        cursor = self.conn.execute("SELECT COUNT(*) FROM universities")
        stats['universities'] = cursor.fetchone()[0]
        
        # Professor count
        cursor = self.conn.execute("SELECT COUNT(*) FROM professors")
        stats['professors'] = cursor.fetchone()[0]
        
        # Journal count
        cursor = self.conn.execute("SELECT COUNT(*) FROM journals")
        stats['journals'] = cursor.fetchone()[0]
        
        # Research areas count
        cursor = self.conn.execute("SELECT COUNT(*) FROM research_areas")
        stats['research_areas'] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main data loading function"""
    loader = DataLoader()
    
    # Initialize database
    if not loader.initialize_database():
        logger.error("Failed to initialize database")
        return False
    
    # Load universities
    if not loader.load_universities():
        logger.error("Failed to load universities")
        return False
    
    # Load faculty
    if not loader.load_faculty():
        logger.error("Failed to load faculty")
        return False
    
    # Extract research areas
    if not loader.extract_research_areas():
        logger.error("Failed to extract research areas")
        return False
    
    # Load sample of Scimago data (for development)
    if os.path.exists('data/scimago_journals_comprehensive.csv'):
        if not loader.load_scimago_journals(sample_size=1000):
            logger.warning("Failed to load Scimago data, continuing without it")
    
    # Print statistics
    stats = loader.get_database_stats()
    logger.info("Database loading completed!")
    logger.info(f"Statistics: {stats}")
    
    loader.close()
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 