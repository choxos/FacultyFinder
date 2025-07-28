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
DB_PATH = '../database/facultyfinder_dev.db'
SCHEMA_PATH = '../database/schema.sql'

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

    def load_universities(self, csv_path='../data/university_codes.csv'):
        """Load university data from CSV"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loading {len(df)} universities from {csv_path}")

            for _, row in df.iterrows():
                # Parse year_established, handle non-numeric values
                year_established = None
                if pd.notna(row.get('established', '')):
                    try:
                        year_established = int(float(str(row.get('established', '')).strip()))
                    except (ValueError, TypeError):
                        year_established = None
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO universities
                    (university_code, name, country, province_state, city, address, university_type, languages, year_established)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['university_code'],
                    row['university_name'],
                    row['country'],
                    row['province_state'],
                    row['city'],
                    row.get('address', ''),
                    row.get('type', ''),
                    row.get('language', ''),
                    year_established
                ))

            self.conn.commit()
            logger.info(f"Successfully loaded {len(df)} universities")
            return True
        except Exception as e:
            logger.error(f"Failed to load universities: {e}")
            return False

    def load_faculty(self, csv_path='../data/mcmaster_hei_faculty.csv'):
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

    def load_scimago_journals(self, csv_path='../data/scimago_journals_comprehensive.csv', sample_size=1000):
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

    def extract_and_normalize_degrees(self):
        """Extract and normalize degrees from faculty data"""
        try:
            import re
            
            # Common degree patterns and their full names
            degree_mappings = {
                'PhD': 'Doctor of Philosophy',
                'Ph.D.': 'Doctor of Philosophy', 
                'DPhil': 'Doctor of Philosophy',
                'MD': 'Doctor of Medicine',
                'M.D.': 'Doctor of Medicine',
                'MSc': 'Master of Science',
                'M.Sc.': 'Master of Science',
                'MS': 'Master of Science',
                'MA': 'Master of Arts',
                'M.A.': 'Master of Arts',
                'MBA': 'Master of Business Administration',
                'MPH': 'Master of Public Health',
                'MPhil': 'Master of Philosophy',
                'BSc': 'Bachelor of Science',
                'B.Sc.': 'Bachelor of Science',
                'BS': 'Bachelor of Science',
                'BA': 'Bachelor of Arts',
                'B.A.': 'Bachelor of Arts',
                'BEng': 'Bachelor of Engineering',
                'BMed': 'Bachelor of Medicine',
                'MBBS': 'Bachelor of Medicine, Bachelor of Surgery',
                'MBChB': 'Bachelor of Medicine, Bachelor of Surgery',
                'JD': 'Juris Doctor',
                'LLB': 'Bachelor of Laws',
                'LLM': 'Master of Laws',
                'DMD': 'Doctor of Dental Medicine',
                'DDS': 'Doctor of Dental Surgery',
                'PharmD': 'Doctor of Pharmacy',
                'EdD': 'Doctor of Education',
                'DSc': 'Doctor of Science',
                'ScD': 'Doctor of Science'
            }

            # Get all degree data
            cursor = self.conn.execute("""
                SELECT id, degrees, all_degrees_and_inst, all_degrees_only 
                FROM professors 
                WHERE degrees IS NOT NULL OR all_degrees_and_inst IS NOT NULL
            """)
            faculty_data = cursor.fetchall()

            degrees_found = set()
            professor_degrees = []

            for row in faculty_data:
                professor_id, degrees, all_degrees_inst, all_degrees_only = row
                
                # Use the most detailed degree info available
                degree_text = all_degrees_only or all_degrees_inst or degrees
                
                if degree_text:
                    # Split by semicolon and process each degree
                    degree_parts = [d.strip() for d in degree_text.split(';') if d.strip()]
                    
                    for degree_part in degree_parts:
                        # Extract degree type and specialization
                        degree_type, specialization, institution = self._parse_degree(degree_part)
                        
                        if degree_type:
                            # Normalize degree type
                            normalized_type = degree_mappings.get(degree_type, degree_type)
                            degrees_found.add((degree_type, normalized_type))
                            
                            professor_degrees.append({
                                'professor_id': professor_id,
                                'degree_type': degree_type,
                                'specialization': specialization,
                                'institution': institution
                            })

            # Insert unique degrees
            for degree_type, full_name in degrees_found:
                category = self._categorize_degree(degree_type)
                self.conn.execute("""
                    INSERT OR IGNORE INTO degrees (degree_type, full_name, category) 
                    VALUES (?, ?, ?)
                """, (degree_type, full_name, category))

            # Insert professor-degree relationships
            for pd in professor_degrees:
                # Get degree_id
                cursor = self.conn.execute(
                    "SELECT id FROM degrees WHERE degree_type = ?", 
                    (pd['degree_type'],)
                )
                degree_result = cursor.fetchone()
                
                if degree_result:
                    degree_id = degree_result[0]
                    self.conn.execute("""
                        INSERT OR IGNORE INTO professor_degrees 
                        (professor_id, degree_id, specialization, institution)
                        VALUES (?, ?, ?, ?)
                    """, (pd['professor_id'], degree_id, pd['specialization'], pd['institution']))

            self.conn.commit()
            logger.info(f"Extracted {len(degrees_found)} unique degree types")
            logger.info(f"Created {len(professor_degrees)} professor-degree relationships")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract degrees: {e}")
            return False

    def _parse_degree(self, degree_text):
        """Parse a degree string to extract type, specialization, and institution"""
        import re
        
        degree_type = None
        specialization = None
        institution = None
        
        # Common degree patterns
        degree_patterns = [
            r'\b(PhD|Ph\.D\.?|DPhil)\b',
            r'\b(MD|M\.D\.?)\b',
            r'\b(MSc|M\.Sc\.?|MS)\b',
            r'\b(MA|M\.A\.?)\b',
            r'\b(MBA)\b',
            r'\b(MPH)\b',
            r'\b(MPhil)\b',
            r'\b(BSc|B\.Sc\.?|BS)\b',
            r'\b(BA|B\.A\.?)\b',
            r'\b(BEng)\b',
            r'\b(BMed)\b',
            r'\b(MBBS|MBChB)\b',
            r'\b(JD)\b',
            r'\b(LLB|LLM)\b',
            r'\b(DMD|DDS)\b',
            r'\b(PharmD)\b',
            r'\b(EdD)\b',
            r'\b(DSc|ScD)\b'
        ]
        
        # Find degree type
        for pattern in degree_patterns:
            match = re.search(pattern, degree_text, re.IGNORECASE)
            if match:
                degree_type = match.group(1).upper().replace('.', '')
                break
        
        # Extract specialization (text between degree and comma/institution)
        if degree_type:
            # Remove the degree type and look for specialization
            remaining_text = re.sub(rf'\b{re.escape(degree_type)}\b', '', degree_text, flags=re.IGNORECASE).strip()
            
            # Split by comma to separate specialization and institution
            parts = [p.strip() for p in remaining_text.split(',')]
            if parts and parts[0]:
                specialization = parts[0]
            
            # Institution is usually the last part or after specific keywords
            if len(parts) > 1:
                institution = parts[-1]
        
        return degree_type, specialization, institution

    def _categorize_degree(self, degree_type):
        """Categorize degree by level"""
        doctoral_degrees = ['PhD', 'Ph.D.', 'DPhil', 'MD', 'M.D.', 'JD', 'DMD', 'DDS', 'PharmD', 'EdD', 'DSc', 'ScD']
        masters_degrees = ['MSc', 'M.Sc.', 'MS', 'MA', 'M.A.', 'MBA', 'MPH', 'MPhil', 'LLM']
        bachelors_degrees = ['BSc', 'B.Sc.', 'BS', 'BA', 'B.A.', 'BEng', 'BMed', 'MBBS', 'MBChB', 'LLB']
        
        if degree_type in doctoral_degrees:
            return 'Doctoral'
        elif degree_type in masters_degrees:
            return "Master's"
        elif degree_type in bachelors_degrees:
            return "Bachelor's"
        else:
            return 'Other'

    def get_database_stats(self):
        """Get database statistics"""
        stats = {}
        cursor = self.conn.execute("SELECT COUNT(*) FROM universities")
        stats['universities'] = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(*) FROM professors")
        stats['professors'] = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(*) FROM journals")
        stats['journals'] = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(*) FROM research_areas")
        stats['research_areas'] = cursor.fetchone()[0]
        
        # Add degree stats if table exists
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM degrees")
            stats['degrees'] = cursor.fetchone()[0]
            cursor = self.conn.execute("SELECT COUNT(*) FROM professor_degrees")
            stats['professor_degrees'] = cursor.fetchone()[0]
        except:
            stats['degrees'] = 0
            stats['professor_degrees'] = 0
        
        return stats

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main data loading function"""
    loader = DataLoader()
    if not loader.initialize_database():
        logger.error("Failed to initialize database")
        return False
    if not loader.load_universities():
        logger.error("Failed to load universities")
        return False
    if not loader.load_faculty():
        logger.error("Failed to load faculty")
        return False
    if not loader.extract_research_areas():
        logger.error("Failed to extract research areas")
        return False
    if not loader.extract_and_normalize_degrees():
        logger.error("Failed to extract and normalize degrees")
        return False
    if os.path.exists('../data/scimago_journals_comprehensive.csv'):
        if not loader.load_scimago_journals(sample_size=1000):
            logger.warning("Failed to load Scimago data, continuing without it")
    stats = loader.get_database_stats()
    logger.info("Database loading completed!")
    logger.info(f"Statistics: {stats}")
    loader.close()
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 