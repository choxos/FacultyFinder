#!/usr/bin/env python3
"""
Publications Data Importer

Imports JSON publication files and CSV tracking files into PostgreSQL database.
Handles OpenAlex, PubMed, and other publication sources.

Usage:
    python3 publications_importer.py [options]

Example:
    python3 publications_importer.py --data-dir data --dry-run
    python3 publications_importer.py --faculty-only  # Only import author profiles
"""

import os
import sys
import json
import csv
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
from dotenv import load_dotenv


class PublicationsImporter:
    def __init__(self, db_config: Dict[str, str], dry_run: bool = False):
        """Initialize database connection"""
        self.db_config = db_config
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'publications_imported': 0,
            'publications_updated': 0,
            'faculty_publications_imported': 0,
            'author_profiles_imported': 0,
            'author_profiles_updated': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            print("✅ Connected to PostgreSQL database")
            
            if self.dry_run:
                print("🧪 DRY RUN MODE - No data will be modified")
            
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            raise

    def import_publication_json(self, json_file: Path, source_system: str) -> bool:
        """Import a single publication JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract publication ID based on source system
            if source_system == 'openalex':
                pub_id = data.get('id', '').replace('https://openalex.org/', '')
                title = data.get('display_name', '')
                abstract = self._reconstruct_abstract(data.get('abstract_inverted_index', {}))
                doi = data.get('doi', '').replace('https://doi.org/', '') if data.get('doi') else ''
                citation_count = data.get('cited_by_count', 0)
                pub_year = data.get('publication_year')
                pub_date = data.get('publication_date')
                journal_name = ''
                if data.get('primary_location', {}).get('source'):
                    journal_name = data['primary_location']['source'].get('display_name', '')
                
            elif source_system == 'pubmed':
                pub_id = data.get('pmid', '')
                title = data.get('title', '')
                abstract = data.get('abstract', '')
                doi = data.get('doi', '')
                citation_count = 0  # PubMed doesn't provide citation counts
                pub_year = data.get('year')
                pub_date = data.get('date')
                journal_name = data.get('journal', '')
                
            else:
                print(f"⚠️  Unknown source system: {source_system}")
                return False

            if not pub_id:
                print(f"⚠️  No publication ID found in {json_file}")
                return False

            if self.dry_run:
                print(f"🧪 [DRY RUN] Would import: {title[:50]}... ({source_system}:{pub_id})")
                self.stats['publications_imported'] += 1
                return True

            # Check if publication already exists
            check_query = """
                SELECT id FROM publications 
                WHERE publication_id = %s AND source_system = %s
            """
            self.cursor.execute(check_query, (pub_id, source_system))
            existing = self.cursor.fetchone()

            # Insert or update publication
            if existing:
                update_query = """
                    UPDATE publications SET
                        title = %s,
                        abstract = %s,
                        citation_count = %s,
                        authors = %s,
                        affiliations = %s,
                        topics = %s,
                        keywords = %s,
                        raw_data = %s,
                        updated_at = %s
                    WHERE publication_id = %s AND source_system = %s
                """
                
                # Prepare data for update
                authors_json = json.dumps(self._extract_authors(data, source_system))
                affiliations_json = json.dumps(self._extract_affiliations(data, source_system))
                topics_json = json.dumps(self._extract_topics(data, source_system))
                keywords_json = json.dumps(self._extract_keywords(data, source_system))
                
                self.cursor.execute(update_query, (
                    title, abstract, citation_count, authors_json, affiliations_json,
                    topics_json, keywords_json, json.dumps(data), datetime.now(),
                    pub_id, source_system
                ))
                
                self.stats['publications_updated'] += 1
                
            else:
                insert_query = """
                    INSERT INTO publications (
                        publication_id, source_system, title, abstract, publication_year,
                        publication_date, doi, journal_name, citation_count, authors, 
                        affiliations, topics, keywords, raw_data, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                # Prepare data for insertion
                authors_json = json.dumps(self._extract_authors(data, source_system))
                affiliations_json = json.dumps(self._extract_affiliations(data, source_system))
                topics_json = json.dumps(self._extract_topics(data, source_system))
                keywords_json = json.dumps(self._extract_keywords(data, source_system))
                
                self.cursor.execute(insert_query, (
                    pub_id, source_system, title, abstract, pub_year,
                    pub_date, doi, journal_name, citation_count, authors_json, 
                    affiliations_json, topics_json, keywords_json, json.dumps(data), 
                    datetime.now()
                ))
                
                self.stats['publications_imported'] += 1
            
            return True
                
        except Exception as e:
            print(f"⚠️  Error importing {json_file}: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_faculty_publications_csv(self, csv_file: Path, source_system: str) -> bool:
        """Import faculty-publication tracking CSV"""
        try:
            faculty_id = csv_file.stem.replace(f'_{source_system}', '')
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Get publication ID based on source system
                    if source_system.lower() == 'openalex':
                        pub_id = row.get('openalex_id', '').replace('https://openalex.org/', '')
                    elif source_system.lower() == 'pubmed':
                        pub_id = row.get('pmid', '')
                    else:
                        continue
                    
                    if not pub_id:
                        continue
                    
                    current_affiliation = row.get('current_affiliation', 'FALSE').upper() == 'TRUE'
                    
                    if self.dry_run:
                        print(f"🧪 [DRY RUN] Would link: {faculty_id} -> {pub_id} ({source_system})")
                        self.stats['faculty_publications_imported'] += 1
                        continue
                    
                    # Insert faculty-publication relationship
                    insert_query = """
                        INSERT INTO faculty_publications (
                            faculty_id, publication_id, source_system, current_affiliation
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (faculty_id, publication_id, source_system) DO UPDATE SET
                            current_affiliation = EXCLUDED.current_affiliation
                    """
                    
                    self.cursor.execute(insert_query, (faculty_id, pub_id, source_system, current_affiliation))
                    self.stats['faculty_publications_imported'] += 1
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error importing faculty CSV {csv_file}: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_author_profiles_csv(self, csv_file: Path) -> bool:
        """Import OpenAlex author profiles CSV"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    faculty_id = row.get('faculty_id', '')
                    openalex_id = row.get('openalex_id', '').replace('https://openalex.org/', '') if row.get('openalex_id') else ''
                    
                    if not faculty_id:
                        continue
                    
                    if self.dry_run:
                        print(f"🧪 [DRY RUN] Would import profile: {faculty_id} ({row.get('display_name', 'Unknown')})")
                        self.stats['author_profiles_imported'] += 1
                        continue
                    
                    # Check if profile already exists
                    check_query = "SELECT id FROM author_profiles WHERE faculty_id = %s"
                    self.cursor.execute(check_query, (faculty_id,))
                    existing = self.cursor.fetchone()
                    
                    # Prepare structured data
                    affiliations = self._parse_pipe_separated_affiliations(row)
                    research_topics = self._parse_pipe_separated_topics(row)
                    topic_distribution = self._parse_topic_shares(row)
                    external_ids = self._parse_external_ids(row)
                    publication_trends = self._parse_publication_trends(row)
                    
                    if existing:
                        update_query = """
                            UPDATE author_profiles SET
                                openalex_id = %s,
                                orcid = %s,
                                display_name = %s,
                                first_name = %s,
                                last_name = %s,
                                works_count = %s,
                                cited_by_count = %s,
                                h_index = %s,
                                i10_index = %s,
                                mean_citedness = %s,
                                affiliations = %s,
                                research_topics = %s,
                                topic_distribution = %s,
                                external_ids = %s,
                                publication_trends = %s,
                                raw_profile = %s,
                                last_updated = %s
                            WHERE faculty_id = %s
                        """
                        
                        self.cursor.execute(update_query, (
                            openalex_id, row.get('orcid', ''),
                            row.get('display_name', ''), row.get('faculty_first_name', ''),
                            row.get('faculty_last_name', ''), 
                            int(row.get('works_count', 0) or 0),
                            int(row.get('cited_by_count', 0) or 0),
                            int(row.get('h_index', 0) or 0),
                            int(row.get('i10_index', 0) or 0),
                            float(row.get('2yr_mean_citedness', 0) or 0),
                            json.dumps(affiliations), json.dumps(research_topics),
                            json.dumps(topic_distribution), json.dumps(external_ids),
                            json.dumps(publication_trends), json.dumps(dict(row)),
                            datetime.now(), faculty_id
                        ))
                        
                        self.stats['author_profiles_updated'] += 1
                        
                    else:
                        insert_query = """
                            INSERT INTO author_profiles (
                                faculty_id, openalex_id, orcid, display_name, first_name, last_name,
                                works_count, cited_by_count, h_index, i10_index, mean_citedness,
                                affiliations, research_topics, topic_distribution, external_ids,
                                publication_trends, raw_profile, last_updated
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        
                        self.cursor.execute(insert_query, (
                            faculty_id, openalex_id, row.get('orcid', ''),
                            row.get('display_name', ''), row.get('faculty_first_name', ''),
                            row.get('faculty_last_name', ''), 
                            int(row.get('works_count', 0) or 0),
                            int(row.get('cited_by_count', 0) or 0),
                            int(row.get('h_index', 0) or 0),
                            int(row.get('i10_index', 0) or 0),
                            float(row.get('2yr_mean_citedness', 0) or 0),
                            json.dumps(affiliations), json.dumps(research_topics),
                            json.dumps(topic_distribution), json.dumps(external_ids),
                            json.dumps(publication_trends), json.dumps(dict(row)),
                            datetime.now()
                        ))
                        
                        self.stats['author_profiles_imported'] += 1
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error importing author profiles {csv_file}: {str(e)}")
            self.stats['errors'] += 1
            return False

    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """Reconstruct abstract from OpenAlex inverted index"""
        if not inverted_index:
            return ""
        
        try:
            # Create position-to-word mapping
            words = {}
            for word, positions in inverted_index.items():
                for pos in positions:
                    words[pos] = word
            
            # Reconstruct in order
            if not words:
                return ""
            
            max_pos = max(words.keys())
            result = []
            for i in range(max_pos + 1):
                result.append(words.get(i, ''))
            
            return ' '.join(result).strip()
        except Exception:
            return ""

    def _extract_authors(self, data: Dict, source_system: str) -> List[Dict]:
        """Extract author information based on source system"""
        try:
            if source_system == 'openalex':
                return data.get('authorships', [])
            elif source_system == 'pubmed':
                return data.get('authors', [])
            return []
        except Exception:
            return []

    def _extract_affiliations(self, data: Dict, source_system: str) -> List[Dict]:
        """Extract affiliation information"""
        try:
            if source_system == 'openalex':
                affiliations = []
                for authorship in data.get('authorships', []):
                    affiliations.extend(authorship.get('institutions', []))
                return affiliations
            elif source_system == 'pubmed':
                return data.get('affiliations', [])
            return []
        except Exception:
            return []

    def _extract_topics(self, data: Dict, source_system: str) -> List[Dict]:
        """Extract topic information"""
        try:
            if source_system == 'openalex':
                return data.get('topics', [])
            elif source_system == 'pubmed':
                return data.get('mesh_terms', [])
            return []
        except Exception:
            return []

    def _extract_keywords(self, data: Dict, source_system: str) -> List[str]:
        """Extract keywords"""
        try:
            if source_system == 'openalex':
                return [kw.get('display_name', '') for kw in data.get('keywords', [])]
            elif source_system == 'pubmed':
                return data.get('keywords', [])
            return []
        except Exception:
            return []

    def _parse_pipe_separated_affiliations(self, row: Dict) -> List[Dict]:
        """Parse pipe-separated affiliation data"""
        try:
            names = row.get('affiliations_names', '').split('|') if row.get('affiliations_names') else []
            years = row.get('affiliations_years', '').split('|') if row.get('affiliations_years') else []
            
            affiliations = []
            for i, name in enumerate(names):
                if name.strip():
                    affiliation = {'name': name.strip()}
                    if i < len(years) and years[i].strip():
                        affiliation['years'] = years[i].strip()
                    affiliations.append(affiliation)
            
            return affiliations
        except Exception:
            return []

    def _parse_pipe_separated_topics(self, row: Dict) -> List[Dict]:
        """Parse research topics from pipe-separated data"""
        try:
            names = row.get('top_topics_names', '').split('|') if row.get('top_topics_names') else []
            counts = row.get('top_topics_counts', '').split('|') if row.get('top_topics_counts') else []
            fields = row.get('top_topics_fields', '').split('|') if row.get('top_topics_fields') else []
            domains = row.get('top_topics_domains', '').split('|') if row.get('top_topics_domains') else []
            
            topics = []
            for i, name in enumerate(names):
                if name.strip():
                    topic = {'name': name.strip()}
                    if i < len(counts) and counts[i].strip():
                        topic['count'] = int(counts[i].strip() or 0)
                    if i < len(fields) and fields[i].strip():
                        topic['field'] = fields[i].strip()
                    if i < len(domains) and domains[i].strip():
                        topic['domain'] = domains[i].strip()
                    topics.append(topic)
            
            return topics
        except Exception:
            return []

    def _parse_topic_shares(self, row: Dict) -> List[Dict]:
        """Parse topic share distribution"""
        try:
            names = row.get('topic_share_names', '').split('|') if row.get('topic_share_names') else []
            values = row.get('topic_share_values', '').split('|') if row.get('topic_share_values') else []
            
            shares = []
            for i, name in enumerate(names):
                if name.strip():
                    share = {'topic': name.strip()}
                    if i < len(values) and values[i].strip():
                        try:
                            share['value'] = float(values[i].strip() or 0)
                        except ValueError:
                            share['value'] = 0
                    shares.append(share)
            
            return shares
        except Exception:
            return []

    def _parse_external_ids(self, row: Dict) -> Dict:
        """Parse external identifiers"""
        return {
            'scopus_id': row.get('scopus_id', ''),
            'mag_id': row.get('mag_id', ''),
            'twitter_id': row.get('twitter_id', ''),
            'wikipedia_id': row.get('wikipedia_id', '')
        }

    def _parse_publication_trends(self, row: Dict) -> List[Dict]:
        """Parse year-by-year publication trends"""
        try:
            years = row.get('recent_years', '').split('|') if row.get('recent_years') else []
            works = row.get('recent_works_counts', '').split('|') if row.get('recent_works_counts') else []
            citations = row.get('recent_citations_counts', '').split('|') if row.get('recent_citations_counts') else []
            
            trends = []
            for i, year in enumerate(years):
                if year.strip():
                    try:
                        trend = {'year': int(year.strip())}
                        if i < len(works) and works[i].strip():
                            trend['works_count'] = int(works[i].strip() or 0)
                        if i < len(citations) and citations[i].strip():
                            trend['cited_by_count'] = int(citations[i].strip() or 0)
                        trends.append(trend)
                    except ValueError:
                        continue
            
            return trends
        except Exception:
            return []

    def process_all_data(self, data_dir: str = "data", publications_only: bool = False, faculty_only: bool = False):
        """Process all publication data"""
        data_path = Path(data_dir)
        
        print("🔄 Starting comprehensive data import...")
        
        if not faculty_only:
            # 1. Import JSON publication files
            print("\n📚 Importing JSON publication files...")
            
            # OpenAlex publications
            openalex_dir = data_path / "publications" / "openalex"
            if openalex_dir.exists():
                json_files = list(openalex_dir.glob("*.json"))
                print(f"   Found {len(json_files)} OpenAlex JSON files")
                for i, json_file in enumerate(json_files, 1):
                    if i % 100 == 0:
                        print(f"   Processed {i}/{len(json_files)} OpenAlex files...")
                    self.import_publication_json(json_file, "openalex")
            
            # PubMed publications
            pubmed_dir = data_path / "publications" / "pubmed"
            if pubmed_dir.exists():
                json_files = list(pubmed_dir.glob("*.json"))
                print(f"   Found {len(json_files)} PubMed JSON files")
                for i, json_file in enumerate(json_files, 1):
                    if i % 100 == 0:
                        print(f"   Processed {i}/{len(json_files)} PubMed files...")
                    self.import_publication_json(json_file, "pubmed")
        
        if not publications_only:
            # 2. Import faculty-publication tracking CSVs
            print("\n👥 Importing faculty-publication relationships...")
            
            faculties_dir = data_path / "faculties"
            
            # OpenAlex tracking CSVs
            openalex_csvs = list(faculties_dir.rglob("*_OpenAlex.csv"))
            openalex_tracking_csvs = [csv for csv in openalex_csvs if "publications" in str(csv)]
            print(f"   Found {len(openalex_tracking_csvs)} OpenAlex tracking CSVs")
            
            for csv_file in openalex_tracking_csvs:
                self.import_faculty_publications_csv(csv_file, "openalex")
            
            # PubMed tracking CSVs
            pubmed_csvs = list(faculties_dir.rglob("*_PubMed.csv"))
            pubmed_tracking_csvs = [csv for csv in pubmed_csvs if "publications" in str(csv)]
            print(f"   Found {len(pubmed_tracking_csvs)} PubMed tracking CSVs")
            
            for csv_file in pubmed_tracking_csvs:
                self.import_faculty_publications_csv(csv_file, "pubmed")
            
            # 3. Import author profiles
            print("\n👨‍🎓 Importing author profiles...")
            
            author_csvs = list(faculties_dir.rglob("*_faculty_info_OpenAlex.csv"))
            print(f"   Found {len(author_csvs)} author profile CSVs")
            
            for csv_file in author_csvs:
                self.import_author_profiles_csv(csv_file)
        
        # Commit all changes
        if not self.dry_run:
            self.conn.commit()
            print("\n✅ All data imported and committed to database!")
        else:
            print("\n🧪 DRY RUN completed - no data was modified")

    def refresh_metrics_cache(self):
        """Refresh metrics cache for all faculty"""
        if self.dry_run:
            print("🧪 [DRY RUN] Would refresh metrics cache")
            return
        
        print("\n📊 Refreshing faculty metrics cache...")
        
        # Get all faculty IDs from author profiles
        self.cursor.execute("SELECT faculty_id FROM author_profiles")
        faculty_ids = [row['faculty_id'] for row in self.cursor.fetchall()]
        
        print(f"   Calculating metrics for {len(faculty_ids)} faculty members...")
        
        for i, faculty_id in enumerate(faculty_ids, 1):
            if i % 50 == 0:
                print(f"   Processed {i}/{len(faculty_ids)} faculty metrics...")
            
            try:
                self.cursor.execute("SELECT refresh_faculty_metrics(%s)", (faculty_id,))
            except Exception as e:
                print(f"   ⚠️  Error calculating metrics for {faculty_id}: {str(e)}")
        
        self.conn.commit()
        print("✅ Metrics cache refreshed!")

    def print_stats(self):
        """Print import statistics"""
        print(f"\n📊 Import Statistics:")
        print(f"{'='*50}")
        print(f"Publications imported: {self.stats['publications_imported']}")
        print(f"Publications updated: {self.stats['publications_updated']}")
        print(f"Faculty-publication links: {self.stats['faculty_publications_imported']}")
        print(f"Author profiles imported: {self.stats['author_profiles_imported']}")
        print(f"Author profiles updated: {self.stats['author_profiles_updated']}")
        print(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"{'='*50}")

    def verify_import(self):
        """Verify the imported data"""
        if self.dry_run:
            return
        
        print("\n🔍 Verifying imported data...")
        
        # Publications by source
        self.cursor.execute("""
            SELECT source_system, COUNT(*) as count
            FROM publications
            GROUP BY source_system
            ORDER BY source_system
        """)
        pub_stats = self.cursor.fetchall()
        
        print("📚 Publications by source:")
        for stat in pub_stats:
            print(f"   {stat['source_system']}: {stat['count']} publications")
        
        # Faculty with publications
        self.cursor.execute("""
            SELECT COUNT(DISTINCT faculty_id) as faculty_count
            FROM faculty_publications
        """)
        faculty_count = self.cursor.fetchone()['faculty_count']
        print(f"\n👥 Faculty with publications: {faculty_count}")
        
        # Author profiles
        self.cursor.execute("SELECT COUNT(*) as count FROM author_profiles")
        profile_count = self.cursor.fetchone()['count']
        print(f"👨‍🎓 Author profiles: {profile_count}")
        
        # Top cited publications
        self.cursor.execute("""
            SELECT title, citation_count, source_system
            FROM publications
            WHERE citation_count > 0
            ORDER BY citation_count DESC
            LIMIT 5
        """)
        top_cited = self.cursor.fetchall()
        
        if top_cited:
            print(f"\n🏆 Top cited publications:")
            for pub in top_cited:
                title = pub['title'][:60] + "..." if len(pub['title']) > 60 else pub['title']
                print(f"   {pub['citation_count']} citations: {title} ({pub['source_system']})")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Import publication data into PostgreSQL database')
    parser.add_argument('--data-dir', default='data', help='Data directory path (default: data)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without making changes')
    parser.add_argument('--publications-only', action='store_true', help='Import only publication JSON files')
    parser.add_argument('--faculty-only', action='store_true', help='Import only faculty profiles and relationships')
    parser.add_argument('--refresh-metrics', action='store_true', help='Refresh faculty metrics cache after import')
    parser.add_argument('--verify', action='store_true', help='Verify imported data')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'facultyfinder'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    # Verify database configuration
    if not all([db_config['user'], db_config['password']]):
        print("❌ Missing database credentials. Please check your .env file.")
        print("Required variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    # Check if data directory exists
    if not Path(args.data_dir).exists():
        print(f"❌ Data directory not found: {args.data_dir}")
        sys.exit(1)
    
    print(f"📥 Publications Data Importer")
    print(f"{'='*50}")
    print(f"Data directory: {args.data_dir}")
    print(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No data will be modified")
    
    # Initialize and run importer
    importer = PublicationsImporter(db_config, dry_run=args.dry_run)
    
    try:
        importer.connect()
        
        # Import data
        importer.process_all_data(
            data_dir=args.data_dir,
            publications_only=args.publications_only,
            faculty_only=args.faculty_only
        )
        
        # Refresh metrics if requested
        if args.refresh_metrics and not args.dry_run:
            importer.refresh_metrics_cache()
        
        # Print statistics
        importer.print_stats()
        
        # Verify data if requested
        if args.verify:
            importer.verify_import()
    
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        sys.exit(1)
    
    finally:
        importer.close()
    
    print(f"\n✅ Publications import completed successfully!")


if __name__ == "__main__":
    main() 