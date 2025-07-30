#!/usr/bin/env python3
"""
Import PubMed Data to VPS PostgreSQL Database
Imports the JSON/CSV data exported from local machine
"""

import os
import json
import csv
import sys
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PubMedDataImporter:
    """Import PubMed data into PostgreSQL database"""
    
    def __init__(self):
        self.conn = None
        self.connect_to_database()
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'ff_production'),
                user=os.getenv('DB_USER', 'ff_user'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            sys.exit(1)
    
    def get_or_create_professor_id(self, faculty_name):
        """Get professor ID by name or create if doesn't exist"""
        
        cur = self.conn.cursor()
        
        try:
            # Try to find existing professor
            cur.execute(
                "SELECT id FROM professors WHERE name ILIKE %s LIMIT 1",
                (faculty_name,)
            )
            
            result = cur.fetchone()
            if result:
                professor_id = result[0]
                print(f"   Found existing professor: {faculty_name} (ID: {professor_id})")
                return professor_id
            
            # Create new professor record
            cur.execute("""
                INSERT INTO professors (name, created_at) 
                VALUES (%s, %s) 
                RETURNING id
            """, (faculty_name, datetime.now()))
            
            professor_id = cur.fetchone()[0]
            self.conn.commit()
            
            print(f"   Created new professor: {faculty_name} (ID: {professor_id})")
            return professor_id
            
        except Exception as e:
            print(f"   ❌ Error with professor {faculty_name}: {str(e)}")
            self.conn.rollback()
            return None
        finally:
            cur.close()
    
    def import_publication(self, publication_data, professor_id):
        """Import a single publication"""
        
        cur = self.conn.cursor()
        
        try:
            # Check if publication already exists
            pmid = publication_data.get('pmid')
            if pmid:
                cur.execute("SELECT id FROM publications WHERE pmid = %s", (pmid,))
                existing = cur.fetchone()
                
                if existing:
                    publication_id = existing[0]
                    print(f"      Publication {pmid} already exists")
                else:
                    # Insert new publication
                    insert_query = """
                    INSERT INTO publications (
                        pmid, doi, title, abstract, authors, journal_name,
                        publication_date, publication_year, volume, issue, pages,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                    """
                    
                    cur.execute(insert_query, (
                        publication_data.get('pmid'),
                        publication_data.get('doi'),
                        publication_data.get('title'),
                        publication_data.get('abstract'),
                        publication_data.get('authors'),
                        publication_data.get('journal_name'),
                        publication_data.get('publication_date'),
                        publication_data.get('publication_year'),
                        publication_data.get('volume'),
                        publication_data.get('issue'),
                        publication_data.get('pages'),
                        datetime.now()
                    ))
                    
                    publication_id = cur.fetchone()[0]
                    print(f"      Imported publication {pmid}")
            else:
                # No PMID - create publication anyway
                insert_query = """
                INSERT INTO publications (
                    title, abstract, authors, journal_name,
                    publication_date, publication_year, volume, issue, pages,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """
                
                cur.execute(insert_query, (
                    publication_data.get('title'),
                    publication_data.get('abstract'),
                    publication_data.get('authors'),
                    publication_data.get('journal_name'),
                    publication_data.get('publication_date'),
                    publication_data.get('publication_year'),
                    publication_data.get('volume'),
                    publication_data.get('issue'),
                    publication_data.get('pages'),
                    datetime.now()
                ))
                
                publication_id = cur.fetchone()[0]
                print(f"      Imported publication without PMID")
            
            # Link to professor (check if relationship already exists)
            cur.execute(
                "SELECT id FROM author_publications WHERE professor_id = %s AND publication_id = %s",
                (professor_id, publication_id)
            )
            
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO author_publications (professor_id, publication_id, author_order)
                    VALUES (%s, %s, %s)
                """, (professor_id, publication_id, 1))
                
                print(f"      Linked to professor")
            
            self.conn.commit()
            return publication_id
            
        except Exception as e:
            print(f"      ❌ Error importing publication: {str(e)}")
            self.conn.rollback()
            return None
        finally:
            cur.close()
    
    def import_from_json(self, json_file):
        """Import publications from JSON file"""
        
        print(f"📄 Importing from {json_file}...")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # Combined file with all publications
                publications = data
                faculty_groups = {}
                
                # Group by faculty
                for pub in publications:
                    faculty_name = pub.get('faculty_name', 'Unknown')
                    if faculty_name not in faculty_groups:
                        faculty_groups[faculty_name] = []
                    faculty_groups[faculty_name].append(pub)
                
                total_imported = 0
                
                for faculty_name, faculty_pubs in faculty_groups.items():
                    print(f"\n👨‍🔬 Processing {faculty_name} ({len(faculty_pubs)} publications)")
                    
                    professor_id = self.get_or_create_professor_id(faculty_name)
                    if not professor_id:
                        continue
                    
                    for pub in faculty_pubs:
                        if self.import_publication(pub, professor_id):
                            total_imported += 1
                
            elif isinstance(data, dict) and 'publications' in data:
                # Individual faculty file
                faculty_name = data.get('faculty_name', 'Unknown')
                publications = data.get('publications', [])
                
                print(f"\n👨‍🔬 Processing {faculty_name} ({len(publications)} publications)")
                
                professor_id = self.get_or_create_professor_id(faculty_name)
                if not professor_id:
                    return 0
                
                total_imported = 0
                for pub in publications:
                    if self.import_publication(pub, professor_id):
                        total_imported += 1
            
            else:
                print("❌ Unrecognized JSON format")
                return 0
            
            print(f"\n✅ Imported {total_imported} publications from {json_file}")
            return total_imported
            
        except Exception as e:
            print(f"❌ Error importing from {json_file}: {str(e)}")
            return 0
    
    def import_from_csv(self, csv_file):
        """Import publications from CSV file"""
        
        print(f"📄 Importing from {csv_file}...")
        
        try:
            total_imported = 0
            current_faculty = None
            professor_id = None
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    faculty_name = row.get('faculty_name', 'Unknown')
                    
                    # Get professor ID if faculty changed
                    if faculty_name != current_faculty:
                        current_faculty = faculty_name
                        professor_id = self.get_or_create_professor_id(faculty_name)
                        
                        if not professor_id:
                            continue
                    
                    # Import publication
                    if self.import_publication(row, professor_id):
                        total_imported += 1
            
            print(f"\n✅ Imported {total_imported} publications from {csv_file}")
            return total_imported
            
        except Exception as e:
            print(f"❌ Error importing from {csv_file}: {str(e)}")
            return 0
    
    def import_directory(self, directory_path):
        """Import all files from a directory"""
        
        print(f"📁 Importing from directory: {directory_path}")
        
        if not os.path.exists(directory_path):
            print(f"❌ Directory not found: {directory_path}")
            return
        
        total_imported = 0
        
        # Look for files
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            if filename.endswith('.json'):
                imported = self.import_from_json(file_path)
                total_imported += imported
            elif filename.endswith('.csv'):
                imported = self.import_from_csv(file_path)
                total_imported += imported
        
        print(f"\n🎉 Total imported from directory: {total_imported} publications")
        
        # Show final statistics
        self.show_statistics()
    
    def show_statistics(self):
        """Show database statistics after import"""
        
        cur = self.conn.cursor()
        
        try:
            # Total publications
            cur.execute("SELECT COUNT(*) FROM publications")
            total_pubs = cur.fetchone()[0]
            
            # Publications with PMIDs
            cur.execute("SELECT COUNT(*) FROM publications WHERE pmid IS NOT NULL")
            with_pmids = cur.fetchone()[0]
            
            # Faculty with publications
            cur.execute("SELECT COUNT(DISTINCT professor_id) FROM author_publications")
            faculty_with_pubs = cur.fetchone()[0]
            
            # Recent publications (last hour)
            cur.execute("""
                SELECT COUNT(*) FROM publications 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """)
            recent_pubs = cur.fetchone()[0]
            
            print(f"\n📊 Database Statistics:")
            print(f"   Total Publications: {total_pubs}")
            print(f"   With PMIDs: {with_pmids}")
            print(f"   Faculty with Publications: {faculty_with_pubs}")
            print(f"   Imported in last hour: {recent_pubs}")
            
        except Exception as e:
            print(f"❌ Error getting statistics: {str(e)}")
        finally:
            cur.close()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main function for data import"""
    
    print("📥 PubMed Data Importer for VPS")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage: python3 import_pubmed_data.py <file_or_directory>")
        print("\nExamples:")
        print("  python3 import_pubmed_data.py pubmed_exports/")
        print("  python3 import_pubmed_data.py all_publications.json")
        print("  python3 import_pubmed_data.py all_publications.csv")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    # Initialize importer
    importer = PubMedDataImporter()
    
    try:
        if os.path.isdir(target_path):
            # Import entire directory
            importer.import_directory(target_path)
        elif target_path.endswith('.json'):
            # Import JSON file
            importer.import_from_json(target_path)
        elif target_path.endswith('.csv'):
            # Import CSV file
            importer.import_from_csv(target_path)
        else:
            print(f"❌ Unsupported file type: {target_path}")
    
    finally:
        importer.close()
    
    print("\n🎉 Import completed!")
    print("✅ Your VPS database now contains PubMed publication data")

if __name__ == "__main__":
    main() 